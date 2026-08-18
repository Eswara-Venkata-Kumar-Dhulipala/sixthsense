# SPDX-License-Identifier: MPL-2.0

###############################################################################
#
# SixthSense
#
# Version : 3.0.0
#
# Module  : Multi-ToF Observation Engine
#
# Platform: Arduino UNO Q
#
# Features
#
#   • 6 x VL53L5CX through I2C mux
#   • 4x4 / 16 zones per sensor
#   • 96 raw zones total
#   • 30 Hz requested ranging frequency
#   • 400 kHz I2C
#   • 128-byte SparkFun transfer packet
#   • Immutable six-sensor ready/read/consume Bridge observation
#   • Per-zone confidence estimation
#   • Three sectors per ToF: S0 / S1 / S2
#   • Independent temporal history per sensor
#   • Velocity estimation and smoothing
#   • Motion classification
#   • Motion persistence
#   • Multi-sensor WebUI payload
#
###############################################################################

from dataclasses import dataclass
from collections import deque

import math
import time
import numpy as np

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI


###############################################################################
# Application Configuration
###############################################################################

APP_NAME = "SixthSense"
APP_VERSION = "3.0.0"


###############################################################################
# Fixed Six-ToF Configuration
###############################################################################

NUM_SENSORS = 6

SENSOR_CONFIGS = (
    {
        "sensor_index": 0,
        "sensor_id": "T1",
        "sensor_name": "Front-right",
        "position": "Front-right",
        "mux_channel": 0,
    },
    {
        "sensor_index": 1,
        "sensor_id": "T2",
        "sensor_name": "Front",
        "position": "Front",
        "mux_channel": 1,
    },
    {
        "sensor_index": 2,
        "sensor_id": "T3",
        "sensor_name": "Front-left",
        "position": "Front-left",
        "mux_channel": 2,
    },
    {
        "sensor_index": 3,
        "sensor_id": "T4",
        "sensor_name": "Rear-left",
        "position": "Rear-left",
        "mux_channel": 5,
    },
    {
        "sensor_index": 4,
        "sensor_id": "T5",
        "sensor_name": "Rear",
        "position": "Rear",
        "mux_channel": 6,
    },
    {
        "sensor_index": 5,
        "sensor_id": "T6",
        "sensor_name": "Rear-right",
        "position": "Rear-right",
        "mux_channel": 7,
    },
)

I2C_SPEED_HZ = 400_000
TOF_PACKET_SIZE = 128
REQUESTED_RANGING_FREQUENCY_HZ = 30
INTEGRATION_TIME_MS = 20

# This is a measured acquisition-side benchmark result, not a configured value.
MEASURED_RETRIEVED_RATE_HZ = 14.0


###############################################################################
# Sensor Image
###############################################################################

IMAGE_ROWS = 4
IMAGE_COLS = 4
NUM_ZONES = 16
TOTAL_ZONES = NUM_SENSORS * NUM_ZONES


###############################################################################
# Sector Configuration
###############################################################################

TOF_SECTOR_COUNT = 3

SECTOR_NAMES = (
    "S0",
    "S1",
    "S2",
)

# IMPORTANT:
#
# These ranges apply AFTER the existing left-right orientation correction
# (np.flip / np.fliplr equivalent).
#
# 4x4 oriented image:
#
#     column 0       columns 1-2       column 3
#        S0               S1              S2
#
# Therefore:
#   S0 = left-most column       = 4 zones
#   S1 = middle two columns     = 8 zones
#   S2 = right-most column      = 4 zones
#
SECTOR_RANGES = (
    (0, 1),
    (1, 3),
    (3, 4),
)


###############################################################################
# Observation Configuration
###############################################################################

TOF_HISTORY_SIZE = 20


###############################################################################
# Temporal Observation Configuration
###############################################################################

VELOCITY_WINDOW = 5
MIN_VALID_DT = 0.02
STATIONARY_THRESHOLD = 50.0


###############################################################################
# Motion Classification Configuration
###############################################################################

MOTION_APPROACHING = "Approaching"
MOTION_STATIONARY = "Stationary"
MOTION_RECEDING = "Receding"
MOTION_UNKNOWN = "Unknown"

MOTION_STATES = (
    MOTION_APPROACHING,
    MOTION_STATIONARY,
    MOTION_RECEDING,
)


###############################################################################
# Motion Persistence Configuration
###############################################################################

# Motion persistence is a bounded temporal consistency / evidence score.
# It is not a probability and it is not a percentage.

MOTION_PERSISTENCE_MIN = 0
MOTION_PERSISTENCE_MAX = 100
MOTION_PERSISTENCE_STEP = 1


###############################################################################
# Dashboard / Logging Configuration
###############################################################################

REFRESH_PERIOD = 0.02

# Full six-sensor logging every observation would itself become a bottleneck.
DEBUG_LOG_PERIOD = 1.0

# The Observation Engine can process every received observation while the
# browser payload is capped to a responsive but lighter 10 Hz.
UI_PUBLISH_PERIOD = 0.10


###############################################################################
# Distance Configuration
###############################################################################

MAX_DISTANCE_MM = 3000
INVALID_DISTANCE_MM = 4000


###############################################################################
# Confidence Configuration
###############################################################################

# These are the same engineering normalization references used in v2.3.0.
# They were derived from earlier datasets and should be recalibrated later
# using representative 4x4 data. Confidence is an engineering measurement-
# quality heuristic; it is not a probability.

CONF_SIGNAL_REFERENCE = 1000.0
CONF_SIGMA_REFERENCE = 64.0
CONF_AMBIENT_REFERENCE = 128.0
CONF_REFLECTANCE_REFERENCE = 255.0
CONF_SPADS_REFERENCE = 3840.0

CONF_WEIGHT_STATUS = 30.0
CONF_WEIGHT_SIGNAL = 30.0
CONF_WEIGHT_SIGMA = 20.0
CONF_WEIGHT_AMBIENT = 5.0
CONF_WEIGHT_REFLECTANCE = 5.0
CONF_WEIGHT_TARGETS = 5.0
CONF_WEIGHT_SPADS = 5.0


###############################################################################
# Web UI
###############################################################################

ui = WebUI()


###############################################################################
# Data Models
###############################################################################

@dataclass
class ToFFrame:
    sensor_index: int
    sensor_id: str
    sensor_name: str
    position: str
    mux_channel: int

    frame_number: int
    timestamp: int

    distance: np.ndarray
    signal: np.ndarray
    sigma: np.ndarray
    status: np.ndarray
    reflectance: np.ndarray
    ambient: np.ndarray
    targets: np.ndarray
    spads: np.ndarray
    confidence: np.ndarray


@dataclass
class MultiToFFrame:
    observation_number: int
    timestamp: int
    sensor_frames: list


@dataclass
class SectorObservation:
    sector_id: int
    sector_name: str

    distance_mm: int
    zone_id: int = -1

    confidence: float = 0.0

    signal_kcps_per_spad: int = 0
    sigma: int = 0
    target_status: int = 255
    reflectance: int = 0
    ambient_kcps_per_spad: int = 0
    targets: int = 0
    spads: int = 0

    velocity_mmps: float = 0.0
    velocity_valid: bool = False
    velocity_state: str = MOTION_UNKNOWN

    motion_persistence: int = 0
    approaching_persistence: int = 0
    stationary_persistence: int = 0
    receding_persistence: int = 0


@dataclass
class ToFObservation:
    sensor_index: int
    sensor_id: str
    sensor_name: str
    position: str
    mux_channel: int

    status: str
    frame_number: int
    timestamp: int
    fps: float

    sectors: list
    history_size: int = 0


@dataclass
class MultiToFObservation:
    observation_number: int
    timestamp: int
    sensors: list


###############################################################################
# Confidence Engine
###############################################################################

class ConfidenceEngine:

    @staticmethod
    def _clamp(value):
        return max(
            0.0,
            min(
                1.0,
                float(value),
            ),
        )

    def normalize_status(self, status):
        status = int(status)

        if status == 5:
            return 1.0

        if status in (6, 9):
            return 0.5

        return 0.0

    def normalize_signal(self, signal):
        signal = float(signal)

        if signal <= 0.0:
            return 0.0

        score = (
            math.log10(signal + 1.0)
            /
            math.log10(CONF_SIGNAL_REFERENCE + 1.0)
        )

        return self._clamp(score)

    def normalize_sigma(self, sigma):
        return self._clamp(
            1.0
            -
            float(sigma)
            /
            CONF_SIGMA_REFERENCE
        )

    def normalize_ambient(self, ambient):
        return self._clamp(
            1.0
            -
            float(ambient)
            /
            CONF_AMBIENT_REFERENCE
        )

    def normalize_reflectance(self, reflectance):
        return self._clamp(
            float(reflectance)
            /
            CONF_REFLECTANCE_REFERENCE
        )

    @staticmethod
    def normalize_targets(targets):
        return 1.0 if int(targets) > 0 else 0.0

    def normalize_spads(self, spads):
        return self._clamp(
            float(spads)
            /
            CONF_SPADS_REFERENCE
        )

    def calculate(
        self,
        distance,
        signal,
        sigma,
        status,
        reflectance,
        ambient,
        targets,
        spads,
    ):
        distance = int(distance)
        targets = int(targets)

        if distance <= 0:
            return 0.0

        if distance > MAX_DISTANCE_MM:
            return 0.0

        if targets <= 0:
            return 0.0

        status_score = self.normalize_status(status)

        if status_score <= 0.0:
            return 0.0

        score = (
            CONF_WEIGHT_STATUS
            *
            status_score
            +
            CONF_WEIGHT_SIGNAL
            *
            self.normalize_signal(signal)
            +
            CONF_WEIGHT_SIGMA
            *
            self.normalize_sigma(sigma)
            +
            CONF_WEIGHT_AMBIENT
            *
            self.normalize_ambient(ambient)
            +
            CONF_WEIGHT_REFLECTANCE
            *
            self.normalize_reflectance(reflectance)
            +
            CONF_WEIGHT_TARGETS
            *
            self.normalize_targets(targets)
            +
            CONF_WEIGHT_SPADS
            *
            self.normalize_spads(spads)
        )

        return round(
            max(
                0.0,
                min(
                    100.0,
                    score,
                ),
            ),
            1,
        )

    def calculate_image(
        self,
        distance,
        signal,
        sigma,
        status,
        reflectance,
        ambient,
        targets,
        spads,
    ):
        result = np.zeros(
            (
                IMAGE_ROWS,
                IMAGE_COLS,
            ),
            dtype=np.float32,
        )

        for row in range(IMAGE_ROWS):
            for column in range(IMAGE_COLS):
                result[
                    row,
                    column,
                ] = self.calculate(
                    distance[row, column],
                    signal[row, column],
                    sigma[row, column],
                    status[row, column],
                    reflectance[row, column],
                    ambient[row, column],
                    targets[row, column],
                    spads[row, column],
                )

        return result


confidence_engine = ConfidenceEngine()


###############################################################################
# Motion Persistence Engine
###############################################################################

class MotionPersistenceEngine:

    def __init__(self):
        self.counters = {
            sector_id: {
                MOTION_APPROACHING: 0,
                MOTION_STATIONARY: 0,
                MOTION_RECEDING: 0,
            }
            for sector_id in range(
                TOF_SECTOR_COUNT
            )
        }

    @staticmethod
    def _clamp(value):
        return max(
            MOTION_PERSISTENCE_MIN,
            min(
                MOTION_PERSISTENCE_MAX,
                int(value),
            ),
        )

    def update(self, sector):
        counters = self.counters[
            sector.sector_id
        ]

        current_state = (
            sector.velocity_state
        )

        if current_state in MOTION_STATES:
            for state in MOTION_STATES:
                if state == current_state:
                    counters[state] = self._clamp(
                        counters[state]
                        +
                        MOTION_PERSISTENCE_STEP
                    )
                else:
                    counters[state] = self._clamp(
                        counters[state]
                        -
                        MOTION_PERSISTENCE_STEP
                    )
        else:
            for state in MOTION_STATES:
                counters[state] = self._clamp(
                    counters[state]
                    -
                    MOTION_PERSISTENCE_STEP
                )

        sector.approaching_persistence = counters[
            MOTION_APPROACHING
        ]

        sector.stationary_persistence = counters[
            MOTION_STATIONARY
        ]

        sector.receding_persistence = counters[
            MOTION_RECEDING
        ]

        if current_state in MOTION_STATES:
            sector.motion_persistence = counters[
                current_state
            ]
        else:
            sector.motion_persistence = 0


###############################################################################
# Build Sector Observations
###############################################################################

def build_sector_observation(
    frame,
    sector_id,
    start_column,
    end_column,
):
    distance_sector = frame.distance[
        :,
        start_column:end_column,
    ]

    confidence_sector = frame.confidence[
        :,
        start_column:end_column,
    ]

    valid = distance_sector.astype(
        np.int32,
        copy=True,
    )

    invalid_mask = (
        (valid <= 0)
        |
        (valid > MAX_DISTANCE_MM)
        |
        (confidence_sector <= 0.0)
    )

    valid[
        invalid_mask
    ] = INVALID_DISTANCE_MM

    local_index = int(
        np.argmin(
            valid
        )
    )

    (
        row,
        local_column,
    ) = np.unravel_index(
        local_index,
        valid.shape,
    )

    distance = int(
        valid[
            row,
            local_column,
        ]
    )

    if distance == INVALID_DISTANCE_MM:
        return SectorObservation(
            sector_id=sector_id,
            sector_name=SECTOR_NAMES[
                sector_id
            ],
            distance_mm=0,
        )

    oriented_column = (
        start_column
        +
        local_column
    )

    # The Python image is horizontally flipped to create the established
    # local orientation. Recover the sensor's raw zone ID for diagnostics.
    raw_column = (
        IMAGE_COLS
        -
        1
        -
        oriented_column
    )

    zone_id = (
        row
        *
        IMAGE_COLS
        +
        raw_column
    )

    return SectorObservation(
        sector_id=sector_id,
        sector_name=SECTOR_NAMES[
            sector_id
        ],
        distance_mm=distance,
        zone_id=int(zone_id),
        confidence=round(
            float(
                frame.confidence[
                    row,
                    oriented_column,
                ]
            ),
            1,
        ),
        signal_kcps_per_spad=int(
            frame.signal[
                row,
                oriented_column,
            ]
        ),
        sigma=int(
            frame.sigma[
                row,
                oriented_column,
            ]
        ),
        target_status=int(
            frame.status[
                row,
                oriented_column,
            ]
        ),
        reflectance=int(
            frame.reflectance[
                row,
                oriented_column,
            ]
        ),
        ambient_kcps_per_spad=int(
            frame.ambient[
                row,
                oriented_column,
            ]
        ),
        targets=int(
            frame.targets[
                row,
                oriented_column,
            ]
        ),
        spads=int(
            frame.spads[
                row,
                oriented_column,
            ]
        ),
    )


def build_sector_observations(frame):
    sectors = []

    for (
        sector_id,
        (
            start_column,
            end_column,
        ),
    ) in enumerate(
        SECTOR_RANGES
    ):
        sectors.append(
            build_sector_observation(
                frame=frame,
                sector_id=sector_id,
                start_column=start_column,
                end_column=end_column,
            )
        )

    return sectors


###############################################################################
# Per-Sensor Observation Engine
###############################################################################

class ObservationEngine:

    def __init__(
        self,
        sensor_config,
    ):
        self.sensor_config = (
            sensor_config
        )

        self.observation_history = deque(
            maxlen=TOF_HISTORY_SIZE
        )

        self.velocity_history = {
            sector_id: deque(
                maxlen=VELOCITY_WINDOW
            )
            for sector_id in range(
                TOF_SECTOR_COUNT
            )
        }

        self.motion_persistence_engine = (
            MotionPersistenceEngine()
        )

    def previous_observation(self):
        if len(
            self.observation_history
        ) == 0:
            return None

        return self.observation_history[
            -1
        ]

    def process_frame(
        self,
        frame,
        current_fps,
    ):
        sectors = (
            build_sector_observations(
                frame
            )
        )

        observation = ToFObservation(
            sensor_index=frame.sensor_index,
            sensor_id=frame.sensor_id,
            sensor_name=frame.sensor_name,
            position=frame.position,
            mux_channel=frame.mux_channel,
            status="ONLINE",
            frame_number=frame.frame_number,
            timestamp=frame.timestamp,
            fps=current_fps,
            sectors=sectors,
        )

        self._estimate_velocity(
            observation
        )

        self._filter_velocity(
            observation
        )

        self._classify_motion(
            observation
        )

        self._update_motion_persistence(
            observation
        )

        self.observation_history.append(
            observation
        )

        observation.history_size = len(
            self.observation_history
        )

        return observation

    def _estimate_velocity(
        self,
        observation,
    ):
        previous = (
            self.previous_observation()
        )

        if previous is None:
            for sector in observation.sectors:
                sector.velocity_mmps = 0.0
                sector.velocity_valid = False
            return

        dt = (
            observation.timestamp
            -
            previous.timestamp
        ) / 1000.0

        if dt < MIN_VALID_DT:
            dt = MIN_VALID_DT

        for (
            current,
            old,
        ) in zip(
            observation.sectors,
            previous.sectors,
        ):
            if (
                current.distance_mm <= 0
                or
                old.distance_mm <= 0
                or
                current.confidence <= 0.0
                or
                old.confidence <= 0.0
            ):
                current.velocity_mmps = 0.0
                current.velocity_valid = False
                continue

            velocity = (
                current.distance_mm
                -
                old.distance_mm
            ) / dt

            current.velocity_mmps = velocity
            current.velocity_valid = True

            self.velocity_history[
                current.sector_id
            ].append(
                velocity
            )

    def _filter_velocity(
        self,
        observation,
    ):
        for sector in observation.sectors:
            if not sector.velocity_valid:
                sector.velocity_mmps = 0.0
                continue

            history = self.velocity_history[
                sector.sector_id
            ]

            if len(history) == 0:
                continue

            sector.velocity_mmps = round(
                sum(history)
                /
                len(history),
                1,
            )

    def _classify_motion(
        self,
        observation,
    ):
        for sector in observation.sectors:
            if not sector.velocity_valid:
                sector.velocity_state = (
                    MOTION_UNKNOWN
                )
                continue

            if (
                sector.velocity_mmps
                <
                -STATIONARY_THRESHOLD
            ):
                sector.velocity_state = (
                    MOTION_APPROACHING
                )

            elif (
                sector.velocity_mmps
                >
                STATIONARY_THRESHOLD
            ):
                sector.velocity_state = (
                    MOTION_RECEDING
                )

            else:
                sector.velocity_state = (
                    MOTION_STATIONARY
                )

    def _update_motion_persistence(
        self,
        observation,
    ):
        for sector in observation.sectors:
            self.motion_persistence_engine.update(
                sector
            )


observation_engines = [
    ObservationEngine(
        sensor_config
    )
    for sensor_config in SENSOR_CONFIGS
]


###############################################################################
# Global Runtime State
###############################################################################

last_sensor_frame_numbers = [
    None
    for _ in range(
        NUM_SENSORS
    )
]

last_sensor_timestamps = [
    None
    for _ in range(
        NUM_SENSORS
    )
]

sensor_fps = [
    0.0
    for _ in range(
        NUM_SENSORS
    )
]

last_observation_number = -1
last_debug_log_time = 0.0
last_wait_log_time = 0.0
last_ui_publish_time = 0.0


###############################################################################
# Logging
###############################################################################

def sensor_init_description(code):
    descriptions = {
        0: "initialization not completed",
        1: "sensor initialized successfully",
        -1: "mux channel selection failed",
        -2: "sensor probe / begin failed",
        -3: "128-byte packet-size configuration failed",
        -4: "4x4 resolution configuration failed",
        -5: "30 Hz ranging-frequency configuration failed",
        -6: "20 ms integration-time configuration failed",
        -7: "startRanging() failed",
        -10: "I2C mux initialization failed",
    }

    return descriptions.get(
        int(code),
        "unknown sensor initialization result",
    )


def maybe_log_wait_state():
    global last_wait_log_time

    now = time.time()

    if (
        now
        -
        last_wait_log_time
        <
        1.0
    ):
        return

    last_wait_log_time = now

    try:
        ready_flags = list(
            Bridge.call(
                "get_sensor_ready_flags"
            )
        )

        init_codes = list(
            Bridge.call(
                "get_sensor_init_codes"
            )
        )

        mux_errors = int(
            Bridge.call(
                "get_mux_select_errors"
            )
        )

        read_errors = list(
            Bridge.call(
                "get_sensor_read_errors"
            )
        )

    except Exception as exc:
        print(
            "[TOF] Waiting for Arduino Bridge |",
            exc,
        )
        return

    if all(
        int(flag) == 1
        for flag in ready_flags
    ):
        print(
            "[TOF] All six sensors online | waiting for next six-sensor observation",
            "| mux errors:",
            mux_errors,
            "| read errors:",
            read_errors,
        )
        return

    print(
        "[TOF] Sensor initialization state:"
    )

    for (
        sensor_config,
        ready,
        code,
    ) in zip(
        SENSOR_CONFIGS,
        ready_flags,
        init_codes,
    ):
        print(
            "   ",
            sensor_config[
                "sensor_id"
            ],
            sensor_config[
                "position"
            ],
            "| ready:",
            int(ready),
            "| code:",
            int(code),
            "|",
            sensor_init_description(
                code
            ),
        )


def log_multi_observation(
    observation,
):
    global last_debug_log_time

    now = time.time()

    if (
        now
        -
        last_debug_log_time
        <
        DEBUG_LOG_PERIOD
    ):
        return

    last_debug_log_time = now

    print(
        "------------------------------------------------------------"
    )

    print(
        "Observation:",
        observation.observation_number,
        "| Timestamp:",
        observation.timestamp,
    )

    for sensor in observation.sensors:
        sector_text = []

        for sector in sensor.sectors:
            sector_text.append(
                (
                    f"{sector.sector_name}="
                    f"{sector.distance_mm}mm,"
                    f"C{sector.confidence:.1f},"
                    f"{sector.velocity_state},"
                    f"P{sector.motion_persistence}"
                )
            )

        print(
            sensor.sensor_id,
            sensor.position,
            "| Frame:",
            sensor.frame_number,
            "| FPS:",
            round(
                sensor.fps,
                2,
            ),
            "|",
            " | ".join(
                sector_text
            ),
        )


###############################################################################
# Bridge Array Conversion
###############################################################################

def bridge_array_to_numpy(
    values,
    dtype,
    expected_size,
):
    np_dtype = np.dtype(
        dtype
    )

    if isinstance(
        values,
        (
            bytes,
            bytearray,
            memoryview,
        ),
    ):
        array = np.frombuffer(
            values,
            dtype=np_dtype,
        )
    else:
        array = np.asarray(
            values,
            dtype=np_dtype,
        )

    if array.size != expected_size:
        raise ValueError(
            "Invalid Bridge array size: expected "
            +
            str(expected_size)
            +
            ", received "
            +
            str(array.size)
        )

    return array


def convert_flat_array_to_sensor_images(
    values,
    dtype,
):
    array = bridge_array_to_numpy(
        values=values,
        dtype=dtype,
        expected_size=TOTAL_ZONES,
    )

    images = array.reshape(
        (
            NUM_SENSORS,
            IMAGE_ROWS,
            IMAGE_COLS,
        )
    )

    # Preserve the orientation convention used by v2.3.0:
    # flip left/right independently for every ToF image.
    images = np.flip(
        images,
        axis=2,
    )

    return images.copy()


###############################################################################
# Read Immutable Six-Sensor Snapshot
###############################################################################

def read_multi_tof_snapshot():

    try:
        pending_observation = int(
            Bridge.call(
                "get_pending_observation"
            )
        )

    except Exception:
        maybe_log_wait_state()
        return None

    if pending_observation == 0:
        maybe_log_wait_state()
        return None

    try:
        observation_timestamp = int(
            Bridge.call(
                "get_observation_timestamp"
            )
        )

        frame_counters = list(
            Bridge.call(
                "get_sensor_frame_counters"
            )
        )

        sensor_timestamps = list(
            Bridge.call(
                "get_sensor_timestamps"
            )
        )

        distance_raw = Bridge.call(
            "get_distance"
        )

        signal_raw = Bridge.call(
            "get_signal"
        )

        sigma_raw = Bridge.call(
            "get_sigma"
        )

        status_raw = Bridge.call(
            "get_status"
        )

        reflectance_raw = Bridge.call(
            "get_reflectance"
        )

        ambient_raw = Bridge.call(
            "get_ambient"
        )

        targets_raw = Bridge.call(
            "get_targets"
        )

        spads_raw = Bridge.call(
            "get_spads"
        )

    except Exception as exc:
        print(
            "[TOF] Six-sensor snapshot read error:",
            exc,
        )
        return None

    if (
        len(frame_counters)
        !=
        NUM_SENSORS
        or
        len(sensor_timestamps)
        !=
        NUM_SENSORS
    ):
        print(
            "[TOF] Invalid six-sensor metadata."
        )
        return None

    try:
        distance = convert_flat_array_to_sensor_images(
            distance_raw,
            np.int16,
        )

        signal = convert_flat_array_to_sensor_images(
            signal_raw,
            np.uint32,
        )

        sigma = convert_flat_array_to_sensor_images(
            sigma_raw,
            np.uint16,
        )

        status = convert_flat_array_to_sensor_images(
            status_raw,
            np.uint8,
        )

        reflectance = convert_flat_array_to_sensor_images(
            reflectance_raw,
            np.uint8,
        )

        ambient = convert_flat_array_to_sensor_images(
            ambient_raw,
            np.uint32,
        )

        targets = convert_flat_array_to_sensor_images(
            targets_raw,
            np.uint8,
        )

        spads = convert_flat_array_to_sensor_images(
            spads_raw,
            np.uint32,
        )

    except Exception as exc:
        print(
            "[TOF] Snapshot conversion error:",
            exc,
        )
        return None

    # We have copied every published field into Python-owned memory.
    # Release the one-slot MCU publication buffer before confidence / temporal
    # processing and WebUI serialization.
    try:
        consumed = bool(
            Bridge.call(
                "consume_observation",
                pending_observation,
            )
        )

    except Exception as exc:
        print(
            "[TOF] consume_observation error:",
            exc,
        )
        return None

    if not consumed:
        print(
            "[TOF] consume_observation rejected observation",
            pending_observation,
        )
        return None

    sensor_frames = []

    for sensor_index in range(
        NUM_SENSORS
    ):
        sensor_config = SENSOR_CONFIGS[
            sensor_index
        ]

        confidence = (
            confidence_engine.calculate_image(
                distance[
                    sensor_index
                ],
                signal[
                    sensor_index
                ],
                sigma[
                    sensor_index
                ],
                status[
                    sensor_index
                ],
                reflectance[
                    sensor_index
                ],
                ambient[
                    sensor_index
                ],
                targets[
                    sensor_index
                ],
                spads[
                    sensor_index
                ],
            )
        )

        sensor_frames.append(
            ToFFrame(
                sensor_index=sensor_index,
                sensor_id=sensor_config[
                    "sensor_id"
                ],
                sensor_name=sensor_config[
                    "sensor_name"
                ],
                position=sensor_config[
                    "position"
                ],
                mux_channel=sensor_config[
                    "mux_channel"
                ],
                frame_number=int(
                    frame_counters[
                        sensor_index
                    ]
                ),
                timestamp=int(
                    sensor_timestamps[
                        sensor_index
                    ]
                ),
                distance=distance[
                    sensor_index
                ],
                signal=signal[
                    sensor_index
                ],
                sigma=sigma[
                    sensor_index
                ],
                status=status[
                    sensor_index
                ],
                reflectance=reflectance[
                    sensor_index
                ],
                ambient=ambient[
                    sensor_index
                ],
                targets=targets[
                    sensor_index
                ],
                spads=spads[
                    sensor_index
                ],
                confidence=confidence,
            )
        )

    return MultiToFFrame(
        observation_number=pending_observation,
        timestamp=observation_timestamp,
        sensor_frames=sensor_frames,
    )


###############################################################################
# FPS Estimation
###############################################################################

def update_sensor_fps(
    frame,
):
    sensor_index = (
        frame.sensor_index
    )

    previous_frame_number = (
        last_sensor_frame_numbers[
            sensor_index
        ]
    )

    previous_timestamp = (
        last_sensor_timestamps[
            sensor_index
        ]
    )

    if (
        previous_frame_number is not None
        and
        previous_timestamp is not None
    ):
        frame_delta = (
            frame.frame_number
            -
            previous_frame_number
        )

        timestamp_delta = (
            frame.timestamp
            -
            previous_timestamp
        )

        if (
            frame_delta > 0
            and
            timestamp_delta > 0
        ):
            # If Python skips an MCU publication while busy, frame_delta can
            # exceed one. Including it preserves an estimate of the underlying
            # MCU retrieved frame rate.
            sensor_fps[
                sensor_index
            ] = round(
                frame_delta
                *
                1000.0
                /
                timestamp_delta,
                2,
            )

    last_sensor_frame_numbers[
        sensor_index
    ] = frame.frame_number

    last_sensor_timestamps[
        sensor_index
    ] = frame.timestamp

    return sensor_fps[
        sensor_index
    ]


###############################################################################
# Serialization
###############################################################################

def sector_to_dict(
    sector,
):
    return {
        "sector_id":
            sector.sector_id,

        "sector_name":
            sector.sector_name,

        "distance_mm":
            sector.distance_mm,

        "zone_id":
            sector.zone_id,

        "confidence":
            round(
                sector.confidence,
                1,
            ),

        "signal_kcps_per_spad":
            sector.signal_kcps_per_spad,

        "sigma":
            sector.sigma,

        "target_status":
            sector.target_status,

        "reflectance":
            sector.reflectance,

        "ambient_kcps_per_spad":
            sector.ambient_kcps_per_spad,

        "targets":
            sector.targets,

        "spads":
            sector.spads,

        "velocity_mmps":
            round(
                sector.velocity_mmps,
                1,
            ),

        "velocity_valid":
            sector.velocity_valid,

        "velocity_state":
            sector.velocity_state,

        "motion_persistence":
            sector.motion_persistence,

        "motion_persistence_counters": {
            "approaching":
                sector.approaching_persistence,

            "stationary":
                sector.stationary_persistence,

            "receding":
                sector.receding_persistence,
        },
    }


def observation_to_dict(
    observation,
):
    return {
        "sensor_index":
            observation.sensor_index,

        "sensor_id":
            observation.sensor_id,

        "sensor_name":
            observation.sensor_name,

        "position":
            observation.position,

        "mux_channel":
            observation.mux_channel,

        "status":
            observation.status,

        "frame_number":
            observation.frame_number,

        "timestamp":
            observation.timestamp,

        "fps":
            observation.fps,

        "history_size":
            observation.history_size,

        "sectors": [
            sector_to_dict(
                sector
            )
            for sector in observation.sectors
        ],
    }


def trusted_nearest_distance(
    frame,
):
    trusted = frame.distance.astype(
        np.int32,
        copy=True,
    )

    invalid = (
        (trusted <= 0)
        |
        (trusted > MAX_DISTANCE_MM)
        |
        (frame.confidence <= 0.0)
    )

    trusted[
        invalid
    ] = INVALID_DISTANCE_MM

    nearest = int(
        np.min(
            trusted
        )
    )

    if nearest == INVALID_DISTANCE_MM:
        return 0

    return nearest


###############################################################################
# WebUI Payload
###############################################################################

def publish_webui(
    frame,
    observation,
):
    global last_ui_publish_time

    now = time.time()

    if (
        now
        -
        last_ui_publish_time
        <
        UI_PUBLISH_PERIOD
    ):
        return

    last_ui_publish_time = now

    sensor_payloads = []

    for (
        sensor_frame,
        sensor_observation,
    ) in zip(
        frame.sensor_frames,
        observation.sensors,
    ):
        sensor_payloads.append(
            {
                "sensor_id":
                    sensor_frame.sensor_id,

                "sensor_name":
                    sensor_frame.sensor_name,

                "position":
                    sensor_frame.position,

                "mux_channel":
                    sensor_frame.mux_channel,

                "frame_number":
                    sensor_frame.frame_number,

                "timestamp":
                    sensor_frame.timestamp,

                "fps":
                    sensor_observation.fps,

                "image":
                    sensor_frame.distance.tolist(),

                "confidence_image":
                    sensor_frame.confidence.tolist(),

                "nearest":
                    trusted_nearest_distance(
                        sensor_frame
                    ),

                "observation":
                    observation_to_dict(
                        sensor_observation
                    ),
            }
        )

    message = {
        "app_name":
            APP_NAME,

        "app_version":
            APP_VERSION,

        "observation_number":
            observation.observation_number,

        "timestamp":
            observation.timestamp,

        "configuration": {
            "sensor_count":
                NUM_SENSORS,

            "resolution":
                "4x4",

            "zones_per_sensor":
                NUM_ZONES,

            "total_zones":
                TOTAL_ZONES,

            "requested_ranging_frequency_hz":
                REQUESTED_RANGING_FREQUENCY_HZ,

            "measured_retrieved_rate_hz_approx":
                MEASURED_RETRIEVED_RATE_HZ,

            "integration_time_ms":
                INTEGRATION_TIME_MS,

            "i2c_hz":
                I2C_SPEED_HZ,

            "packet_size_bytes":
                TOF_PACKET_SIZE,

            "sector_columns": {
                "S0": [0],
                "S1": [1, 2],
                "S2": [3],
            },
        },

        "sensors":
            sensor_payloads,
    }

    # ------------------------------------------------------------------------
    # Backward-compatible single-ToF dashboard fields
    #
    # Existing v2.3.0 UI can continue to display the FRONT sensor (T2)
    # until the web frontend is upgraded for six ToFs.
    # ------------------------------------------------------------------------

    front_index = 1

    front_frame = frame.sensor_frames[
        front_index
    ]

    front_observation = observation.sensors[
        front_index
    ]

    message[
        "image"
    ] = front_frame.distance.tolist()

    message[
        "confidence_image"
    ] = front_frame.confidence.tolist()

    message[
        "observation"
    ] = observation_to_dict(
        front_observation
    )

    message[
        "frame"
    ] = front_frame.frame_number

    message[
        "fps"
    ] = front_observation.fps

    message[
        "nearest"
    ] = trusted_nearest_distance(
        front_frame
    )

    message[
        "left"
    ] = front_observation.sectors[
        0
    ].distance_mm

    message[
        "center"
    ] = front_observation.sectors[
        1
    ].distance_mm

    message[
        "right"
    ] = front_observation.sectors[
        2
    ].distance_mm

    ui.send_message(
        "tof_frame",
        message,
    )


###############################################################################
# Process Multi-ToF Frame
###############################################################################

def process_multi_tof_frame(
    frame,
):
    sensor_observations = []

    for sensor_frame in frame.sensor_frames:
        current_fps = update_sensor_fps(
            sensor_frame
        )

        sensor_observations.append(
            observation_engines[
                sensor_frame.sensor_index
            ].process_frame(
                frame=sensor_frame,
                current_fps=current_fps,
            )
        )

    return MultiToFObservation(
        observation_number=frame.observation_number,
        timestamp=frame.timestamp,
        sensors=sensor_observations,
    )


###############################################################################
# Main Publish Function
###############################################################################

def publish_frame():

    global last_observation_number

    frame = (
        read_multi_tof_snapshot()
    )

    if frame is None:
        return

    if (
        frame.observation_number
        ==
        last_observation_number
    ):
        return

    last_observation_number = (
        frame.observation_number
    )

    observation = (
        process_multi_tof_frame(
            frame
        )
    )

    log_multi_observation(
        observation
    )

    publish_webui(
        frame,
        observation,
    )


###############################################################################
# Browser Events
###############################################################################

def on_connect(
    client,
):
    print(
        "Browser Connected:",
        client,
    )


def on_disconnect(
    client,
):
    print(
        "Browser Disconnected:",
        client,
    )


def get_initial_state(
    client,
    data,
):
    print(
        "Initial state requested."
    )

    publish_frame()


ui.on_connect(
    on_connect
)

ui.on_disconnect(
    on_disconnect
)

ui.on_message(
    "get_initial_state",
    get_initial_state
)


###############################################################################
# Main Application Loop
###############################################################################

def loop():

    publish_frame()

    time.sleep(
        REFRESH_PERIOD
    )


###############################################################################
# Startup
###############################################################################

print()

print(
    "============================================================"
)

print(
    APP_NAME
)

print(
    "Version                    :",
    APP_VERSION
)

print(
    "============================================================"
)

print(
    "Sensors                    :",
    NUM_SENSORS,
    "x VL53L5CX"
)

print(
    "Resolution                 : 4 x 4"
)

print(
    "Zones / sensor             :",
    NUM_ZONES
)

print(
    "Total zones                :",
    TOTAL_ZONES
)

print(
    "Requested ranging rate     :",
    REQUESTED_RANGING_FREQUENCY_HZ,
    "Hz"
)

print(
    "Measured retrieval (~)     :",
    MEASURED_RETRIEVED_RATE_HZ,
    "Hz / sensor"
)

print(
    "Integration time           :",
    INTEGRATION_TIME_MS,
    "ms"
)

print(
    "I2C                        :",
    I2C_SPEED_HZ,
    "Hz"
)

print(
    "Packet size                :",
    TOF_PACKET_SIZE,
    "bytes"
)

print()

print(
    "Mux mapping:"
)

for sensor in SENSOR_CONFIGS:
    print(
        " ",
        sensor[
            "sensor_id"
        ],
        "-> CH",
        sensor[
            "mux_channel"
        ],
        "->",
        sensor[
            "position"
        ],
        sep="",
    )

print()

print(
    "Sector mapping             : S0=col0, S1=cols1-2, S2=col3"
)

print(
    "Observation Engine         : ENABLED"
)

print(
    "Confidence Engine          : ENABLED"
)

print(
    "Velocity Estimation        : ENABLED"
)

print(
    "Velocity Smoothing         : ENABLED"
)

print(
    "Motion Classification      : ENABLED"
)

print(
    "Motion Persistence         : ENABLED"
)

print()

print(
    "Waiting for Arduino Bridge / six ToF sensors..."
)

print()


###############################################################################
# Run
###############################################################################

App.run(
    user_loop=loop
)
