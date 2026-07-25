# SPDX-License-Identifier: MPL-2.0

###############################################################################
#
# SixthSense
#
# Version : 2.1.0
#
# Module  : Python Backend
#
# Platform: Arduino UNO Q
#
# Purpose :
#
#   • Read ToF frames from Arduino Bridge
#   • Maintain frame history
#   • Generate ToF Observations
#   • Publish observations to Web Dashboard
#
# NOTE
#
#Version 2.1.0 introduces Temporal Observation.
#
#Implemented
#
#• Observation History
#• Velocity Estimation
#• Velocity Smoothing
#• Enhanced Dashboard
#
#Not Implemented
#
#• Persistence
#• Confidence
#• Context Engine
#• Attention Engine
#• Feedback Engine
#
###############################################################################

from dataclasses import dataclass, asdict
from collections import deque

import time
import numpy as np

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

###############################################################################
# Configuration
###############################################################################

APP_NAME = "SixthSense"

APP_VERSION = "2.1.0"

###############################################################################
# Sensor Configuration
###############################################################################

TOF_SENSOR_ID = "tof_01"

TOF_SENSOR_NAME = "Prototype ToF"

###############################################################################
# Observation Configuration
###############################################################################

#
# Number of observations stored in history
#

TOF_HISTORY_SIZE = 20

#
# Number of logical sectors
#

TOF_SECTOR_COUNT = 3

###############################################################################
# Temporal Observation Configuration (v2.1.0)
###############################################################################

#
# Number of velocity samples used for smoothing
#

VELOCITY_WINDOW = 5

#
# Minimum valid time difference (seconds)
#

MIN_VALID_DT = 0.02

#
# Velocity classification threshold (mm/s)
#

STATIONARY_THRESHOLD = 50.0

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
# Sector Configuration
###############################################################################

SECTOR_NAMES = [

    "Sector 0",

    "Sector 1",

    "Sector 2"

]

###############################################################################
# Image Configuration
###############################################################################

IMAGE_ROWS = 8

IMAGE_COLS = 8

###############################################################################
# Web UI
###############################################################################

ui = WebUI()

print()

print("============================================================")

print(APP_NAME)

print("Version :", APP_VERSION)

print("============================================================")

print("Local URL :", ui.local_url)

print("URL       :", ui.url)

print("============================================================")

###############################################################################
# Data Models
###############################################################################

@dataclass
class ToFFrame:
    """
    Raw frame received from Arduino.
    """

    frame_number: int

    timestamp: int

    image: np.ndarray


@dataclass
class SectorObservation:
    """
    Observation for one logical sector.
    """

    sector_id: int

    sector_name: str

    #
    # Current nearest obstacle
    #

    distance_mm: int

    #
    # Estimated velocity
    #
    # Positive -> Moving Away
    # Negative -> Approaching
    #

    velocity_mmps: float = 0.0

    #
    # Reserved for v2.2.0
    #

    persistence: float = 0.0


@dataclass
class ToFObservation:
    """
    Complete observation generated from one ToF sensor.
    """

    sensor_id: str

    sensor_name: str

    status: str

    frame_number: int

    timestamp: int

    fps: float

    sectors: list

    #
    # Number of observations currently
    # stored inside the Observation Engine.
    #

    history_size: int = 0

###############################################################################
# Global State
###############################################################################

last_frame_counter = -1

last_timestamp = None

fps = 0.0

###############################################################################
# Velocity History
###############################################################################

velocity_history = {

    0: deque(maxlen=VELOCITY_WINDOW),

    1: deque(maxlen=VELOCITY_WINDOW),

    2: deque(maxlen=VELOCITY_WINDOW)

}

###############################################################################
# Observation Engine
###############################################################################

class ObservationEngine:
    """
    Observation Engine for one Time-of-Flight sensor.

    Responsibilities
    ----------------
    • Build observations
    • Maintain observation history
    • Maintain velocity history
    • Estimate sector velocities
    • Produce enhanced ToF observations
    """

    def __init__(self):

        self.observation_history = deque(
            maxlen=TOF_HISTORY_SIZE
        )

        self.velocity_history = {

            0: deque(maxlen=VELOCITY_WINDOW),

            1: deque(maxlen=VELOCITY_WINDOW),

            2: deque(maxlen=VELOCITY_WINDOW)

        }

    ###########################################################################
    # Public API
    ###########################################################################

    def process_frame(
        self,
        frame_number,
        timestamp,
        fps,
        image
    ):
        """
        Process one ToF frame.
        """

        observation = self._build_observation(

            frame_number,

            timestamp,

            fps,

            image

        )

        self._estimate_velocity(
            observation
        )

        self._filter_velocity(
            observation
        )

        self._update_history(
            observation
        )

        observation.history_size = len(
            self.observation_history
        )

        return observation

    ###########################################################################
    # Observation History
    ###########################################################################

    def _update_history(
        self,
        observation
    ):

        self.observation_history.append(
            observation
        )

    def previous_observation(self):

        if len(self.observation_history) == 0:

            return None

        return self.observation_history[-1]

    ###########################################################################
    # Observation Builder
    ###########################################################################

    def _build_observation(

        self,

        frame_number,

        timestamp,

        fps,

        image

    ):

        sectors = build_sector_observations(
            image
        )

        observation = ToFObservation(

            sensor_id=TOF_SENSOR_ID,

            sensor_name=TOF_SENSOR_NAME,

            status="ONLINE",

            frame_number=frame_number,

            timestamp=timestamp,

            fps=fps,

            sectors=sectors

        )

        return observation

    ###########################################################################
    # Placeholders
    #
    # Implemented in Part 3
    ###########################################################################

    ###########################################################################
    # Velocity Estimation
    ###########################################################################

    def _estimate_velocity(
        self,
        observation
    ):
        """
        Estimate sector-wise velocity using the previous observation.
        """

        previous = self.previous_observation()

        #
        # First observation
        #

        if previous is None:

            for sector in observation.sectors:

                sector.velocity_mmps = 0.0

            return

        #
        # Time difference
        #

        dt = (

            observation.timestamp
            - previous.timestamp

        ) / 1000.0

        if dt < MIN_VALID_DT:

            dt = MIN_VALID_DT

        #
        # Compute velocity for every sector
        #

        for current_sector, previous_sector in zip(

            observation.sectors,

            previous.sectors

        ):

            current_distance = current_sector.distance_mm

            previous_distance = previous_sector.distance_mm

            #
            # Ignore invalid measurements
            #

            if current_distance == 0 or previous_distance == 0:

                velocity = 0.0

            else:

                #
                # Positive  -> Moving Away
                # Negative  -> Approaching
                #

                velocity = (

                    current_distance
                    - previous_distance

                ) / dt

            current_sector.velocity_mmps = velocity

            self.velocity_history[
                current_sector.sector_id
            ].append(
                velocity
            )

    ###########################################################################
    # Velocity Filter
    ###########################################################################

    def _filter_velocity(
        self,
        observation
    ):
        """
        Apply moving-average smoothing to the estimated velocity.
        """

        for sector in observation.sectors:

            history = self.velocity_history[
                sector.sector_id
            ]

            if len(history) == 0:

                continue

            sector.velocity_mmps = round(

                sum(history)

                /

                len(history),

                1

            )


###############################################################################
# Observation Engine Instance
###############################################################################

observation_engine = ObservationEngine()

###############################################################################
# Browser Events
###############################################################################

def on_connect(client):

    print()

    print("============================================================")

    print("Browser Connected")

    print(client)

    print("============================================================")


def on_disconnect(client):

    print()

    print("============================================================")

    print("Browser Disconnected")

    print(client)

    print("============================================================")


###############################################################################
# Initial State
###############################################################################

def get_initial_state(client, data):

    print()

    print("Initial state requested.")

    publish_frame()

###############################################################################
# Register Browser Events
###############################################################################

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
# Helper Functions
###############################################################################

def log_separator():

    print("------------------------------------------------------------")


def log_header(title):

    print()

    print("============================================================")

    print(title)

    print("============================================================")

###############################################################################
# Image Processing
###############################################################################

def convert_frame_to_image(frame):

    """
    Convert the raw Bridge frame into an 8×8 NumPy array.
    """

    image = np.array(
        frame,
        dtype=np.uint16
    )

    image = image.reshape(
        (
            IMAGE_ROWS,
            IMAGE_COLS
        )
    )

    #
    # Correct sensor orientation
    #

    image = np.fliplr(image)

    return image


###############################################################################
# Sector Processing
###############################################################################

def compute_sector_distance(image,
                            start_column,
                            end_column):

    """
    Compute the nearest valid distance
    inside one logical sector.

    end_column follows Python slicing.
    """

    sector = image[:, start_column:end_column]

    valid = sector.copy()

    valid[valid == 0] = INVALID_DISTANCE_MM

    distance = int(np.min(valid))

    if distance == INVALID_DISTANCE_MM:

        distance = 0

    return distance


###############################################################################
# Observation Engine
###############################################################################

def build_sector_observations(image):

    """
    Divide the 8×8 image into three sectors.

    Columns

    0 1 | 2 3 4 | 5 6 7
    """

    sectors = []

    sectors.append(

        SectorObservation(

            sector_id=0,

            sector_name=SECTOR_NAMES[0],

            distance_mm=compute_sector_distance(
                image,
                0,
                2
            )

        )

    )

    sectors.append(

        SectorObservation(

            sector_id=1,

            sector_name=SECTOR_NAMES[1],

            distance_mm=compute_sector_distance(
                image,
                2,
                5
            )

        )

    )

    sectors.append(

        SectorObservation(

            sector_id=2,

            sector_name=SECTOR_NAMES[2],

            distance_mm=compute_sector_distance(
                image,
                5,
                8
            )

        )

    )

    return sectors

###############################################################################
# Debug Logging
###############################################################################

def log_observation(observation):

    log_separator()

    print("Frame       :", observation.frame_number)

    print("Timestamp   :", observation.timestamp)

    print("FPS         :", observation.fps)

    print("History     :", observation.history_size)

    print()

    for sector in observation.sectors:

        if sector.velocity_mmps < -STATIONARY_THRESHOLD:

            state = "Approaching"

        elif sector.velocity_mmps > STATIONARY_THRESHOLD:

            state = "Receding"

        else:

            state = "Stationary"

        print(

            sector.sector_name,

            ":",

            sector.distance_mm,

            "mm",

            "|",

            round(
                sector.velocity_mmps,
                1
            ),

            "mm/s",

            "|",

            state

        )

    log_separator()

###############################################################################
# Dashboard Helpers
###############################################################################

def velocity_state(velocity):
    """
    Classify velocity for dashboard visualization.
    """

    if velocity < -STATIONARY_THRESHOLD:

        return "Approaching"

    elif velocity > STATIONARY_THRESHOLD:

        return "Receding"

    else:

        return "Stationary"


###############################################################################
# Dashboard Serialization
###############################################################################

def sector_to_dict(sector):
    """
    Convert one SectorObservation into a JSON serializable dictionary.
    """

    return {

        "sector_id": sector.sector_id,

        "sector_name": sector.sector_name,

        "distance_mm": sector.distance_mm,

        "velocity_mmps": round(
            sector.velocity_mmps,
            1
        ),

        "velocity_state": velocity_state(
            sector.velocity_mmps
        ),

        "persistence": sector.persistence

    }


def observation_to_dict(observation):
    """
    Convert ToFObservation into a JSON serializable dictionary.
    """

    return {

        "sensor_id": observation.sensor_id,

        "sensor_name": observation.sensor_name,

        "status": observation.status,

        "frame_number": observation.frame_number,

        "timestamp": observation.timestamp,

        "fps": observation.fps,

        "history_size": observation.history_size,

        "sectors": [

            sector_to_dict(sector)

            for sector in observation.sectors

        ]

    }

###############################################################################
# Observation Engine
###############################################################################

def publish_frame():

    global last_frame_counter
    global last_timestamp
    global fps

    ###########################################################################
    # Sensor Ready?
    ###########################################################################

    try:

        ready = Bridge.call("sensor_ready")

        print("[DEBUG] sensor_ready =", ready)

    except Exception as e:

        print("[DEBUG] Bridge exception:", e)

        return

    if not ready:

        print("[DEBUG] Sensor not ready")

        return

    ###########################################################################
    # Frame Counter
    ###########################################################################

    try:

        frame_counter = Bridge.call(
            "get_frame_counter"
        )
        print("[DEBUG] frame_counter =", frame_counter)

    except Exception as e:

        print(e)

        return

    #
    # Nothing new?
    #

    if frame_counter == last_frame_counter:

        return

    last_frame_counter = frame_counter

    ###########################################################################
    # Timestamp
    ###########################################################################

    timestamp = Bridge.call(
        "get_timestamp"
    )

    ###########################################################################
    # FPS
    ###########################################################################

    if last_timestamp is not None:

        dt = timestamp - last_timestamp

        if dt > 0:

            fps = round(
                1000.0 / dt,
                1
            )

    last_timestamp = timestamp

    ###########################################################################
    # Read ToF Frame
    ###########################################################################

    frame = Bridge.call(
        "get_frame"
    )
    print("[DEBUG] frame length =", len(frame))

    ###########################################################################
    # Validate
    ###########################################################################

    if len(frame) != 64:

        print(
            "Invalid frame size:",
            len(frame)
        )

        return

    ###########################################################################
    # Convert To Image
    ###########################################################################

    image = convert_frame_to_image(
        frame
    )

    ###########################################################################
    # Observation Engine
    ###########################################################################

    observation = observation_engine.process_frame(

        frame_counter,

        timestamp,

        fps,

        image

    )

    ###########################################################################
    # Debug Log
    ###########################################################################

    log_observation(
        observation
    )

    ###########################################################################
    # Dashboard Message
    ###########################################################################

    message = {

        #
        # Metadata
        #

        "app_name": APP_NAME,

        "app_version": APP_VERSION,

        #
        # Raw image
        #

        "image": image.tolist(),

        #
        # Observation
        #

        "observation": observation_to_dict(
            observation
        )

    }

    ###########################################################################
    # Backward Compatibility
    #
    # Existing dashboard continues to work until
    # the new dashboard (v2.0.0.2) is introduced.
    ###########################################################################

    valid = image.copy()

    valid[valid == 0] = INVALID_DISTANCE_MM

    message["frame"] = frame_counter

    message["timestamp"] = timestamp

    message["fps"] = fps

    message["nearest"] = int(
        np.min(valid)
    )

    message["left"] = observation.sectors[0].distance_mm

    message["center"] = observation.sectors[1].distance_mm

    message["right"] = observation.sectors[2].distance_mm

    ###########################################################################
    # Publish
    ###########################################################################

    ui.send_message(

        "tof_frame",

        message

    )
###############################################################################
# Main Loop
###############################################################################

def loop():

    """
    Main application loop.

    Responsibilities
    ----------------
    1. Read latest ToF frame (if available)
    2. Update Observation Engine
    3. Publish observation to dashboard
    """
    print("[DEBUG] loop")

    publish_frame()

    time.sleep(
        REFRESH_PERIOD
    )

###############################################################################
# Startup Information
###############################################################################

log_header("Application Configuration")

print("Application")

print("  Name          :", APP_NAME)

print("  Version       :", APP_VERSION)

print()

print("Sensor")

print("  ID            :", TOF_SENSOR_ID)

print("  Name          :", TOF_SENSOR_NAME)

print("  Sectors       :", TOF_SECTOR_COUNT)

print("  History Size  :", TOF_HISTORY_SIZE)

print()

print("Dashboard")

print("  Heatmap       :", SHOW_HEATMAP)

print("  JSON          :", SHOW_JSON)

print("  Refresh       :", REFRESH_PERIOD, "sec")

print()

print("Distance")

print("  Max           :", MAX_DISTANCE_MM, "mm")

print("  Invalid       :", INVALID_DISTANCE_MM, "mm")

print()

print("Waiting for ToF sensor...")

print()

print("Temporal Observation Engine Enabled")

print("Velocity Estimation Enabled")

print("Velocity Smoothing Enabled")

print()

print("Waiting for sensor...")

print()

###############################################################################
# Run Application
###############################################################################

App.run(

    user_loop=loop

)

###############################################################################
#
# End of File
#
# SixthSense v2.1.0
#
###############################################################################