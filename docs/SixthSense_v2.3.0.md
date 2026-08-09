# SixthSense

> **A Modular Physical AI Perception Framework for Assistive Navigation**

<div align="center">

![Version](https://img.shields.io/badge/Version-v2.3.0-blue)
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
- Relative velocity
- Velocity validity
- Velocity state
- Motion persistence
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

## **v2.3.0 — Persistent ToF Observation Engine**

Version **v2.3.0** extends the Confidence-Aware Temporal ToF Observation Engine introduced in v2.2.1 with a **Motion Persistence Engine**.

Previous versions could estimate relative velocity and classify each sector as:

- `Approaching`
- `Stationary`
- `Receding`

Version v2.3.0 adds temporal evidence describing **how consistently a velocity state has been observed over successive processed observations**.

The implementation maintains three independent bounded persistence counters per sector:

```text
Approaching Persistence : 0 ... 100
Stationary Persistence  : 0 ... 100
Receding Persistence    : 0 ... 100
```

For every processed velocity classification:

```text
Approaching:
    Approaching +1
    Stationary  -1
    Receding    -1

Stationary:
    Approaching -1
    Stationary  +1
    Receding    -1

Receding:
    Approaching -1
    Stationary  -1
    Receding    +1

Unknown / other:
    Approaching -1
    Stationary  -1
    Receding    -1
```

All counters are saturated to:

```text
0 ... 100
```

The current velocity state's counter is exposed as:

```text
motion_persistence
```

For example:

```text
Velocity State     : Approaching
Motion Persistence : 80
```

`Motion Persistence` is a bounded temporal consistency/evidence score. It is **not a percentage, probability, or object identity score**.

Current implementation provides:

- Real-time 8×8 Time-of-Flight sensing
- Complete VL53L5CX measurement acquisition
- Synchronized Arduino-side sensor snapshots
- 64-zone confidence estimation
- Confidence-aware obstacle selection
- Three-sector obstacle observation
- Temporal observation history
- Relative velocity estimation
- Velocity validity tracking
- Velocity smoothing
- Velocity state classification
- `Unknown` state for unavailable/invalid velocity
- Per-sector Motion Persistence Engine
- Independent Approaching / Stationary / Receding persistence counters
- Distance heatmap
- Confidence heatmap
- Interactive confidence-aware web dashboard
- Motion persistence visualization
- Live structured JSON observation viewer

https://github.com/user-attachments/assets/4bd971f7-c2f7-41b0-82dd-f804ac0389fa

---

# Current Status

| Item | Status |
|------|:------:|
| Version | **v2.3.0** |
| Milestone | **Persistent ToF Observation Engine** |
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
| Velocity Validity | ✅ |
| Velocity Smoothing | ✅ |
| Velocity State Classification | ✅ |
| Motion Persistence Engine | ✅ |
| Per-State Persistence Counters | ✅ |
| Multi-Sensor Perception | 🚧 Planned |
| Context Engine | 🚧 Planned |
| Attention Engine | 🚧 Planned |
| Feedback Engine | 🚧 Planned |

---

# Dashboard

SixthSense includes a real-time web dashboard for visualizing the complete perception pipeline.

The **v2.3.0 dashboard** displays:

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
- Velocity state
- Motion persistence
- 8×8 distance heatmap
- 8×8 confidence heatmap
- Temporal observation history
- Live structured JSON observation
- Backend and dashboard versions

Each sector card presents the high-level temporal observation in a compact form:

```text
Distance             617 mm
Confidence            81.3 % HIGH
Zone                  63
Velocity              -5.0 mm/s
Velocity State        Stationary
Motion Persistence    100
```

`Motion Persistence` is intentionally displayed **without a `%` symbol** because it is a bounded evidence score rather than a calibrated probability.

The JSON viewer additionally exposes all three persistence counters for debugging and future reasoning layers.

---

# Why SixthSense?

Most obstacle detection systems answer a single question:

> **"Where is the obstacle?"**

SixthSense aims to progressively answer richer questions:

- Where is the obstacle?
- How reliable is the measurement?
- Is the measured range increasing or decreasing?
- Is the obstacle approximately approaching, stationary, or receding relative to the sensor?
- How consistently has that velocity state been observed?
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
Velocity State
     │
     ▼
Motion Persistence
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

Detailed implementation and architectural decisions for individual releases are maintained separately in the `docs/` directory.

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

The current prototype validates the **Persistent ToF Observation Engine** using a single **SparkFun VL53L5CX Time-of-Flight sensor** connected to an **Arduino UNO Q**.

```text
VL53L5CX
    │
    │  Continuous 15 Hz acquisition
    ▼
Arduino UNO Q
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
    ├── Confidence-Aware Sector Selection
    │
    ├── Observation Engine
    │
    ├── Velocity Estimation
    │
    ├── Velocity Smoothing
    │
    ├── Velocity State Classification
    │
    ├── Motion Persistence Engine
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

Python then retrieves the sensor arrays through the RouterBridge and creates one structured perception observation.

No Arduino firmware changes are required specifically for the Motion Persistence Engine because persistence is derived in Python after temporal velocity processing.

---

# VL53L5CX Sensor Data

SixthSense uses more than distance alone.

For each of the 64 VL53L5CX zones, SixthSense acquires:

| Measurement | Purpose |
|-------------|---------|
| Distance | Measured target range |
| Signal per SPAD | Strength/rate of returned ranging signal |
| Range Sigma | Estimated ranging uncertainty |
| Target Status | Sensor validity information |
| Reflectance | Sensor-provided target reflectance information |
| Ambient per SPAD | Background light activity |
| Number of Targets | Number of detected targets |
| SPADs Enabled | Active detector information |

These values are transferred from the Arduino to Python through the snapshot interface.

For clarity, the public sector observation uses explicit names for the SPAD-normalized rates:

```text
signal_kcps_per_spad
ambient_kcps_per_spad
```

The lower-level sensor transport may continue to use shorter internal names such as `signal` and `ambient`.

---

# Snapshot-Based Arduino Bridge

SixthSense uses a **snapshot-copy architecture** for transferring a complete sensor state from Arduino to Python.

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
Quality signals correspond to the captured snapshot state
```

The sensor continues ranging while Python consumes the snapshot.

This avoids permanently locking sensor acquisition and provides a stable interface for the Observation Engine.

The current design should be understood as a snapshot-copy mechanism rather than a formally proven atomic multi-threaded transaction.

---

# Confidence Engine

Version **v2.2.1** introduced the SixthSense **Confidence Engine**, which remains part of v2.3.0.

Instead of assuming every measured distance is equally trustworthy, the engine calculates an engineering measurement-quality score for every one of the 64 ToF zones.

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

SixthSense currently interprets it conservatively as:

| Target Status | Status Score |
|--------------:|-------------:|
| `5` | 1.0 |
| `6` | 0.5 |
| `9` | 0.5 |
| Other statuses | 0.0 in the current implementation |

Statuses outside `5`, `6`, and `9` are therefore rejected by the current confidence-aware obstacle-selection path.

This is an intentional conservative engineering decision.

---

# Important Confidence Note

The SixthSense confidence value is currently an **engineering measurement-quality score**.

For example:

```text
Confidence = 82
```

means that the current weighted confidence model produces a score of approximately 82/100.

It does **not currently mean**:

```text
There is exactly an 82% statistical probability
that the measured distance is correct.
```

The current model is heuristic and can be refined using controlled sensor characterization and real-world validation data.

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

Signal strength uses logarithmic normalization because the ranging signal can span a comparatively wide dynamic range.

The normalization reference values are engineering parameters and can be recalibrated as additional experimental data becomes available.

---

# Confidence-Aware Observation

Sector selection remains confidence-aware in v2.3.0.

The implementation selects the nearest **trusted** zone rather than simply selecting the nearest non-zero distance.

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
Target Status Accepted?
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

This prevents an unusable measurement from becoming the primary sector observation simply because its reported distance happens to be the smallest.

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
- Velocity validity tracking
- Velocity smoothing
- Velocity state classification
- Motion persistence estimation
- Raw quality information attached to selected observations

The processing order is:

```text
VL53L5CX Snapshot
        │
        ▼
Confidence Engine
        │
        ▼
Nearest Trusted Zone
        │
        ▼
Sector Observation
        │
        ▼
Velocity Estimation
        │
        ▼
Velocity Smoothing
        │
        ▼
Velocity State Classification
        │
        ▼
Motion Persistence Engine
        │
        ▼
ToFObservation
```

The Observation Engine performs **perception only**.

Environmental understanding, prioritization, navigation reasoning, and user feedback are intentionally handled by future architectural layers.

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
- Signal per SPAD
- Range sigma
- Target status
- Reflectance
- Ambient per SPAD
- Number of detected targets
- Enabled SPADs
- Relative velocity
- Velocity validity
- Velocity state
- Motion persistence
- Approaching persistence counter
- Stationary persistence counter
- Receding persistence counter

---

# Temporal Observation

SixthSense maintains a history of recent processed observations.

Current observation-history capacity:

```text
20 observations
```

Temporal information enables the system to estimate relative range velocity.

For each sector:

```text
velocity =
    (current_distance - previous_distance)
    /
    time_difference
```

Interpretation:

```text
Negative velocity  -> range is decreasing
Positive velocity  -> range is increasing
Near zero          -> approximately stationary range
```

The current velocity-state threshold is:

```text
velocity < -50 mm/s  -> Approaching
velocity > +50 mm/s  -> Receding
otherwise            -> Stationary
```

The velocity represents **relative range change**, not full 2-D or 3-D object velocity.

---

# Confidence and Velocity Validity

Confidence participates in velocity estimation as a **validity gate**.

Velocity is calculated only when both the current and previous sector observations provide usable trusted distances.

Conceptually:

```text
Current trusted distance?
        │
        ├── No  -> velocity_valid = false
        │
        ▼
Previous trusted distance?
        │
        ├── No  -> velocity_valid = false
        │
        ▼
Calculate relative velocity
        │
        ▼
velocity_valid = true
```

The numerical confidence score is **not multiplied into the physical velocity value**.

For example, a lower but still accepted confidence value does not artificially reduce the calculated range velocity.

---

# Velocity Smoothing

SixthSense uses a short per-sector velocity history to reduce frame-to-frame noise.

Current smoothing capacity:

```text
5 valid velocity samples
```

Only valid velocity samples are inserted into the velocity smoothing history.

An unavailable velocity is therefore not inserted as a synthetic zero measurement.

This distinction is important because:

```text
velocity = 0, velocity_valid = true
```

means a valid velocity estimate that is near zero, while:

```text
velocity = 0, velocity_valid = false
```

means that velocity could not be calculated from the current transition.

---

# Velocity State

Version v2.3.0 explicitly distinguishes valid velocity classification from unavailable velocity.

The possible states are:

```text
Approaching
Stationary
Receding
Unknown
```

Classification follows:

```text
velocity_valid = false
        │
        ▼
      Unknown
```

Otherwise:

```text
velocity < -50 mm/s
        │
        ▼
   Approaching

-50 mm/s <= velocity <= +50 mm/s
        │
        ▼
    Stationary

velocity > +50 mm/s
        │
        ▼
     Receding
```

This prevents an invalid placeholder numerical zero from being incorrectly interpreted as a genuine Stationary observation.

---

# Motion Persistence Engine

Version **v2.3.0** introduces the **Motion Persistence Engine**.

The engine answers a focused temporal question:

> **How consistently has the current velocity state been observed in this sector?**

It maintains three independent counters for every logical sector:

```text
Approaching
Stationary
Receding
```

Each counter is bounded to:

```text
0 ... 100
```

The update rule is symmetric.

## Approaching Observation

```text
Approaching += 1
Stationary  -= 1
Receding    -= 1
```

## Stationary Observation

```text
Approaching -= 1
Stationary  += 1
Receding    -= 1
```

## Receding Observation

```text
Approaching -= 1
Stationary  -= 1
Receding    += 1
```

## Unknown or Other Observation

```text
Approaching -= 1
Stationary  -= 1
Receding    -= 1
```

All operations are clamped to the valid range.

The current state's counter is published as:

```text
motion_persistence
```

The complete internal state is also exposed as:

```json
"motion_persistence_counters": {
    "approaching": 0,
    "stationary": 100,
    "receding": 0
}
```

---

# Motion Persistence Semantics

Motion persistence is intentionally simple and interpretable.

For example, after many consistent `Approaching` observations:

```text
Approaching = 80
Stationary  = 3
Receding    = 0
```

If the next observation is `Stationary`:

```text
Approaching = 79
Stationary  = 4
Receding    = 0
```

If `Approaching` resumes, the approaching counter can continue to recover.

This provides temporal memory without requiring object tracking.

---

# Important Motion Persistence Note

`motion_persistence` is **not**:

- A probability
- A percentage
- Measurement confidence
- Obstacle-presence probability
- Same-object tracking confidence
- An object identifier

It is a bounded **observation-based temporal consistency score for velocity classification**.

At an effective backend processing rate of approximately 5 observations per second:

```text
100 consecutive consistent classifications
≈ 20 seconds
```

At approximately 6 observations per second:

```text
100 consecutive consistent classifications
≈ 16.7 seconds
```

Therefore the current persistence score is **observation-count based**, not explicitly time-normalized.

---

# Invalid Velocity and Persistence

When the system cannot calculate a valid velocity from the current and previous observations:

```text
velocity_valid = false
velocity_state = Unknown
```

The Persistence Engine then applies its general "other classification" rule:

```text
Approaching -= 1
Stationary  -= 1
Receding    -= 1
```

This prevents an unavailable velocity from strengthening the Stationary persistence counter.

If no new sensor observation is processed at all, the Persistence Engine is not updated and the counters remain unchanged.

---

# ToFObservation

Every successfully processed sensor snapshot generates one structured **ToFObservation**.

A simplified v2.3.0 representation is:

```json
{
    "sensor_id": "tof_01",
    "sensor_name": "Prototype ToF",
    "status": "ONLINE",
    "frame_number": 1258,
    "timestamp": 121478,
    "fps": 5.5,
    "history_size": 20,
    "sectors": [
        {
            "sector_id": 0,
            "sector_name": "Sector 0",
            "distance_mm": 617,
            "zone_id": 63,
            "confidence": 81.3,
            "signal_kcps_per_spad": 121,
            "sigma": 6,
            "target_status": 5,
            "reflectance": 115,
            "ambient_kcps_per_spad": 127,
            "targets": 1,
            "spads": 4096,
            "velocity_mmps": -5.0,
            "velocity_valid": true,
            "velocity_state": "Stationary",
            "motion_persistence": 100,
            "motion_persistence_counters": {
                "approaching": 0,
                "stationary": 100,
                "receding": 0
            }
        }
    ]
}
```

Higher-level modules can consume this structured observation rather than interacting directly with raw sensor arrays.

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

The confidence heatmap visualizes the measurement-quality score associated with each zone.

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
How much the current confidence model trusts the measurement
```

The sector cards additionally expose the temporal interpretation:

```text
Relative Velocity
Velocity State
Motion Persistence
```

---

# Current Capabilities

Version **v2.3.0** provides:

| Capability | Status |
|------------|:------:|
| 8×8 ToF ranging | ✅ |
| Static obstacle observation | ✅ |
| Temporal observation history | ✅ |
| Relative velocity estimation | ✅ |
| Velocity validity tracking | ✅ |
| Velocity state classification | ✅ |
| Unknown state for invalid velocity | ✅ |
| Valid-only velocity smoothing | ✅ |
| Complete VL53L5CX quality acquisition | ✅ |
| Arduino snapshot transport | ✅ |
| 64-zone confidence estimation | ✅ |
| Confidence-aware sector selection | ✅ |
| Motion Persistence Engine | ✅ |
| Per-state persistence counters | ✅ |
| Distance heatmap | ✅ |
| Confidence heatmap | ✅ |
| Interactive web dashboard | ✅ |
| Live JSON observations | ✅ |
| Multi-sensor support | 🚧 Planned |
| Context reasoning | 🚧 Planned |
| Attention model | 🚧 Planned |
| User feedback engine | 🚧 Planned |

---

# Current Scope

The current implementation intentionally focuses on **perception**.

It does not yet attempt to:

- Identify or track individual physical objects
- Fuse measurements from multiple ToF sensors
- Infer complete environmental context
- Estimate user intent
- Prioritize observations
- Generate navigation decisions
- Produce haptic feedback
- Produce spatial audio feedback

Motion persistence should not be confused with same-object tracking.

If a selected zone changes within the same logical sector, the Persistence Engine continues to operate on the sector's velocity-state sequence.

---

# Hardware & Software

## Current Hardware

| Component | Quantity |
|-----------|---------:|
| Arduino UNO Q | 1 |
| SparkFun VL53L5CX Time-of-Flight Sensor | 1 |
| Qwiic JST Cable | 1 |
| USB-C Cable | 1 |

The current prototype intentionally uses a single ToF sensor to validate the perception architecture before scaling to multiple sensors.

Future releases will expand the system toward multiple independently observed directions.

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

A dedicated v2.3.0 architecture document can be added alongside the earlier release documents as part of the release documentation.

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
     v2.3.0
Motion Persistence
        │
        ▼
     v3.0.0
Multi-Sensor Perception
        │
        ▼
     v4.0.0
     Context
        │
        ▼
     v5.0.0
    Attention
        │
        ▼
     v6.0.0
    Feedback
        │
        ▼
     v7.0.0
Complete Prototype
```

---

# Roadmap

| Version | Milestone | Status |
|---------|-----------|:------:|
| **v2.0.0** | Static ToF Observation Engine | ✅ |
| **v2.1.0** | Temporal ToF Observation Engine | ✅ |
| **v2.2.1** | Confidence-Aware Temporal ToF Observation Engine | ✅ |
| **v2.3.0** | Persistent ToF Observation Engine | ✅ |
| **v3.0.0** | Multi-ToF Sensor Integration | 🚧 |
| **v4.0.0** | Context Engine | 🚧 |
| **v5.0.0** | Attention Engine | 🚧 |
| **v6.0.0** | Feedback Engine | 🚧 |
| **v7.0.0** | Complete SixthSense Prototype | 🎯 |

---

# Future Direction

Version v2.3.0 establishes a **confidence-aware temporal perception layer with motion-state persistence**.

The next major steps are expected to include:

### Multi-Sensor Perception

Scale the architecture from one ToF sensor to multiple independently observed directions while preserving a consistent observation interface.

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

Version v2.3.0 has several intentional limitations.

### Single Sensor

Only one VL53L5CX sensor is currently integrated.

### Heuristic Confidence

The confidence model is an engineering quality score and has not yet been statistically calibrated against large-scale ground-truth datasets.

### Relative Range Velocity Only

Velocity is estimated from successive sector distances.

It represents relative range change rather than complete object motion or world-frame velocity.

### Sector-Level Motion Persistence

Persistence is maintained independently per logical sector.

It does not prove that the same physical object generated every observation in the sequence.

### No Object Tracking

The current implementation does not associate detections with persistent object identities.

Motion persistence therefore represents consistency of the sector's velocity classification, not same-object persistence.

### Observation-Based Persistence

Persistence increments and decrements once per processed observation.

It is not currently normalized by elapsed wall-clock time.

### Effective Backend Observation Rate

The VL53L5CX is configured for higher-rate sensor acquisition, while the Python backend performs multiple RouterBridge calls per snapshot.

The backend may therefore process fewer observations per second than the underlying sensor acquisition frequency.

### Persistence Memory Across Measurement Gaps

Invalid velocity transitions do not enter the smoothing history and are classified as `Unknown`.

The current implementation does not perform explicit object re-identification across measurement gaps.

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
- Velocity validity handling
- Valid-only velocity smoothing
- Velocity state classification
- `Unknown` state handling
- Motion persistence counter updates
- Persistence saturation at 0 and 100
- Independent per-sector persistence
- Distance heatmap visualization
- Confidence heatmap visualization
- Real-time dashboard updates
- Motion persistence dashboard display
- Live structured JSON observations

Recommended v2.3.0 persistence validation cases include:

- Continuous Stationary observations
- Continuous Approaching observations
- Continuous Receding observations
- Single-state glitches
- Sustained state transitions
- Unknown / invalid velocity transitions
- Counter saturation at 100
- Counter floor at 0
- Independent behavior across sectors
- Zone changes within the same sector

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
- Temporal perception
- Motion persistence
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

For architectural discussions and ideas, use **GitHub Discussions** when available for the repository.

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
- Pull Requests
- Repository discussions when available

Constructive feedback and contributions are greatly appreciated.

---

<div align="center">

### SixthSense

**Perception → Confidence → Temporal Motion → Persistence → Understanding → Attention → Feedback**

</div>
