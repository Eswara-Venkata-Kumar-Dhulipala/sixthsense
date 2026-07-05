# SixthSense v2.0.0

## Software Design Document (SDD)

---

## Document Information

| Item | Value |
|------|-------|
| Project | SixthSense |
| Version | v2.0.0 |
| Document | Software Design Document |
| Status | Approved |
| Date | July 2026 |
| Platform | Arduino UNO Q |
| IDE | Arduino App Lab |

---

# 1. Introduction

SixthSense is a wearable AI-based situational awareness system designed to assist users by continuously monitoring their surroundings using multiple sensors.

The complete system will ultimately consist of:

- Six VL53L5CX Time-of-Flight sensors
- Two USB cameras
- Four vibration motors
- Stereo earbuds
- Arduino UNO Q

Version 2.0.0 focuses exclusively on establishing the first production-quality **ToF Observation Engine**.

No sensor fusion or decision making is performed in this version.

---

# 2. Objectives

Version 2.0.0 shall:

- Read VL53L5CX frames
- Maintain a rolling history buffer
- Divide the depth image into logical sectors
- Compute nearest distance per sector
- Generate structured ToF observations
- Display observations on the dashboard

Version 2.0.0 shall NOT:

- Estimate velocity
- Estimate persistence
- Estimate confidence
- Detect motion
- Perform context reasoning
- Generate vibration
- Generate audio

---

# 3. System Architecture

```

User

▲

Dashboard

▲

ToF Observation Engine

▲

Bridge RPC

▲

Arduino Sketch

▲

VL53L5CX Sensor

```

---

# 4. Project Structure

```

SixthSense/

│

├── docs/

│ ├── SixthSense_v2.0.0.md
│ └── CHANGELOG.md

│

├── sketch/

│ └── sketch.ino

│

├── python/

│ └── main.py

│

└── assets/

├── index.html
├── app.js
├── style.css
└── socket.io.min.js

```

---

# 5. Software Layers

## Layer 1 — Hardware

Responsible for:

- ToF sensor
- Cameras
- Motors
- Earbuds

---

## Layer 2 — Sketch

Responsibilities

- Initialize hardware
- Read sensor data
- Provide Bridge RPC methods

Never performs

- observations
- calculations
- decision making

---

## Layer 3 — Observation Engines

Converts raw sensor data into observations.

Current version implements

- ToF Observation Engine

Future versions implement

- Camera Observation Engine

---

## Layer 4 — Context Engine

Future version.

Consumes observations and generates attention events.

---

## Layer 5 — Output Manager

Future version.

Generates

- vibration
- speech
- spatial audio

---

# 6. Configuration Module

The Configuration Module shall be the first section inside **python/main.py**.

Example parameters:

```

APP_NAME

APP_VERSION

TOF_SENSOR_ID

TOF_SENSOR_NAME

TOF_HISTORY_SIZE

TOF_SECTOR_COUNT

SHOW_HEATMAP

SHOW_JSON

MAX_DISTANCE_MM

INVALID_DISTANCE_MM

REFRESH_PERIOD

```

No configuration values shall exist elsewhere.

---

# 7. ToF Observation Engine

Input

```

Timestamp

Frame Number

8×8 Depth Image

```

Processing

```

Read Frame

↓

Validate Frame

↓

Store History

↓

Divide Into Sectors

↓

Compute Nearest Distance

↓

Generate ToFObservation

↓

Publish Dashboard

```

---

# 8. Frame History

History Buffer Size

```

20 Frames

```

History is stored but not processed in Version 2.0.0.

Future versions will use it for

- velocity
- persistence
- confidence

---

# 9. Sector Definition

Each ToF sensor contains three logical sectors.

```

Sector 0

Sector 1

Sector 2

```

Sector names are intentionally independent of mounting position.

No references to

- front
- rear
- left
- right

exist inside the Observation Engine.

---

# 10. Sector Layout

The 8×8 frame is divided column-wise.

```

Columns

0 1 | 2 3 4 | 5 6 7

Sector 0

Sector 1

Sector 2

```

---

# 11. Distance Calculation

Each sector computes

```

Nearest Valid Distance

```

Rules

- Ignore zero values.
- Replace invalid values using INVALID_DISTANCE_MM.
- Return minimum valid distance.

---

# 12. Data Model

## ToFObservation

```

timestamp

frame_number

sensor_id

sensor_name

status

fps

image

sectors

```

---

## SectorObservation

```

sector_id

distance

```

Only these fields exist in Version 2.0.0.

---

# 13. Dashboard Layout

Dashboard shall contain

```

Application Header

↓

Sensor Information

↓

ToF Observation

↓

Heatmap

↓

Observation JSON

```

---

## Sensor Information

Displays

- Sensor ID
- Sensor Name
- Status
- Frame Number
- Timestamp
- FPS

---

## ToF Observation

Displays

```

Sector 0

Nearest Distance

Sector 1

Nearest Distance

Sector 2

Nearest Distance

```

---

## Heatmap

Displays

Live 8×8 depth image.

---

## Observation JSON

Displays

Current ToFObservation object.

Purpose

- debugging
- validation
- future API verification

---

# 14. Bridge Services

Sketch provides

```

sensor_ready()

get_frame()

get_frame_counter()

get_timestamp()

```

Python consumes only these services.

---

# 15. Data Flow

```

VL53L5CX

↓

Sketch

↓

Bridge

↓

main.py

↓

ToFObservation

↓

Socket.IO

↓

Dashboard

```

---

# 16. Coding Standards

Every module begins with

```

###############################################################################
# Module Name
###############################################################################

```

Maximum nesting depth

```

3

```

Maximum function size

```

50 lines

```

Configuration values belong only inside the Configuration Module.

---

# 17. Testing Checklist

Sensor

- Sensor initializes
- Bridge connects
- Frames received

Observation

- History updated
- Sectors computed
- Distances correct

Dashboard

- Heatmap updates
- Sector cards update
- JSON updates
- FPS updates

Performance

- Stable frame rate
- No memory growth
- Responsive UI

---

# 18. Future Versions

## v2.1.0

Velocity Engine

---

## v2.2.0

Motion Engine

---

## v2.3.0

Persistence Engine

---

## v2.4.0

Confidence Engine

---

## v3.0.0

Camera Observation Engine

---

## v4.0.0

Context Engine

---

## v5.0.0

Output Manager

---

# 19. Design Principles

1. Separation of Responsibilities
2. Sensor Independence
3. Observation Before Decision
4. Configuration Driven
5. Stable Interfaces
6. Incremental Development
7. Dashboard is Visualization Only
8. Backward Compatibility
9. Production-quality Code
10. One Sketch + One Python Script Architecture

---

# 20. Release Status

Version v2.0.0 establishes the software foundation upon which all future SixthSense functionality will be built.

All future releases shall extend this architecture without redesigning the Observation Engine.