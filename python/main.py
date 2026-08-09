# SPDX-License-Identifier: MPL-2.0

###############################################################################
#
# SixthSense
#
# Version : 2.3.0
#
# Module  : Python Backend
#
# Platform: Arduino UNO Q
#
# Features
#
#   • Complete VL53L5CX Bridge snapshot
#   • 64-zone confidence estimation
#   • Sector observations
#   • Temporal history
#   • Velocity estimation
#   • Velocity smoothing
#   • Motion classification
#   • Motion persistence
#   • Sensor initialization diagnostics
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

APP_VERSION = "2.3.0"


###############################################################################
# Sensor Configuration
###############################################################################

TOF_SENSOR_ID = "tof_01"

TOF_SENSOR_NAME = "Prototype ToF"


###############################################################################
# Sensor Image
###############################################################################

IMAGE_ROWS = 8

IMAGE_COLS = 8

NUM_ZONES = 64


###############################################################################
# Sector Configuration
###############################################################################

TOF_SECTOR_COUNT = 3

SECTOR_NAMES = [

    "Sector 0",

    "Sector 1",

    "Sector 2"

]


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

    MOTION_RECEDING

)


###############################################################################
# Motion Persistence Configuration
###############################################################################

#
# Motion persistence is a bounded evidence score.
#
# It is not a percentage.
#
# Range:
#
#     0 ... 100
#

MOTION_PERSISTENCE_MIN = 0

MOTION_PERSISTENCE_MAX = 100

MOTION_PERSISTENCE_STEP = 1


###############################################################################
# Dashboard Configuration
###############################################################################

SHOW_HEATMAP = True

SHOW_JSON = True

REFRESH_PERIOD = 0.02


###############################################################################
# Distance Configuration
###############################################################################

MAX_DISTANCE_MM = 3000

INVALID_DISTANCE_MM = 4000


###############################################################################
# Confidence Configuration
###############################################################################

#
# Initial normalization references.
#
# These are engineering values based on the
# VL53L5CX datasets collected so far.
#
# They can later be recalibrated.
#

CONF_SIGNAL_REFERENCE = 1000.0

CONF_SIGMA_REFERENCE = 64.0

CONF_AMBIENT_REFERENCE = 128.0

CONF_REFLECTANCE_REFERENCE = 255.0

CONF_SPADS_REFERENCE = 3840.0


#
# Confidence fusion weights
#
# Sum = 100
#

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
    """
    Complete synchronized VL53L5CX snapshot.
    """

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
class SectorObservation:
    """
    Logical sector observation.
    """

    sector_id: int

    sector_name: str

    distance_mm: int

    zone_id: int = -1

    confidence: float = 0.0

    # VL53L5CX target return signal rate per SPAD.
    signal_kcps_per_spad: int = 0

    sigma: int = 0

    target_status: int = 255

    reflectance: int = 0

    # VL53L5CX ambient photon rate per SPAD.
    ambient_kcps_per_spad: int = 0

    targets: int = 0

    spads: int = 0

    velocity_mmps: float = 0.0

    #
    # True only when velocity is calculated from
    # two valid trusted sector observations.
    #

    velocity_valid: bool = False

    #
    # Current velocity-derived motion classification.
    #

    velocity_state: str = MOTION_UNKNOWN

    #
    # Persistence score corresponding to the
    # current velocity state.
    #
    # Example:
    #
    #     Velocity State     : Approaching
    #     Motion Persistence : 80
    #

    motion_persistence: int = 0

    #
    # Internal persistence counters exposed for
    # debugging and future reasoning layers.
    #

    approaching_persistence: int = 0

    stationary_persistence: int = 0

    receding_persistence: int = 0

@dataclass
class ToFObservation:
    """
    Complete SixthSense ToF observation.
    """

    sensor_id: str

    sensor_name: str

    status: str

    frame_number: int

    timestamp: int

    fps: float

    sectors: list

    history_size: int = 0


###############################################################################
# Global State
###############################################################################

last_frame_counter = -1

last_timestamp = None

fps = 0.0

last_wait_log_time = 0.0


###############################################################################
# Confidence Engine
###############################################################################

class ConfidenceEngine:
    """
    Estimate confidence for every VL53L5CX zone.

    Output range:

        0.0 ... 100.0
    """

    ###########################################################################
    # Clamp
    ###########################################################################

    @staticmethod
    def _clamp(
        value
    ):

        return max(

            0.0,

            min(
                1.0,
                float(
                    value
                )
            )

        )

    ###########################################################################
    # Target Status
    ###########################################################################

    def normalize_status(
        self,
        status
    ):
        """
        VL53L5CX documentation interpretation:

        status 5:
            100% status validity

        status 6 or 9:
            50% confidence

        all other statuses:
            below 50%.

        For this conservative implementation,
        undocumented lower-confidence statuses
        are assigned zero.
        """

        status = int(
            status
        )

        if status == 5:

            return 1.0

        if status in (
            6,
            9
        ):

            return 0.5

        return 0.0

    ###########################################################################
    # Signal
    ###########################################################################

    def normalize_signal(
        self,
        signal
    ):

        signal = float(
            signal
        )

        if signal <= 0.0:

            return 0.0

        score = (

            math.log10(
                signal
                +
                1.0
            )

            /

            math.log10(
                CONF_SIGNAL_REFERENCE
                +
                1.0
            )

        )

        return self._clamp(
            score
        )

    ###########################################################################
    # Sigma
    ###########################################################################

    def normalize_sigma(
        self,
        sigma
    ):

        score = (

            1.0

            -

            float(
                sigma
            )

            /

            CONF_SIGMA_REFERENCE

        )

        return self._clamp(
            score
        )

    ###########################################################################
    # Ambient
    ###########################################################################

    def normalize_ambient(
        self,
        ambient
    ):

        score = (

            1.0

            -

            float(
                ambient
            )

            /

            CONF_AMBIENT_REFERENCE

        )

        return self._clamp(
            score
        )

    ###########################################################################
    # Reflectance
    ###########################################################################

    def normalize_reflectance(
        self,
        reflectance
    ):

        score = (

            float(
                reflectance
            )

            /

            CONF_REFLECTANCE_REFERENCE

        )

        return self._clamp(
            score
        )

    ###########################################################################
    # Targets
    ###########################################################################

    def normalize_targets(
        self,
        targets
    ):

        if int(
            targets
        ) > 0:

            return 1.0

        return 0.0

    ###########################################################################
    # SPADs
    ###########################################################################

    def normalize_spads(
        self,
        spads
    ):

        score = (

            float(
                spads
            )

            /

            CONF_SPADS_REFERENCE

        )

        return self._clamp(
            score
        )

    ###########################################################################
    # Calculate One Zone
    ###########################################################################

    def calculate(
        self,
        distance,
        signal,
        sigma,
        status,
        reflectance,
        ambient,
        targets,
        spads
    ):

        distance = int(
            distance
        )

        targets = int(
            targets
        )

        #######################################################################
        # Fundamental validity gates
        #######################################################################

        if distance <= 0:

            return 0.0

        if distance > MAX_DISTANCE_MM:

            return 0.0

        if targets <= 0:

            return 0.0

        #######################################################################
        # Status
        #######################################################################

        status_score = self.normalize_status(
            status
        )

        if status_score <= 0.0:

            return 0.0

        #######################################################################
        # Continuous quality scores
        #######################################################################

        signal_score = self.normalize_signal(
            signal
        )

        sigma_score = self.normalize_sigma(
            sigma
        )

        ambient_score = self.normalize_ambient(
            ambient
        )

        reflectance_score = (
            self.normalize_reflectance(
                reflectance
            )
        )

        target_score = self.normalize_targets(
            targets
        )

        spad_score = self.normalize_spads(
            spads
        )

        #######################################################################
        # Weighted fusion
        #######################################################################

        score = (

            CONF_WEIGHT_STATUS
            *
            status_score

            +

            CONF_WEIGHT_SIGNAL
            *
            signal_score

            +

            CONF_WEIGHT_SIGMA
            *
            sigma_score

            +

            CONF_WEIGHT_AMBIENT
            *
            ambient_score

            +

            CONF_WEIGHT_REFLECTANCE
            *
            reflectance_score

            +

            CONF_WEIGHT_TARGETS
            *
            target_score

            +

            CONF_WEIGHT_SPADS
            *
            spad_score

        )

        return round(

            max(

                0.0,

                min(
                    100.0,
                    score
                )

            ),

            1

        )

    ###########################################################################
    # Calculate Complete 8x8 Confidence Image
    ###########################################################################

    def calculate_image(
        self,
        distance,
        signal,
        sigma,
        status,
        reflectance,
        ambient,
        targets,
        spads
    ):

        result = np.zeros(

            (
                IMAGE_ROWS,
                IMAGE_COLS
            ),

            dtype=np.float32

        )

        for row in range(
            IMAGE_ROWS
        ):

            for column in range(
                IMAGE_COLS
            ):

                result[
                    row,
                    column
                ] = self.calculate(

                    distance[
                        row,
                        column
                    ],

                    signal[
                        row,
                        column
                    ],

                    sigma[
                        row,
                        column
                    ],

                    status[
                        row,
                        column
                    ],

                    reflectance[
                        row,
                        column
                    ],

                    ambient[
                        row,
                        column
                    ],

                    targets[
                        row,
                        column
                    ],

                    spads[
                        row,
                        column
                    ]

                )

        return result


###############################################################################
# Confidence Engine Instance
###############################################################################

confidence_engine = ConfidenceEngine()


###############################################################################
# Motion Persistence Engine
###############################################################################

class MotionPersistenceEngine:
    """
    Maintain independent bounded persistence counters
    for Approaching, Stationary, and Receding motion.

    Update rules:

        Approaching:
            Approaching += 1
            Stationary  -= 1
            Receding    -= 1

        Stationary:
            Approaching -= 1
            Stationary  += 1
            Receding    -= 1

        Receding:
            Approaching -= 1
            Stationary  -= 1
            Receding    += 1

        Any other classification:
            Approaching -= 1
            Stationary  -= 1
            Receding    -= 1

    Every counter is saturated to the range 0 ... 100.

    The score represents accumulated motion consistency.
    It is not a percentage.
    """

    def __init__(
        self
    ):

        self.counters = {

            sector_id: {

                MOTION_APPROACHING:
                    0,

                MOTION_STATIONARY:
                    0,

                MOTION_RECEDING:
                    0

            }

            for sector_id in range(
                TOF_SECTOR_COUNT
            )

        }

    ###########################################################################
    # Clamp Counter
    ###########################################################################

    @staticmethod
    def _clamp(
        value
    ):

        return max(

            MOTION_PERSISTENCE_MIN,

            min(

                MOTION_PERSISTENCE_MAX,

                int(
                    value
                )

            )

        )

    ###########################################################################
    # Update One Sector
    ###########################################################################

    def update(
        self,
        sector
    ):

        counters = self.counters[
            sector.sector_id
        ]

        current_state = (
            sector.velocity_state
        )

        #######################################################################
        # Recognized motion state
        #######################################################################

        if current_state in MOTION_STATES:

            for state in MOTION_STATES:

                if state == current_state:

                    counters[
                        state
                    ] = self._clamp(

                        counters[
                            state
                        ]

                        +

                        MOTION_PERSISTENCE_STEP

                    )

                else:

                    counters[
                        state
                    ] = self._clamp(

                        counters[
                            state
                        ]

                        -

                        MOTION_PERSISTENCE_STEP

                    )

        #######################################################################
        # Any other motion classification
        #######################################################################

        else:

            for state in MOTION_STATES:

                counters[
                    state
                ] = self._clamp(

                    counters[
                        state
                    ]

                    -

                    MOTION_PERSISTENCE_STEP

                )

        #######################################################################
        # Copy all counters into sector observation
        #######################################################################

        sector.approaching_persistence = (

            counters[
                MOTION_APPROACHING
            ]

        )

        sector.stationary_persistence = (

            counters[
                MOTION_STATIONARY
            ]

        )

        sector.receding_persistence = (

            counters[
                MOTION_RECEDING
            ]

        )

        #######################################################################
        # Persistence for current motion state
        #######################################################################

        if current_state in MOTION_STATES:

            sector.motion_persistence = (

                counters[
                    current_state
                ]

            )

        else:

            sector.motion_persistence = 0

###############################################################################
# Observation Engine
###############################################################################

class ObservationEngine:

    def __init__(
        self
    ):

        self.observation_history = deque(
            maxlen=TOF_HISTORY_SIZE
        )

        self.velocity_history = {

            0: deque(
                maxlen=VELOCITY_WINDOW
            ),

            1: deque(
                maxlen=VELOCITY_WINDOW
            ),

            2: deque(
                maxlen=VELOCITY_WINDOW
            )

        }

        self.motion_persistence_engine = (
            MotionPersistenceEngine()
        )

    ###########################################################################
    # Previous Observation
    ###########################################################################

    def previous_observation(
        self
    ):

        if len(
            self.observation_history
        ) == 0:

            return None

        return self.observation_history[
            -1
        ]

    ###########################################################################
    # Process Frame
    ###########################################################################

    def process_frame(
        self,
        frame,
        current_fps
    ):

        sectors = build_sector_observations(
            frame
        )

        observation = ToFObservation(

            sensor_id=
                TOF_SENSOR_ID,

            sensor_name=
                TOF_SENSOR_NAME,

            status=
                "ONLINE",

            frame_number=
                frame.frame_number,

            timestamp=
                frame.timestamp,

            fps=
                current_fps,

            sectors=
                sectors

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

    ###########################################################################
    # Velocity Estimation
    ###########################################################################

    def _estimate_velocity(
        self,
        observation
    ):

        previous = (
            self.previous_observation()
        )

        #######################################################################
        # First observation
        #
        # Velocity cannot be calculated without a previous observation.
        #######################################################################

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
            old
        ) in zip(

            observation.sectors,

            previous.sectors

        ):

            ###################################################################
            # Invalid measurement transition
            #
            # Confidence is used as a validity gate exactly as in v2.2.1.
            # An invalid transition does not create a valid velocity sample.
            ###################################################################

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

            ###################################################################
            # Valid instantaneous velocity
            ###################################################################

            velocity = (

                current.distance_mm

                -

                old.distance_mm

            ) / dt

            current.velocity_mmps = velocity

            current.velocity_valid = True

            ###################################################################
            # Only valid velocity samples enter the smoothing history.
            ###################################################################

            self.velocity_history[
                current.sector_id
            ].append(
                velocity
            )

    ###########################################################################
    # Velocity Smoothing
    ###########################################################################

    def _filter_velocity(
        self,
        observation
    ):

        for sector in observation.sectors:

            #
            # Do not use the stored velocity history when the
            # current velocity transition itself is invalid.
            #

            if not sector.velocity_valid:

                sector.velocity_mmps = 0.0

                continue

            history = self.velocity_history[
                sector.sector_id
            ]

            if len(
                history
            ) == 0:

                continue

            sector.velocity_mmps = round(

                sum(
                    history
                )

                /

                len(
                    history
                ),

                1

            )

    ###########################################################################
    # Motion Classification
    ###########################################################################

    def _classify_motion(
        self,
        observation
    ):

        for sector in observation.sectors:

            ###################################################################
            # Invalid or unavailable velocity
            #
            # A numerical zero caused by an invalid transition is not treated
            # as Stationary. It becomes Unknown.
            ###################################################################

            if not sector.velocity_valid:

                sector.velocity_state = (
                    MOTION_UNKNOWN
                )

                continue

            ###################################################################
            # Approaching
            ###################################################################

            if (

                sector.velocity_mmps

                <

                -STATIONARY_THRESHOLD

            ):

                sector.velocity_state = (
                    MOTION_APPROACHING
                )

            ###################################################################
            # Receding
            ###################################################################

            elif (

                sector.velocity_mmps

                >

                STATIONARY_THRESHOLD

            ):

                sector.velocity_state = (
                    MOTION_RECEDING
                )

            ###################################################################
            # Stationary
            ###################################################################

            else:

                sector.velocity_state = (
                    MOTION_STATIONARY
                )

    ###########################################################################
    # Motion Persistence
    ###########################################################################

    def _update_motion_persistence(
        self,
        observation
    ):

        for sector in observation.sectors:

            self.motion_persistence_engine.update(
                sector
            )


###############################################################################
# Observation Engine Instance
###############################################################################

observation_engine = ObservationEngine()


###############################################################################
# Logging
###############################################################################

def log_wait(
    message
):

    global last_wait_log_time

    now = time.time()

    if (

        now
        -
        last_wait_log_time

        >=

        1.0

    ):

        print(
            message
        )

        last_wait_log_time = now


def log_observation(
    observation
):

    print(
        "------------------------------------------------------------"
    )

    print(
        "Frame:",
        observation.frame_number,
        "| Timestamp:",
        observation.timestamp,
        "| FPS:",
        observation.fps,
        "| History:",
        observation.history_size
    )

    for sector in observation.sectors:

        print(

            sector.sector_name,

            ":",

            sector.distance_mm,

            "mm",

            "| Confidence:",

            sector.confidence,

            "%",

            "| Zone:",

            sector.zone_id,

            "| Status:",

            sector.target_status,

            "| Signal (kcps/SPAD):",

            sector.signal_kcps_per_spad,

            "| Sigma:",

            sector.sigma,

            "| Velocity:",

            round(
                sector.velocity_mmps,
                1
            ),

            "mm/s",

            "| Velocity State:",

            sector.velocity_state,

            "| Motion Persistence:",

            sector.motion_persistence,

            "| Counters A/S/R:",

            str(
                sector.approaching_persistence
            )

            +

            "/"

            +

            str(
                sector.stationary_persistence
            )

            +

            "/"

            +

            str(
                sector.receding_persistence
            )

        )


###############################################################################
# Array Conversion
###############################################################################

def convert_array_to_image(
    values,
    dtype
):
    """
    Convert a 64-element Arduino Bridge value into an oriented 8x8 NumPy array.

    RouterBridge may return:
        - normal Python lists for uint16/int16/uint32 arrays
        - bytes for uint8 arrays

    Both representations are handled here.
    """

    np_dtype = np.dtype(
        dtype
    )

    ###########################################################################
    # RouterBridge binary representation
    ###########################################################################

    if isinstance(
        values,
        (
            bytes,
            bytearray,
            memoryview
        )
    ):

        image = np.frombuffer(
            values,
            dtype=np_dtype
        )

    ###########################################################################
    # Normal list / tuple / array representation
    ###########################################################################

    else:

        image = np.asarray(
            values,
            dtype=np_dtype
        )

    ###########################################################################
    # Validate number of zones
    ###########################################################################

    if image.size != NUM_ZONES:

        raise ValueError(

            "Invalid ToF array size: expected "

            +

            str(
                NUM_ZONES
            )

            +

            ", received "

            +

            str(
                image.size
            )

        )

    ###########################################################################
    # Convert 64 zones -> 8x8 image
    ###########################################################################

    image = image.reshape(
        (
            IMAGE_ROWS,
            IMAGE_COLS
        )
    )

    ###########################################################################
    # Correct sensor orientation
    ###########################################################################

    image = np.fliplr(
        image
    )

    #
    # Make an independent contiguous array.
    #
    # Useful because np.frombuffer() may reference
    # the original Bridge binary buffer.
    #

    return image.copy()


###############################################################################
# Validate Snapshot
###############################################################################

def validate_snapshot_arrays(
    distance,
    signal,
    sigma,
    status,
    reflectance,
    ambient,
    targets,
    spads
):

    arrays = {

        "distance":
            distance,

        "signal":
            signal,

        "sigma":
            sigma,

        "status":
            status,

        "reflectance":
            reflectance,

        "ambient":
            ambient,

        "targets":
            targets,

        "spads":
            spads

    }

    for (
        name,
        values
    ) in arrays.items():

        if values is None:

            print(
                "[TOF] Invalid array:",
                name,
                "is None"
            )

            return False

        if len(
            values
        ) != NUM_ZONES:

            print(
                "[TOF] Invalid array:",
                name,
                "| expected:",
                NUM_ZONES,
                "| received:",
                len(
                    values
                )
            )

            return False

    return True


###############################################################################
# Sensor Initialization Description
###############################################################################

def sensor_init_description(
    code
):

    descriptions = {

        0:
            "initialization not completed",

        1:
            "sensor initialized successfully",

        -1:
            "tof.begin() failed / sensor detection failed",

        -2:
            "8x8 resolution configuration failed",

        -3:
            "15 Hz ranging frequency configuration failed",

        -4:
            "20 ms integration time configuration failed",

        -5:
            "startRanging() failed"

    }

    return descriptions.get(

        int(
            code
        ),

        "unknown sensor initialization result"

    )


###############################################################################
# Read Complete ToF Snapshot
###############################################################################

def read_tof_snapshot():

    ###########################################################################
    # Bridge diagnostics
    ###########################################################################

    try:

        ready = Bridge.call(
            "sensor_ready"
        )

        init_code = Bridge.call(
            "get_sensor_init_code"
        )

        live_counter = Bridge.call(
            "get_live_frame_counter"
        )

    except Exception as e:

        log_wait(

            "[TOF] Waiting for Arduino Bridge | "

            +

            str(
                e
            )

        )

        return None

    ###########################################################################
    # Sensor initialization failed
    ###########################################################################

    if not ready:

        log_wait(

            "[TOF] Sensor initialization FAILED"

            +

            " | code = "

            +

            str(
                init_code
            )

            +

            " | "

            +

            sensor_init_description(
                init_code
            )

        )

        return None

    ###########################################################################
    # Sensor initialized, but first frame not yet available
    ###########################################################################

    if live_counter == 0:

        log_wait(

            "[TOF] Sensor initialized successfully"

            +

            " | waiting for first ranging frame"

        )

        return None

    ###########################################################################
    # Capture coherent Arduino-side snapshot
    ###########################################################################

    try:

        frame_counter = Bridge.call(
            "capture_snapshot"
        )

        snapshot_counter = Bridge.call(
            "get_snapshot_frame_counter"
        )

    except Exception as e:

        print(
            "[TOF] Snapshot capture error:",
            e
        )

        return None

    ###########################################################################
    # Validate metadata
    ###########################################################################

    if frame_counter == 0:

        log_wait(
            "[TOF] capture_snapshot() returned 0"
        )

        return None

    if (
        snapshot_counter
        !=
        frame_counter
    ):

        print(

            "[TOF] Snapshot frame mismatch",

            "| returned:",

            frame_counter,

            "| snapshot:",

            snapshot_counter

        )

        return None

    ###########################################################################
    # Nothing new
    ###########################################################################

    if (
        frame_counter
        ==
        last_frame_counter
    ):

        return None

    ###########################################################################
    # Read frozen snapshot
    ###########################################################################

    try:

        timestamp = Bridge.call(
            "get_timestamp"
        )

        distance = Bridge.call(
            "get_distance"
        )

        signal = Bridge.call(
            "get_signal"
        )

        sigma = Bridge.call(
            "get_sigma"
        )

        status = Bridge.call(
            "get_status"
        )

        reflectance = Bridge.call(
            "get_reflectance"
        )

        ambient = Bridge.call(
            "get_ambient"
        )

        targets = Bridge.call(
            "get_targets"
        )

        spads = Bridge.call(
            "get_spads"
        )

    except Exception as e:

        print(
            "[TOF] Snapshot read error:",
            e
        )

        return None

    ###########################################################################
    # Validate arrays
    ###########################################################################

    if not validate_snapshot_arrays(

        distance,

        signal,

        sigma,

        status,

        reflectance,

        ambient,

        targets,

        spads

    ):

        return None

    ###########################################################################
    # Convert to 8x8 images
    ###########################################################################

    distance_image = (
        convert_array_to_image(
            distance,
            np.int16
        )
    )

    signal_image = (
        convert_array_to_image(
            signal,
            np.uint32
        )
    )

    sigma_image = (
        convert_array_to_image(
            sigma,
            np.uint16
        )
    )

    status_image = (
        convert_array_to_image(
            status,
            np.uint8
        )
    )

    reflectance_image = (
        convert_array_to_image(
            reflectance,
            np.uint8
        )
    )

    ambient_image = (
        convert_array_to_image(
            ambient,
            np.uint32
        )
    )

    targets_image = (
        convert_array_to_image(
            targets,
            np.uint8
        )
    )

    spads_image = (
        convert_array_to_image(
            spads,
            np.uint32
        )
    )

    ###########################################################################
    # Confidence image
    ###########################################################################

    confidence_image = (
        confidence_engine.calculate_image(

            distance_image,

            signal_image,

            sigma_image,

            status_image,

            reflectance_image,

            ambient_image,

            targets_image,

            spads_image

        )
    )

    ###########################################################################
    # Build frame object
    ###########################################################################

    return ToFFrame(

        frame_number=
            int(
                frame_counter
            ),

        timestamp=
            int(
                timestamp
            ),

        distance=
            distance_image,

        signal=
            signal_image,

        sigma=
            sigma_image,

        status=
            status_image,

        reflectance=
            reflectance_image,

        ambient=
            ambient_image,

        targets=
            targets_image,

        spads=
            spads_image,

        confidence=
            confidence_image

    )


###############################################################################
# Build Sector Observation
###############################################################################

def build_sector_observation(
    frame,
    sector_id,
    start_column,
    end_column
):

    ###########################################################################
    # Sector views
    ###########################################################################

    distance_sector = frame.distance[
        :,
        start_column:end_column
    ]

    confidence_sector = frame.confidence[
        :,
        start_column:end_column
    ]

    ###########################################################################
    # Working distance array
    ###########################################################################

    valid = distance_sector.astype(
        np.int32,
        copy=True
    )

    ###########################################################################
    # Reject unusable zones
    ###########################################################################

    invalid_mask = (

        (
            valid <= 0
        )

        |

        (
            valid > MAX_DISTANCE_MM
        )

        |

        (
            confidence_sector <= 0.0
        )

    )

    valid[
        invalid_mask
    ] = INVALID_DISTANCE_MM

    ###########################################################################
    # Nearest trusted zone
    ###########################################################################

    local_index = int(

        np.argmin(
            valid
        )

    )

    (
        row,
        local_column
    ) = np.unravel_index(

        local_index,

        valid.shape

    )

    distance = int(

        valid[
            row,
            local_column
        ]

    )

    ###########################################################################
    # No trusted obstacle
    ###########################################################################

    if (
        distance
        ==
        INVALID_DISTANCE_MM
    ):

        return SectorObservation(

            sector_id=
                sector_id,

            sector_name=
                SECTOR_NAMES[
                    sector_id
                ],

            distance_mm=
                0

        )

    ###########################################################################
    # Full oriented image column
    ###########################################################################

    column = (

        start_column

        +

        local_column

    )

    ###########################################################################
    # Recover original raw VL53L5CX zone ID
    ###########################################################################

    raw_column = (

        IMAGE_COLS

        -

        1

        -

        column

    )

    zone_id = (

        row

        *

        IMAGE_COLS

        +

        raw_column

    )

    ###########################################################################
    # Build observation using same zone for all signals
    ###########################################################################

    return SectorObservation(

        sector_id=
            sector_id,

        sector_name=
            SECTOR_NAMES[
                sector_id
            ],

        distance_mm=
            distance,

        zone_id=
            int(
                zone_id
            ),

        confidence=
            round(

                float(

                    frame.confidence[
                        row,
                        column
                    ]

                ),

                1

            ),

        signal_kcps_per_spad=
            int(

                frame.signal[
                    row,
                    column
                ]

            ),

        sigma=
            int(

                frame.sigma[
                    row,
                    column
                ]

            ),

        target_status=
            int(

                frame.status[
                    row,
                    column
                ]

            ),

        reflectance=
            int(

                frame.reflectance[
                    row,
                    column
                ]

            ),

        ambient_kcps_per_spad=
            int(

                frame.ambient[
                    row,
                    column
                ]

            ),

        targets=
            int(

                frame.targets[
                    row,
                    column
                ]

            ),

        spads=
            int(

                frame.spads[
                    row,
                    column
                ]

            )

    )


###############################################################################
# Three Logical Sectors
###############################################################################

def build_sector_observations(
    frame
):

    sector_ranges = [

        (
            0,
            2
        ),

        (
            2,
            5
        ),

        (
            5,
            8
        )

    ]

    sectors = []

    for (
        sector_id,
        (
            start_column,
            end_column
        )
    ) in enumerate(
        sector_ranges
    ):

        sectors.append(

            build_sector_observation(

                frame=
                    frame,

                sector_id=
                    sector_id,

                start_column=
                    start_column,

                end_column=
                    end_column

            )

        )

    return sectors


###############################################################################
# Serialization
###############################################################################

def sector_to_dict(
    sector
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
                1
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
                1
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
                sector.receding_persistence

        }

    }


def observation_to_dict(
    observation
):

    return {

        "sensor_id":
            observation.sensor_id,

        "sensor_name":
            observation.sensor_name,

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

        ]

    }


###############################################################################
# Publish Frame
###############################################################################

def publish_frame():

    global last_frame_counter

    global last_timestamp

    global fps

    ###########################################################################
    # Retrieve frame
    ###########################################################################

    frame = read_tof_snapshot()

    if frame is None:

        return

    ###########################################################################
    # FPS
    ###########################################################################

    if last_timestamp is not None:

        dt = (

            frame.timestamp

            -

            last_timestamp

        )

        if dt > 0:

            fps = round(

                1000.0

                /

                dt,

                1

            )

    last_timestamp = (
        frame.timestamp
    )

    last_frame_counter = (
        frame.frame_number
    )

    ###########################################################################
    # Observation Engine
    ###########################################################################

    observation = (
        observation_engine.process_frame(

            frame,

            fps

        )
    )

    ###########################################################################
    # Debug Log
    ###########################################################################

    log_observation(
        observation
    )

    ###########################################################################
    # Dashboard Payload
    ###########################################################################

    message = {

        "app_name":
            APP_NAME,

        "app_version":
            APP_VERSION,

        "image":
            frame.distance.tolist(),

        "confidence_image":
            frame.confidence.tolist(),

        "observation":
            observation_to_dict(
                observation
            )

    }

    ###########################################################################
    # Backward-Compatible Fields
    ###########################################################################

    trusted = frame.distance.astype(
        np.int32,
        copy=True
    )

    invalid = (

        (
            trusted <= 0
        )

        |

        (
            trusted > MAX_DISTANCE_MM
        )

        |

        (
            frame.confidence <= 0.0
        )

    )

    trusted[
        invalid
    ] = INVALID_DISTANCE_MM

    nearest = int(

        np.min(
            trusted
        )

    )

    if (
        nearest
        ==
        INVALID_DISTANCE_MM
    ):

        nearest = 0

    message[
        "frame"
    ] = frame.frame_number

    message[
        "timestamp"
    ] = frame.timestamp

    message[
        "fps"
    ] = fps

    message[
        "nearest"
    ] = nearest

    message[
        "left"
    ] = observation.sectors[
        0
    ].distance_mm

    message[
        "center"
    ] = observation.sectors[
        1
    ].distance_mm

    message[
        "right"
    ] = observation.sectors[
        2
    ].distance_mm

    ###########################################################################
    # Publish
    ###########################################################################

    ui.send_message(

        "tof_frame",

        message

    )


###############################################################################
# Browser Events
###############################################################################

def on_connect(
    client
):

    print(
        "Browser Connected:",
        client
    )


def on_disconnect(
    client
):

    print(
        "Browser Disconnected:",
        client
    )


def get_initial_state(
    client,
    data
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
    "Version       :",
    APP_VERSION
)

print(
    "============================================================"
)

print(
    "Sensor ID     :",
    TOF_SENSOR_ID
)

print(
    "Sensor Name   :",
    TOF_SENSOR_NAME
)

print(
    "Sectors       :",
    TOF_SECTOR_COUNT
)

print(
    "History Size  :",
    TOF_HISTORY_SIZE
)

print(
    "Refresh       :",
    REFRESH_PERIOD,
    "sec"
)

print()

print(
    "Confidence Engine Enabled"
)

print(
    "Velocity Estimation Enabled"
)

print(
    "Velocity Smoothing Enabled"
)

print(
    "Motion Classification Enabled"
)

print(
    "Motion Persistence Engine Enabled"
)

print()

print(
    "Motion Persistence Range :",
    MOTION_PERSISTENCE_MIN,
    "...",
    MOTION_PERSISTENCE_MAX
)

print(
    "Motion Persistence Step  :",
    MOTION_PERSISTENCE_STEP
)

print()

print(
    "Waiting for Arduino Bridge / ToF sensor..."
)

print()


###############################################################################
# Run
###############################################################################

App.run(
    user_loop=loop
)