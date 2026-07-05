# SixthSense

## AI-Powered Wearable Situational Awareness System

---

## Overview

SixthSense is an AI-powered wearable system designed to improve environmental awareness using multiple complementary sensors.

The system continuously observes the surrounding environment, converts raw sensor data into structured observations, reasons about those observations, and finally provides intuitive feedback to the user through vibration motors and spatial audio.

The project is being developed using **Arduino UNO Q** and **Arduino App Lab**.

---

<img width="1908" height="1020" alt="Recording2026-07-05213314-ezgif com-optimize" src="https://github.com/user-attachments/assets/42befc3f-f4d0-4fa3-bc91-eb6e460240fd" />
<img width="1917" height="965" alt="image" src="https://github.com/user-attachments/assets/fce2f555-09e5-4eb5-9e6d-0a301e34e8b3" />
<img width="1915" height="967" alt="image" src="https://github.com/user-attachments/assets/57b406a6-8333-460b-83b8-1a2038379d49" />
<img width="1915" height="972" alt="image" src="https://github.com/user-attachments/assets/e8450085-320f-423b-b244-3983818326e9" />
<img width="1916" height="966" alt="image" src="https://github.com/user-attachments/assets/b3835375-dd2b-4285-bd75-3034f1347426" />
<img width="1916" height="962" alt="image" src="https://github.com/user-attachments/assets/fae086e5-fc32-4815-95cf-5c2ab39710f8" />

---

# Project Vision

The final system aims to provide near 360° situational awareness using

- 6 × VL53L5CX Time-of-Flight Sensors
- 2 × USB Cameras
- 4 × Vibration Motors
- Stereo Earbuds
- Arduino UNO Q

Rather than relying on a single sensing modality, SixthSense combines geometric perception and semantic perception through a layered software architecture.

---

## Hardware used for v2.0.0
- 1 × VL53L5CX Time-of-Flight Sensors
- Arduino UNO Q
- Qwiic Cable With 1mm JST Connector
<img width="960" height="1280" alt="WhatsApp Image 2026-07-05 at 21 59 37" src="https://github.com/user-attachments/assets/4968e3f6-217f-41ab-af97-992710e7f006" />


---

## Software Stack
Arduino App Lab

Arduino UNO Q

Python

JavaScript

HTML

CSS

SparkFun VL53L5CX Library

---

# Development Philosophy

The software is developed incrementally.

Instead of building the complete system immediately, each release introduces one well-tested capability.

Current development order

```

ToF Observation Engine

↓

Camera Observation Engine

↓

Context Engine

↓

Output Manager

```

---

# Current Version

```

Version

v2.0.0

Status

Stable Observation Engine

```

Implemented

- Working VL53L5CX integration
- Working Arduino Bridge
- Working Python backend
- Working Web Dashboard
- Working Heatmap
- ToF Observation Engine

---

# Software Architecture

```
Sketch

↓

Bridge RPC

↓

Observation Engines

↓

Context Engine

↓

Attention Engine

↓

Output Manager

↓

Dashboard

```

---

# Repository Structure

```

SixthSense

│

├── docs/

│ ├── README.md
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
└── libs/
    └── socket.io.min.js

```

---

# Current Milestone

Version 2.0.0 establishes the complete infrastructure for the ToF Observation Engine.

Features

- Read ToF frames
- Divide frame into sectors
- Generate observations
- Display observations on dashboard

---

# Planned Roadmap

## v2.1.0

Velocity Estimation

---

## v2.2.0

Approach / Recede Classification

---

## v2.3.0

Persistence Estimation

---

## v2.4.0

Confidence Estimation

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

# Design Principles

The project follows the following principles.

- Separation of Responsibilities
- Observation Before Decision
- Sensor Independence
- Configuration Driven
- Stable Interfaces
- Incremental Development
- Production-quality Architecture
- One Sketch + One Python Script Constraint

---

# License

MPL-2.0
