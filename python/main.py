# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

import time
import numpy as np

###############################################################################
# Web UI
###############################################################################

ui = WebUI()

print("========================================")
print("SixthSense Python Backend")
print("========================================")
print("Local URL :", ui.local_url)
print("URL       :", ui.url)
print("========================================")

###############################################################################
# Globals
###############################################################################

last_frame_counter = -1
last_timestamp = None
fps = 0.0

###############################################################################
# Browser Events
###############################################################################

def on_connect(client):

    print()
    print("========================================")
    print("Browser Connected")
    print(client)
    print("========================================")

def on_disconnect(client):

    print()
    print("========================================")
    print("Browser Disconnected")
    print(client)
    print("========================================")

###############################################################################
# Initial State
###############################################################################

def get_initial_state(client, data):

    print("Initial state requested.")

    publish_frame()

###############################################################################
# Register Events
###############################################################################

ui.on_connect(on_connect)

ui.on_disconnect(on_disconnect)

ui.on_message(
    "get_initial_state",
    get_initial_state
)

###############################################################################
# Publish Frame
###############################################################################

def publish_frame():

    global last_frame_counter
    global last_timestamp
    global fps

    ###########################################################
    # Sensor Ready?
    ###########################################################

    try:

        ready = Bridge.call("sensor_ready")

    except Exception as e:

        print("Bridge error:", e)

        return

    if not ready:

        return

    ###########################################################
    # Frame Counter
    ###########################################################

    try:

        frame_counter = Bridge.call("get_frame_counter")

    except Exception as e:

        print(e)

        return

    if frame_counter == last_frame_counter:

        return

    last_frame_counter = frame_counter

    ###########################################################
    # Timestamp
    ###########################################################

    timestamp = Bridge.call("get_timestamp")

    ###########################################################
    # FPS
    ###########################################################

    if last_timestamp is not None:

        dt = timestamp - last_timestamp

        if dt > 0:

            fps = round(1000.0 / dt, 1)

    last_timestamp = timestamp

    ###########################################################
    # Read Frame
    ###########################################################

    frame = Bridge.call("get_frame")

    ###########################################################
    # Validate
    ###########################################################

    if len(frame) != 64:

        print("Invalid frame size:", len(frame))

        return

    ###########################################################
    # Convert to numpy
    ###########################################################

    image = np.array(
        frame,
        dtype=np.uint16
    )

    image = image.reshape((8, 8))

    ###########################################################
    # Correct orientation
    ###########################################################

    image = np.fliplr(image)

    ###########################################################
    # Ignore zeros when computing statistics
    ###########################################################

    valid = image.copy()

    valid[valid == 0] = 4000

    nearest = int(np.min(valid))

    left = int(np.min(valid[:, 0:3]))

    center = int(np.min(valid[:, 3:5]))

    right = int(np.min(valid[:, 5:8]))

    ###########################################################
    # Debug
    ###########################################################

    print("------------------------------------------")
    print("Frame      :", frame_counter)
    print("Timestamp  :", timestamp)
    print("FPS        :", fps)
    print("Nearest    :", nearest)
    print("Left       :", left)
    print("Center     :", center)
    print("Right      :", right)
    print("First Row  :", image[0].tolist())

    ###########################################################
    # Send to Dashboard
    ###########################################################

    message = {

        "frame": frame_counter,

        "timestamp": timestamp,

        "fps": fps,

        "nearest": nearest,

        "left": left,

        "center": center,

        "right": right,

        "image": image.tolist()

    }

    ui.send_message(
        "tof_frame",
        message
    )

###############################################################################
# Main Loop
###############################################################################

def loop():

    publish_frame()

    time.sleep(0.02)

###############################################################################
# Run
###############################################################################

App.run(
    user_loop=loop
)