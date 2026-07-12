# SixthSense

# AI-Powered Wearable Situational Awareness System

> **An Observation-First wearable system that transforms Time-of-Flight sensor measurements into structured observations for intelligent situational awareness.**

---

<div align="center">

![License](https://img.shields.io/badge/License-MPL--2.0-green)

![Arduino](https://img.shields.io/badge/Arduino-UNO%20Q-00979D)

![Python](https://img.shields.io/badge/Python-3.x-blue)

![Latest Release](https://img.shields.io/badge/Release-v2.0.0-success)

![Development](https://img.shields.io/badge/Development-v2.1.0-orange)

</div>

---

# Overview

SixthSense is an AI-powered wearable situational awareness system being developed to assist visually impaired individuals.

Unlike traditional obstacle detection systems, SixthSense does **not** directly convert sensor measurements into vibration or audio feedback.

Instead, raw Time-of-Flight measurements are first converted into structured **observations**. These observations provide a stable interface for higher-level reasoning modules, allowing the system to understand the surrounding environment before deciding what information should be communicated to the user.

This **Observation-First Architecture** separates sensing from reasoning, allowing the software to evolve incrementally while maintaining clean interfaces between architectural layers.

The current prototype is built using:

- Arduino UNO Q
- Arduino App Lab
- SparkFun VL53L5CX Time-of-Flight Sensor
- Python Backend
- HTML / CSS / JavaScript Dashboard

---

# Current Status

| Branch | Purpose | Version |
|----------|---------|----------|
| **main** | Latest Stable Release | **v2.0.0** |
| **develop** | Active Development | **v2.1.0** |

### Latest Stable Release

**SixthSense v2.0.0**

**First Stable ToF Observation Engine**

### Current Development

**SixthSense v2.1.0**

**Temporal ToF Observation Engine**

---

# Demonstration

The current implementation provides a real-time dashboard for visualizing observations generated from the VL53L5CX Time-of-Flight sensor.

Current capabilities include:

- Live 8×8 ToF Heatmap
- Three-Sector Observation Model
- Live Observation Generation
- JSON Observation Viewer
- Arduino Bridge Monitoring
- Browser Connection Monitoring
- Sensor Status Monitoring

---

<!-- Keep your GIFs exactly as they are -->

<img width="1908" height="1020" alt="Recording2026-07-05213314-ezgif com-optimize" src="https://github.com/user-attachments/assets/42befc3f-f4d0-4fa3-bc91-eb6e460240fd" />

<img width="1917" height="965" alt="image" src="https://github.com/user-attachments/assets/fce2f555-09e5-4eb5-9e6d-0a301e34e8b3" />

<img width="1915" height="967" alt="image" src="https://github.com/user-attachments/assets/57b406a6-8333-460b-83b8-1a2038379d49" />

<img width="1915" height="972" alt="image" src="https://github.com/user-attachments/assets/e8450085-320f-423b-b244-3983818326e9" />

<img width="1916" height="966" alt="image" src="https://github.com/user-attachments/assets/b3835375-dd2b-4285-bd75-3034f1347426" />

<img width="1916" height="962" alt="image" src="https://github.com/user-attachments/assets/fae086e5-fc32-4815-95cf-5c2ab39710f8" />

---

# Project Vision

The long-term vision of SixthSense is to build an intelligent wearable system capable of providing near **360° situational awareness** using multiple Time-of-Flight sensors.

The planned prototype consists of:

- 6 × VL53L5CX Time-of-Flight Sensors
- Arduino UNO Q
- Vibration Motors
- Stereo Earbuds

Each Time-of-Flight sensor independently observes a region of the surrounding environment and generates a structured observation.

Future architectural layers will consume these observations to understand the user's surroundings, prioritize important events and generate intuitive audio and haptic feedback.

The objective is not simply obstacle detection.

The objective is intelligent situational awareness.

---

# Why Observation-First?

Traditional obstacle detection systems typically follow a direct processing pipeline.

```text
Sensor

↓

Threshold

↓

Motor / Speaker

↓

User
```

Although simple, this tightly couples sensing with user feedback, making the software difficult to extend as additional sensors and reasoning capabilities are introduced.

SixthSense instead follows an Observation-First Architecture.

```text
Sensor

↓

Observation Engine (Generates ToFObservation)

↓

Context Engine

↓

Attention Engine

↓

Feedback Engine

↓

User
```

Each architectural layer has a single responsibility.

| Layer | Responsibility |
|--------|----------------|
| Observation Engine | Generate observations |
| Context Engine | Understand the environment |
| Attention Engine | Prioritize important events |
| Feedback Engine | Generate user feedback |

This separation allows sensing, reasoning and user interaction to evolve independently while maintaining stable interfaces between architectural layers.

---

# Current Prototype

The current prototype focuses on validating the complete **ToF Observation Engine** using a single **VL53L5CX Time-of-Flight sensor**.

Rather than attempting to build the complete wearable system immediately, SixthSense is being developed incrementally.

Each release introduces one well-defined capability while preserving stable interfaces for future development.

The current implementation includes:

- Single VL53L5CX Time-of-Flight Sensor
- Arduino UNO Q
- Arduino Bridge RPC
- ToF Observation Engine
- Interactive Web Dashboard
- Observation API

The primary objective of the current prototype is to validate the Observation Engine before scaling to a six-sensor wearable prototype.

---

# Hardware

## Current Hardware (v2.0.0)

| Component | Quantity |
|-----------|---------:|
| Arduino UNO Q | 1 |
| SparkFun VL53L5CX Time-of-Flight Sensor | 1 |
| Qwiic JST Cable | 1 |
| USB-C Cable | 1 |

---

## Prototype Hardware

<img width="960" height="1280" alt="Arduino UNO Q with VL53L5CX" src="https://github.com/user-attachments/assets/4968e3f6-217f-41ab-af97-992710e7f006" />

The current prototype validates the complete Observation Engine using a single Time-of-Flight sensor.

Future releases will extend the same Observation Engine architecture to six independent Time-of-Flight sensors.

The Observation Engine design remains unchanged when additional sensors are introduced.

Each additional Time-of-Flight sensor runs an independent instance of the Observation Engine and produces its own `ToFObservation`.

---

# Software Stack

| Layer | Technology |
|--------|------------|
| Development Environment | Arduino App Lab |
| Firmware | Arduino Sketch (C++) |
| Backend | Python |
| Frontend | HTML |
| Styling | CSS |
| Dashboard | JavaScript |
| Communication | Arduino Bridge RPC |
| Web Interface | Arduino App Lab WebUI |

---

# Development Philosophy

SixthSense follows an incremental engineering approach.

Instead of building the complete wearable system in a single step, each release introduces one architectural capability while preserving compatibility with previous releases.

```
v2.0.0

Static ToF Observation

        │

        ▼

v2.1.0

Temporal ToF Observation

        │

        ▼

v2.2.0

Persistent ToF Observation

        │

        ▼

v3.0.0

Six-ToF Sensor Integration

        │

        ▼

v4.0.0

Context Engine

        │

        ▼

v5.0.0

Attention Engine

        │

        ▼

v6.0.0

Feedback Engine

        │

        ▼

v7.0.0

Complete SixthSense Prototype
```

Each milestone introduces one major capability.

This approach keeps the software modular, minimizes technical debt and allows every architectural layer to be independently designed, implemented and validated before the next layer is introduced.

---

# Current Release

| Property | Value |
|----------|-------|
| Version | **v2.0.0** |
| Release Name | **First Stable ToF Observation Engine** |
| Status | **Stable** |

## Implemented Features

- VL53L5CX Sensor Integration
- Arduino Bridge Communication
- ToF Observation Engine
- Interactive Web Dashboard
- Live 8×8 Distance Heatmap
- Three-Sector Observation Model
- Observation API
- Versioned Documentation
- GitHub Release

---

# Current Development

| Property | Value |
|----------|-------|
| Branch | **develop** |
| Target Version | **v2.1.0** |
| Milestone | **Temporal ToF Observation Engine** |
| Status | **In Development** |

## Planned Features

- Observation History
- Sector-wise Velocity Estimation
- Velocity History
- Velocity Filtering
- Enhanced ToFObservation
- Dashboard Velocity Visualization

The objective of **v2.1.0** is to transform the Observation Engine from a static sensing layer into a temporal sensing layer.

Subsequent releases will continue strengthening the Observation Engine before introducing higher-level architectural layers such as the Context Engine, Attention Engine and Feedback Engine.

---

# Software Architecture

The current SixthSense prototype follows a layered **Observation-First Architecture**.

Each architectural layer has a single responsibility.

```text
                 SixthSense

      AI-Powered Situational Awareness System


      VL53L5CX Time-of-Flight Sensor
                  │
                  ▼
         Arduino UNO Q Sketch
                  │
                  ▼
           Arduino Bridge RPC
                  │
                  ▼
          ToF Observation Engine
                  │
                  ▼
         Enhanced ToFObservation
                  │
                  ▼
            Web Dashboard
```

The current prototype separates:

- Sensor acquisition
- Observation generation
- Dashboard visualization

This separation allows each layer to evolve independently while maintaining stable interfaces.

---

# ToF Observation Engine

The ToF Observation Engine is the core software component of the current prototype.

Its responsibility is to convert raw Time-of-Flight measurements into structured observations.

The Observation Engine **does not make decisions**.

It only describes what the sensor observes.

```text
Raw 8×8 ToF Frame
        │
        ▼
Observation Builder
        │
        ▼
ToFObservation
        │
        ├──────────────► Observation History
        │
        ▼
Velocity Estimator
        │
        ├──────────────► Velocity History
        │
        ▼
Velocity Filter
        │
        ▼
Enhanced ToFObservation
        │
        ▼
Dashboard
```

Notice that both **Observation History** and **Velocity History** are persistent data stores used by the Observation Engine rather than sequential processing stages.

---

# Observation Builder

The Observation Builder converts a raw **8×8 Time-of-Flight frame** into a structured observation.

Current responsibilities include:

- Read the raw ToF frame
- Validate distance measurements
- Divide the frame into logical sectors
- Determine the nearest obstacle within each sector
- Construct a `ToFObservation`

The Observation Builder performs **measurement processing**, not environment understanding.

Its output is an objective description of what the sensor currently observes.

---

# ToFObservation

`ToFObservation` is the primary data model produced by the Observation Engine.

It represents the complete state of the sensor at a specific instant.

```text
ToFObservation

├── Timestamp

├── Frame Number

├── Sensor Information

└── Sector Observations

      ├── Left Sector

      ├── Center Sector

      └── Right Sector
```

Version **v2.0.0** includes distance information.

Version **v2.1.0** extends the same observation with temporal information.

---

# Observation History

The Observation Engine maintains a fixed-capacity rolling buffer of previously generated `ToFObservation` objects.

```text
Newest Observation

↓

Observation

↓

Observation

↓

Observation

↓

...

↓

Oldest Observation
```

The Observation History enables temporal reasoning while keeping the Observation Builder stateless.

Current usage:

- Velocity estimation

Future usage:

- Persistence estimation

The Observation History stores observations only.

It does **not** interpret them.

---

# Velocity Estimation

Version **v2.1.0** introduces temporal reasoning by estimating how the surrounding environment changes over time.

Velocity estimation combines the current observation with information stored in the Observation History.

```text
Current Observation
        │
        │
        ├──────────────► Observation History
        │
        ▼
Velocity Estimator
        │
        ├──────────────► Velocity History
        │
        ▼
Velocity Filter
        │
        ▼
Enhanced ToFObservation
```

Velocity is computed independently for each logical sector.

This allows the dashboard to indicate whether objects are approaching, stationary or moving away.

---

# Enhanced ToFObservation

After temporal processing, the Observation Engine produces an enhanced observation.

```text
Enhanced ToFObservation

├── Timestamp

├── Frame Information

├── Sensor Information

└── Sector Observations

      ├── Distance

      ├── Velocity

      └── (Future) Persistence
```

Future architectural layers will consume these enhanced observations without requiring direct access to raw sensor measurements.

---

# Dashboard

The current dashboard visualizes the generated observations in real time.

Current features include:

- Live 8×8 Distance Heatmap
- Three-Sector Distance Display
- JSON Observation Viewer
- System Status
- Frame Counter
- FPS

Version **v2.1.0** extends the dashboard with:

- Sector Velocity
- Velocity Colour Coding
- Observation History Size
- Temporal Observation Visualization

The dashboard is intended for development, debugging and validation of the Observation Engine.

Future versions of SixthSense will replace the dashboard with intuitive audio and haptic feedback.

# Repository Structure

The repository is intentionally organized to remain compatible with **Arduino App Lab** while maintaining a clean software architecture.

```text
SixthSense
│
├── docs/
│   ├── README.md
│   ├── SixthSense_v2.0.0.md
│   ├── SixthSense_v2.1.0.md
│   └── CHANGELOG.md
│
├── sketch/
│   └── sketch.ino
│
├── python/
│   └── main.py
│
├── assets/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── libs/
│       └── socket.io.min.js
│
└── LICENSE
```

The repository structure mirrors the deployment model supported by Arduino App Lab.

Although the software architecture is modular, Arduino App Lab currently supports:

- One Arduino Sketch
- One Python Backend

To remain compatible with these constraints, the software is implemented as a single sketch and a single Python application while maintaining logical separation between architectural components.

---

# Development Workflow

Development follows a simple release-oriented workflow.

```text
                develop
                   │
                   ▼
      Feature Implementation
                   │
                   ▼
        Testing & Validation
                   │
                   ▼
     Documentation Update
                   │
                   ▼
          GitHub Release
                   │
                   ▼
          Merge into main
```

---

## Branch Strategy

| Branch | Purpose |
|----------|----------|
| **main** | Latest stable release |
| **develop** | Active development |

The **develop** branch always contains work for the next planned release.

Once implementation, testing and documentation are complete, a GitHub Release is created and the changes are merged into **main**.

This workflow ensures that the **main** branch always represents the latest stable version of SixthSense.

---

# Documentation

Project documentation is maintained in the **docs/** directory.

| Document | Purpose |
|----------|---------|
| **README.md** | Project overview and architecture |
| **SixthSense_v2.0.0.md** | Static ToF Observation Engine |
| **SixthSense_v2.1.0.md** | Temporal ToF Observation Engine |
| **CHANGELOG.md** | Version history |

Each design document describes the architecture, implementation goals and validation strategy for a specific release.

Maintaining version-specific design documents makes it possible to understand how the software architecture evolves over time.

---

# Roadmap

The project is developed incrementally.

Each release introduces one complete architectural capability before moving to the next.

```text
v2.0.0
Static ToF Observation Engine
        │
        ▼
v2.1.0
Temporal ToF Observation Engine
        │
        ▼
v2.2.0
Persistent ToF Observation Engine
        │
        ▼
v3.0.0
Six-ToF Sensor Integration
        │
        ▼
v4.0.0
Context Engine
        │
        ▼
v5.0.0
Attention Engine
        │
        ▼
v6.0.0
Feedback Engine
        │
        ▼
v7.0.0
Complete SixthSense Prototype
```

The current focus is to fully mature the **Observation Engine** before introducing higher-level reasoning layers.

By the end of the v3.x series, the system will support six independent Time-of-Flight sensors, each producing its own `ToFObservation`.

The **Context Engine** will then consume observations from all sensors to construct a unified understanding of the surrounding environment.

---

# Current Focus

The immediate development effort is **v2.1.0 – Temporal ToF Observation Engine**.

The objectives of this release are:

- Observation History
- Sector-wise Velocity Estimation
- Velocity History
- Velocity Filtering
- Enhanced `ToFObservation`
- Dashboard Velocity Visualization

The goal is to transform the Observation Engine from a **static sensing layer** into a **temporal sensing layer** while preserving the existing observation interface.

Future releases will build upon this stable foundation rather than replacing it.

---

# License

This project is licensed under the **Mozilla Public License 2.0 (MPL-2.0)**.

See the **LICENSE** file for the complete license text.
