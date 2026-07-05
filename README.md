# SixthSense

## AI-Powered Wearable Situational Awareness System

---

## Overview

SixthSense is an AI-powered wearable system designed to improve environmental awareness using multiple complementary sensors.

The system continuously observes the surrounding environment, converts raw sensor data into structured observations, reasons about those observations, and finally provides intuitive feedback to the user through vibration motors and spatial audio.

The project is being developed using **Arduino UNO Q** and **Arduino App Lab**.

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

In Development

```

Implemented

- Working VL53L5CX integration
- Working Arduino Bridge
- Working Python backend
- Working Web Dashboard
- Working Heatmap

Currently under development

- ToF Observation Engine

---

# Software Architecture

```

Sensors

↓

Sketch (Hardware Layer)

↓

Bridge RPC

↓

Python (Observation Engines)

↓

Context Engine

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
└── socket.io.min.js

```

---

# Current Milestone

Version 2.0.0 establishes the complete infrastructure for the ToF Observation Engine.

Features

- Read ToF frames
- Maintain history
- Divide frame into sectors
- Generate observations
- Display observations on dashboard

---

# Planned Roadmap

## v2.0.0

ToF Observation Engine

---

## v2.1.0

Velocity Estimation

---

## v2.2.0

Motion Classification

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

# Documentation

The project documentation consists of three documents.

README.md

Current project overview.

SixthSense_vX.Y.Z.md

Detailed Software Design Document for a specific version.

CHANGELOG.md

History of changes across all versions.

---

# License

MPL-2.0