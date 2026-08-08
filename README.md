# SixthSense

> **A Modular Physical AI Perception Framework for Assistive Navigation**

<div align="center">

![Version](https://img.shields.io/badge/Version-v2.2.1-blue)
![Status](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Arduino%20UNO%20Q-red)
![Sensor](https://img.shields.io/badge/Sensor-VL53L5CX-brightgreen)
![License](https://img.shields.io/badge/License-MPL--2.0-yellow)

</div>

---

# Overview

**SixthSense** is an open-source Physical AI project that explores how wearable systems can perceive and understand their surroundings using Time-of-Flight (ToF) sensors.

Instead of directly converting raw sensor measurements into feedback, SixthSense follows an **Observation-First Architecture**.

Raw sensor data is progressively transformed into structured observations containing:

- Distance
- Measurement confidence
- Relative motion
- Temporal history
- Sensor quality information

These observations can later be interpreted by higher-level reasoning modules such as the **Context Engine**, **Attention Engine**, and **Feedback Engine**.

This layered approach keeps:

- Perception
- Environmental reasoning
- Prioritization
- User feedback

independent from one another, making the system easier to develop, validate, extend, and scale.

The long-term goal is to build a wearable assistive navigation system capable of understanding the surrounding environment and providing intuitive guidance to visually impaired users.

---

# Current Release

## **v2.2.1 — Confidence-Aware Temporal ToF Observation Engine**

Version **v2.2.1** extends the Temporal ToF Observation Engine introduced in v2.1.0 with **measurement confidence estimation**.

The VL53L5CX sensor provides much more information than distance alone.

SixthSense now uses multiple sensor quality signals to determine how trustworthy each individual ranging measurement is.

Current implementation provides:

- Real-time 8×8 Time-of-Flight sensing
- Complete VL53L5CX measurement acquisition
- Synchronized Arduino-side sensor snapshots
- 64-zone confidence estimation
- Confidence-aware obstacle selection
- Three-sector obstacle observation
- Temporal observation history
- Relative velocity estimation
- Motion state classification
- Velocity smoothing
- Distance heatmap
- Confidence heatmap
- Interactive confidence-aware web dashboard
- Live JSON observation viewer
<img width="1918" height="968" alt="confidence_low-ezgif com-optimize" src="https://github.com/user-attachments/assets/88e09a4c-59d8-48ba-b218-b5abb367cc31" />

---

# Current Status

| Item | Status |
|------|:------:|
| Version | **v2.2.1** |
| Milestone | Confidence-Aware Temporal ToF Observation Engine |
| Hardware | Arduino UNO Q + VL53L5CX |
| ToF Sensors | 1 *(Planned: 6)* |
| Dashboard | ✅ |
| 8×8 Distance Sensing | ✅ |
| Full VL53L5CX Quality Signals | ✅ |
| Synchronized Sensor Snapshot | ✅ |
| Zone Confidence | ✅ |
| Confidence-Aware Sector Selection | ✅ |
| Observation History | ✅ |
| Velocity Estimation | ✅ |
| Velocity Smoothing | ✅ |
| Motion Classification | ✅ |
| Persistence Engine | 🚧 Planned |
| Multi-Sensor Perception | 🚧 Planned |
| Context Engine | 🚧 Planned |
| Attention Engine | 🚧 Planned |
| Feedback Engine | 🚧 Planned |

---

# Dashboard

SixthSense includes a real-time web dashboard for visualizing the complete perception pipeline.

The **v2.2.1 dashboard** displays:

- Sensor information
- Sensor connection state
- Arduino Bridge state
- Frame number
- Timestamp
- Effective observation FPS
- Three logical obstacle sectors
- Nearest trusted distance per sector
- Measurement confidence per sector
- Confidence classification
- VL53L5CX source zone
- Relative velocity
- Motion state
- 8×8 distance heatmap
- 8×8 confidence heatmap
- Temporal observation history
- Live structured JSON observation
- Backend and dashboard versions

## Confidence-Aware Dashboard Demo

![SixthSense v2.2.1 Confidence Dashboard](assets/sixthsense_v2_2_1_confidence_dashboard.gif)

The left heatmap represents measured obstacle distance.

The right heatmap represents the confidence assigned to each corresponding VL53L5CX zone.

A zone can therefore contain a raw distance measurement while still receiving low or zero confidence if the associated sensor quality indicators suggest that the measurement should not be trusted.

---

# Why SixthSense?

Most obstacle detection systems answer a single question:

> **"Where is the obstacle?"**

SixthSense aims to progressively answer richer questions:

- Where is the obstacle?
- How reliable is the measurement?
- Is the object approaching or moving away?
- Does the observation remain stable over time?
- What is happening around the user?
- Which information deserves the user's attention?
- How should that information be communicated?

This progression can be represented as:

```text
Measurement
     │
     ▼
Confidence
     │
     ▼
Temporal Observation
     │
     ▼
Persistence
     │
     ▼
Context
     │
     ▼
Attention
     │
     ▼
Feedback
```

By separating perception from reasoning, SixthSense builds a foundation that can evolve from simple obstacle detection toward intelligent environmental understanding.

---

# Design Philosophy

SixthSense is developed incrementally.

Each software release introduces a focused architectural capability while preserving the existing software foundation.

The project follows four guiding principles:

- **Observation First** — Convert raw sensor measurements into structured observations before performing higher-level reasoning.
- **Modularity** — Keep architectural responsibilities independent.
- **Incremental Evolution** — Add and validate one capability at a time.
- **Scalability** — Design components that naturally extend to multiple sensors.

Detailed implementation and architectural decisions for individual releases are documented separately in the `docs/` directory.

---

# Architecture

SixthSense follows an **Observation-First Architecture**, where every layer has a single, well-defined responsibility.

```text
Time-of-Flight Sensors
          │
          ▼
 Observation Engine
          │
          ▼
  Context Engine
          │
          ▼
 Attention Engine
          │
          ▼
 Feedback Engine
          │
          ▼
         User
```

Rather than converting raw sensor measurements directly into user feedback, the system progressively transforms information into increasingly meaningful representations.

This keeps:

- Sensor acquisition
- Observation generation
- Environmental reasoning
- Observation prioritization
- User feedback

independent.

---

# Current Runtime Architecture

The current prototype validates the **Confidence-Aware Temporal ToF Observation Engine** using a single **SparkFun VL53L5CX Time-of-Flight sensor** connected to an **Arduino UNO Q**.

```text
VL53L5CX
    │
    │
    ▼
Arduino UNO Q
    │
    │  Continuous 15 Hz acquisition
    │
    ▼
Live Sensor Buffers
    │
    │ capture_snapshot()
    ▼
Snapshot Buffers
    │
    ▼
Arduino RouterBridge RPC
    │
    ▼
Python Backend
    │
    ├── Confidence Engine
    │
    ├── Observation Engine
    │
    ├── Velocity Estimation
    │
    └── Observation History
    │
    ▼
Structured ToFObservation
    │
    ▼
Interactive Web Dashboard
```

The Arduino continuously acquires sensor frames.

When the Python backend requests a snapshot, the Arduino copies the current complete sensor state into dedicated snapshot buffers.

Python can then retrieve the full measurement safely without requiring the sensor acquisition loop to stop.

---

# VL53L5CX Sensor Data

Version v2.2.1 no longer uses distance alone.

For each of the 64 VL53L5CX zones, SixthSense acquires:

| Measurement | Purpose |
|-------------|---------|
| Distance | Measured target range |
| Signal per SPAD | Strength of returned laser signal |
| Range Sigma | Estimated ranging uncertainty |
| Target Status | Sensor validity information |
| Reflectance | Estimated target reflectivity |
| Ambient per SPAD | Background light level |
| Number of Targets | Number of detected targets |
| SPADs Enabled | Active detector information |

These values are transferred from the Arduino to Python through the synchronized snapshot interface.

---

# Snapshot-Based Arduino Bridge

A major change in v2.2.1 is the introduction of a **snapshot-copy architecture**.

Earlier approaches could retrieve different sensor arrays from different sensor frames because each Arduino Bridge RPC required a separate transaction.

SixthSense now follows:

```text
Sensor continuously updates LIVE buffers
                 │
                 ▼
        capture_snapshot()
                 │
                 ▼
LIVE buffers copied to SNAPSHOT buffers
                 │
                 ▼
Python retrieves snapshot arrays
                 │
                 ▼
All quality signals correspond to one captured state
```

The sensor continues ranging while Python consumes the snapshot.

This avoids permanently locking sensor acquisition and provides a stable interface for the Observation Engine.

---

# Confidence Engine

Version **v2.2.1** introduces the first SixthSense **Confidence Engine**.

Instead of assuming every measured distance is equally trustworthy, the engine calculates a quality score for every one of the 64 ToF zones.

The current confidence model combines:

- Target status
- Signal strength
- Range sigma
- Ambient light
- Reflectance
- Number of detected targets
- Enabled SPADs

The current weighting is:

| Signal | Weight |
|--------|-------:|
| Target Status | 30% |
| Signal per SPAD | 30% |
| Range Sigma | 20% |
| Ambient per SPAD | 5% |
| Reflectance | 5% |
| Targets Detected | 5% |
| SPADs Enabled | 5% |

Total:

```text
100%
```

The confidence score is reported in the range:

```text
0 – 100
```

---

# Target Status Interpretation

The VL53L5CX documentation provides confidence guidance for target status.

SixthSense currently interprets it as:

| Target Status | Status Confidence |
|--------------:|------------------:|
| `5` | 100% |
| `6` | 50% |
| `9` | 50% |
| Other statuses | Below 50% |

For the current implementation, statuses outside `5`, `6`, and `9` are treated conservatively as invalid for confidence-aware obstacle selection until better experimental calibration is available.

This is an intentional engineering decision.

---

# Important Confidence Note

The SixthSense confidence value is currently an **engineering measurement quality score**.

For example:

```text
Confidence = 82%
```

means that the current weighted confidence model produces a score of 82/100.

It does **not currently mean**:

```text
There is exactly an 82% statistical probability
that the measured distance is correct.
```

The current model is heuristic and will be refined using controlled sensor characterization and real-world validation data.

---

# Confidence Normalization

Different VL53L5CX outputs have different numerical ranges.

SixthSense converts them into normalized values before weighted fusion.

Conceptually:

```text
Higher-is-better measurement:

score = normalized(value)
```

Examples:

- Signal strength
- Reflectance
- Enabled SPADs

For lower-is-better measurements:

```text
score = 1 - normalized(value)
```

Examples:

- Range sigma
- Ambient light

Signal strength uses logarithmic normalization because VL53L5CX signal values can span a large dynamic range.

The normalization reference values are currently engineering parameters derived from collected sensor logs and can be recalibrated as additional experimental data becomes available.

---

# Confidence-Aware Observation

A major behavioral change in v2.2.1 is that sector selection is now confidence-aware.

Earlier versions selected the nearest non-zero distance inside a sector.

The current implementation selects the nearest **trusted** zone.

A measurement must satisfy the configured validity and confidence requirements before it can represent a sector obstacle.

Conceptually:

```text
All Zones in Sector
        │
        ▼
Distance Valid?
        │
        ▼
Target Detected?
        │
        ▼
Target Status Valid?
        │
        ▼
Confidence > 0?
        │
        ▼
Nearest Trusted Zone
        │
        ▼
Sector Observation
```

This prevents an unreliable sensor reading from becoming the primary obstacle observation simply because its reported distance happens to be the smallest.

---

# Observation Engine

The Observation Engine remains the core perception component of SixthSense.

Its responsibility is to convert Time-of-Flight sensor information into structured observations.

Current capabilities include:

- Three-sector spatial observation model
- Confidence-aware obstacle selection
- Observation history
- Temporal processing
- Relative velocity estimation
- Motion state classification
- Velocity smoothing
- Raw quality information attached to selected observations

The Observation Engine performs **perception only**.

Environmental understanding, prioritization, navigation reasoning, and feedback are intentionally handled by future architectural layers.

---

# Three-Sector Observation Model

The oriented 8×8 ToF image is currently divided into three logical sectors:

```text
Column:

0  1 | 2  3  4 | 5  6  7

─────   ───────   ───────
 S0       S1        S2
```

Each sector produces one `SectorObservation`.

The current sector observation contains:

- Sector identifier
- Sector name
- Nearest trusted distance
- Source VL53L5CX zone
- Confidence score
- Signal
- Range sigma
- Target status
- Reflectance
- Ambient level
- Number of detected targets
- Enabled SPADs
- Relative velocity
- Motion state
- Persistence placeholder

---

# ToFObservation

Every successfully processed sensor snapshot generates one structured **ToFObservation**.

A simplified representation is:

```json
{
    "sensor_id": "tof_01",
    "sensor_name": "Prototype ToF",
    "status": "ONLINE",
    "frame_number": 934,
    "timestamp": 88774,
    "fps": 6.1,
    "history_size": 20,
    "sectors": [
        {
            "sector_id": 0,
            "distance_mm": 542,
            "zone_id": 63,
            "confidence": 88.3,
            "signal": 138,
            "sigma": 5,
            "target_status": 5,
            "reflectance": 91,
            "ambient": 120,
            "targets": 1,
            "spads": 3584,
            "velocity_mmps": -6.5,
            "velocity_state": "Stationary",
            "persistence": 0
        }
    ]
}
```

Higher-level modules can consume this structured observation rather than interacting directly with raw sensor arrays.

---

# Temporal Observation

SixthSense maintains a history of recent observations.

Current history size:

```text
20 observations
```

Temporal information enables the system to estimate relative obstacle motion.

For each sector:

```text
velocity =
    (current_distance - previous_distance)
    /
    time_difference
```

Interpretation:

```text
Negative velocity  -> Approaching
Positive velocity  -> Receding
Near zero          -> Stationary
```

Velocity measurements are smoothed using a short moving-average history to reduce frame-to-frame noise.

---

# Dashboard Heatmaps

## Distance Heatmap

The distance heatmap visualizes all 64 ToF ranging zones.

Conceptually:

```text
Near obstacle
     ↓
    Red → Orange → Yellow → Green
                              ↑
                         Far obstacle
```

## Confidence Heatmap

The confidence heatmap visualizes the quality score associated with each zone.

```text
Low confidence
     ↓
    Red → Orange → Yellow → Green
                              ↑
                        High confidence
```

Zones that fail the current validity checks are displayed as zero-confidence measurements.

The dashboard therefore makes it possible to compare:

```text
What the sensor measured
```

against:

```text
How much the current system trusts the measurement
```

---

# Current Capabilities

Version **v2.2.1** provides:

| Capability | Status |
|------------|:------:|
| 8×8 ToF ranging | ✅ |
| Static obstacle observation | ✅ |
| Temporal observation history | ✅ |
| Relative velocity estimation | ✅ |
| Motion state classification | ✅ |
| Velocity smoothing | ✅ |
| Complete VL53L5CX quality acquisition | ✅ |
| Arduino snapshot transport | ✅ |
| 64-zone confidence estimation | ✅ |
| Confidence-aware sector selection | ✅ |
| Distance heatmap | ✅ |
| Confidence heatmap | ✅ |
| Interactive web dashboard | ✅ |
| Live JSON observations | ✅ |
| Persistence estimation | 🚧 Planned |
| Multi-sensor support | 🚧 Planned |
| Context reasoning | 🚧 Planned |
| Attention model | 🚧 Planned |
| User feedback engine | 🚧 Planned |

---

# Current Scope

The current implementation intentionally focuses on **perception**.

It does not yet attempt to:

- Understand complete environmental context
- Estimate user intent
- Persistently track obstacles
- Fuse multiple ToF sensors
- Prioritize observations
- Generate navigation decisions
- Produce haptic feedback
- Produce spatial audio feedback

These capabilities will be introduced progressively through future releases.

---

# Hardware & Software

## Current Hardware

| Component | Quantity |
|-----------|---------:|
| Arduino UNO Q | 1 |
| SparkFun VL53L5CX Time-of-Flight Sensor | 1 |
| Qwiic JST Cable | 1 |
| USB-C Cable | 1 |

The current prototype intentionally uses a single ToF sensor to validate the complete perception architecture before scaling to multiple sensors.

Future releases will expand the system toward six independent Time-of-Flight sensors.

<img width="960" height="1280" alt="Arduino UNO Q with VL53L5CX" src="https://github.com/user-attachments/assets/4968e3f6-217f-41ab-af97-992710e7f006" />

---

## Software Stack

| Layer | Technology |
|------|------------|
| Firmware | Arduino Sketch / C++ |
| Sensor Library | SparkFun VL53L5CX Arduino Library |
| MCU ↔ MPU Communication | Arduino RouterBridge RPC |
| Backend | Python |
| Numerical Processing | NumPy |
| Frontend | HTML, CSS, JavaScript |
| Dashboard | Arduino App Lab WebUI |
| Real-Time Browser Communication | Socket.IO |

---

# Repository Structure

```text
sixthsense/
│
├── README.md
├── LICENSE
├── app.yaml
│
├── sketch/
│   └── sketch.ino
│
├── python/
│   └── main.py
│
├── assets/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── sixthsense_v2_2_1_confidence_dashboard.gif
│   └── libs/
│
└── docs/
    ├── CHANGELOG.md
    ├── SixthSense_v2.0.0.md
    ├── SixthSense_v2.1.0.md
    ├── SixthSense_v2.2.1.md
    └── ...
```

The **README** provides the high-level project overview.

The `docs/` directory contains detailed design and release documentation.

---

# Development

SixthSense follows an incremental development workflow.

Development is performed on:

```text
develop
```

Stable, tested versions are merged into:

```text
main
```

Typical workflow:

```text
feature / implementation
        │
        ▼
     develop
        │
        ├── integration
        ├── validation
        ├── documentation
        └── dashboard testing
        │
        ▼
      main
        │
        ▼
 GitHub Release / Tag
```

Each release should be independently:

- Functional
- Testable
- Documented
- Reviewable

before being merged into `main`.

---

# Release Evolution

```text
v2.0.0
Static Observation
        │
        ▼
v2.1.0
Temporal Observation
        │
        ▼
v2.2.1
Confidence-Aware
Temporal Observation
        │
        ▼
Persistence
        │
        ▼
Multi-Sensor Perception
        │
        ▼
Context
        │
        ▼
Attention
        │
        ▼
Feedback
        │
        ▼
Complete Prototype
```

---

# Roadmap

| Version | Milestone | Status |
|---------|-----------|:------:|
| **v2.0.0** | Static ToF Observation Engine | ✅ |
| **v2.1.0** | Temporal ToF Observation Engine | ✅ |
| **v2.2.1** | Confidence-Aware Temporal ToF Observation Engine | ✅ |
| **v2.3.0** | Persistent ToF Observation Engine | 🚧 |
| **v3.0.0** | Multi-ToF Sensor Integration | 🚧 |
| **v4.0.0** | Context Engine | 🚧 |
| **v5.0.0** | Attention Engine | 🚧 |
| **v6.0.0** | Feedback Engine | 🚧 |
| **v7.0.0** | Complete SixthSense Prototype | 🎯 |

---

# Future Direction

The current release establishes a **confidence-aware perception foundation**.

The next major steps are expected to include:

### Persistence

Determine whether an observed obstacle remains consistently present across multiple observations rather than reacting to isolated detections.

### Multi-Sensor Perception

Scale the architecture from one ToF sensor to multiple independently observed directions.

### Context Engine

Combine observations into a meaningful representation of the surrounding environment.

### Attention Engine

Determine which observations are most relevant and require user attention.

### Feedback Engine

Translate prioritized environmental information into intuitive:

- Haptic guidance
- Spatial audio guidance
- Navigation cues

The long-term objective is to develop a modular Physical AI perception framework that cleanly separates:

```text
Perception
    ↓
Understanding
    ↓
Prioritization
    ↓
Feedback
```

---

# Known Limitations

Version v2.2.1 currently has several intentional limitations.

### Single Sensor

Only one VL53L5CX sensor is currently integrated.

### Heuristic Confidence

The confidence model is an engineering quality score and has not yet been statistically calibrated against large-scale ground-truth datasets.

### Relative Motion Only

Velocity is estimated from successive sector distances and represents relative range change rather than complete object motion.

### No Persistent Object Tracking

Sector observations currently represent the latest trusted measurement.

Long-term obstacle persistence will be handled by a future Persistence Engine.

### Effective Backend Observation Rate

The VL53L5CX is configured for higher-rate sensor acquisition, while the Python backend performs multiple RouterBridge calls per snapshot.

The backend may therefore process fewer observations per second than the underlying sensor acquisition frequency.

---

# Validation

The current prototype has been validated through live Arduino UNO Q testing with the VL53L5CX.

Observed functionality includes:

- Sensor initialization
- Continuous ranging
- 8×8 distance acquisition
- Complete sensor quality acquisition
- Snapshot-based Bridge transport
- 64-zone confidence computation
- Confidence-aware sector selection
- Relative velocity calculation
- Temporal observation history
- Distance heatmap visualization
- Confidence heatmap visualization
- Real-time dashboard updates
- Live structured JSON observations

---

# Documentation

Detailed implementation notes are maintained in the `docs/` directory.

```text
docs/

├── CHANGELOG.md
├── SixthSense_v2.0.0.md
├── SixthSense_v2.1.0.md
├── SixthSense_v2.2.1.md
└── ...
```

The version-specific documents describe:

- Architecture
- Design decisions
- Data flow
- Algorithms
- Implementation details
- Validation
- Known limitations
- Future extensions

---

# Contributing

Contributions are welcome.

Areas where contributions can have significant impact include:

- Time-of-Flight perception
- Sensor confidence modelling
- Sensor characterization
- Embedded firmware
- Python perception algorithms
- Multi-sensor architecture
- Dashboard improvements
- Assistive navigation algorithms
- Validation
- Documentation

If you plan to contribute:

1. Fork the repository.
2. Create a feature branch from `develop`.
3. Implement and test the change.
4. Update relevant documentation.
5. Submit a Pull Request.

For bug reports and feature requests, use **GitHub Issues**.

For architectural discussions and ideas, use **GitHub Discussions**.

---

# Citation

If you use SixthSense in your research or build upon this project, please consider citing the repository.

```text
Eswara Venkata Kumar Dhulipala

SixthSense:
A Modular Physical AI Perception Framework
for Assistive Navigation.

GitHub Repository

https://github.com/Eswara-Venkata-Kumar-Dhulipala/SixthSense
```

---

# License

SixthSense is released under the **Mozilla Public License 2.0 (MPL-2.0)**.

See the `LICENSE` file for the complete license.

---

# Acknowledgements

SixthSense builds upon an excellent open-source hardware and software ecosystem.

Special thanks to:

- Arduino
- Arduino App Lab
- SparkFun Electronics
- STMicroelectronics
- Python Community
- NumPy Community
- Open Source Community

Their hardware, libraries, development tools, documentation, and open-source contributions make projects like SixthSense possible.

---

# Contact

Questions, suggestions, bug reports, architectural discussions, and contributions are welcome.

Please use:

- GitHub Issues
- GitHub Discussions
- Pull Requests

Constructive feedback and contributions are greatly appreciated.

---

<div align="center">

### SixthSense

**Perception → Confidence → Understanding → Attention → Feedback**

</div>
