# SPDX-License-Identifier: MPL-2.0

###############################################################################
#
# SixthSense
#
# Version : 2.0.0.1
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
# Version 2.0.0.1 introduces the Observation Infrastructure only.
#
# NOT IMPLEMENTED
#
#   • Velocity
#   • Motion
#   • Persistence
#   • Confidence
#   • Context Engine
#   • Camera Observation
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

APP_VERSION = "2.0.0.1"

###############################################################################
# Sensor Configuration
###############################################################################

TOF_SENSOR_ID = "tof_01"

TOF_SENSOR_NAME = "Prototype ToF"

###############################################################################
# Observation Configuration
###############################################################################

TOF_HISTORY_SIZE = 20

TOF_SECTOR_COUNT = 3

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

    distance: int


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

###############################################################################
# Global State
###############################################################################

last_frame_counter = -1

last_timestamp = None

fps = 0.0

###############################################################################
# Rolling History Buffer
###############################################################################

frame_history = deque(
    maxlen=TOF_HISTORY_SIZE
)

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
# Frame History
###############################################################################

def add_frame_to_history(frame):

    """
    Store the latest frame in the rolling history buffer.
    """

    frame_history.append(frame)


def history_size():

    return len(frame_history)


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

            distance=compute_sector_distance(
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

            distance=compute_sector_distance(
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

            distance=compute_sector_distance(
                image,
                5,
                8
            )

        )

    )

    return sectors


###############################################################################
# ToF Observation Builder
###############################################################################

def build_observation(frame_number,
                      timestamp,
                      fps,
                      image):

    """
    Generate the ToFObservation object.
    """

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


###############################################################################
# Debug Logging
###############################################################################

def log_observation(observation):

    log_separator()

    print("Frame       :", observation.frame_number)

    print("Timestamp   :", observation.timestamp)

    print("FPS         :", observation.fps)

    print("History     :", history_size())

    print()

    for sector in observation.sectors:

        print(

            sector.sector_name,

            ":",

            sector.distance,

            "mm"

        )

    log_separator()


###############################################################################
# Dashboard Serialization
###############################################################################

def observation_to_dict(observation):

    """
    Convert dataclasses into JSON serializable dictionaries.
    """

    data = asdict(observation)

    return data
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

    except Exception as e:

        print("Bridge error:", e)

        return

    if not ready:

        return

    ###########################################################################
    # Frame Counter
    ###########################################################################

    try:

        frame_counter = Bridge.call(
            "get_frame_counter"
        )

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
    # Save History
    ###########################################################################

    current_frame = ToFFrame(

        frame_number=frame_counter,

        timestamp=timestamp,

        image=image.copy()

    )

    add_frame_to_history(
        current_frame
    )

    ###########################################################################
    # Build Observation
    ###########################################################################

    observation = build_observation(

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

    message["left"] = compute_sector_distance(
        image,
        0,
        3
    )

    message["center"] = compute_sector_distance(
        image,
        3,
        5
    )

    message["right"] = compute_sector_distance(
        image,
        5,
        8
    )

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
# SixthSense v2.0.0.1
#
###############################################################################
