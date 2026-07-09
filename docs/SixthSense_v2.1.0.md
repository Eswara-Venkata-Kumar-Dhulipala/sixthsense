# SixthSense v2.1.0

## Dynamic ToF Observation Engine

**Version:** 2.1.0

**Status:** Design Specification

**Previous Version:** v2.0.0 – First Stable ToF Observation Engine

---

# 1. Introduction

Version **2.1.0** extends the Observation Engine introduced in v2.0.0 by enabling **dynamic observation** of the environment.

The previous version produced **static observations**, where each sector contained only the nearest measured distance.

Version **2.1.0** introduces **velocity estimation**, allowing the system to determine whether an object is:

- Approaching
- Moving Away
- Stationary

This information forms the foundation for future modules such as the Persistence Engine, Camera Observation Engine, Context Engine, Attention Engine, and Output Manager.

---

# 2. Objectives

The primary objectives of Version 2.1.0 are:

- Maintain a rolling history of observations.
- Estimate object velocity independently for each sector.
- Extend the ToF Observation API.
- Preserve backward compatibility with v2.0.0.
- Keep the architecture extensible for future enhancements.

---

# 3. Design Philosophy

The Observation Engine should only produce objective measurements.

It should never make decisions.

The pipeline therefore becomes

```
Raw Sensor Data
        ↓
Observation Builder
        ↓
History Buffer
        ↓
Observation Enhancer
        ↓
Enhanced Observation
        ↓
Dashboard
        ↓
Future Context Engine
```

The Observation Engine measures **what is happening**.

The Context Engine will later determine **what it means**.

---

# 4. Overall Architecture

```
VL53L5CX
      │
      ▼
Arduino Sketch
      │
      ▼
Bridge RPC
      │
      ▼
Observation Builder
      │
      ▼
ToFObservation
      │
      ▼
History Buffer
      │
      ▼
Velocity Estimator
      │
      ▼
Enhanced ToFObservation
      │
      ▼
Dashboard
      │
      ▼
Future Context Engine
```

---

# 5. Observation Pipeline

The complete processing pipeline consists of six stages.

## Stage 1

Acquire one 8×8 ToF frame.

↓

## Stage 2

Divide the frame into three sectors.

```
Sector 0

Sector 1

Sector 2
```

↓

## Stage 3

Generate a ToFObservation.

↓

## Stage 4

Store the observation in the rolling history buffer.

↓

## Stage 5

Estimate sector velocities.

↓

## Stage 6

Display the enhanced observation on the dashboard.

---

# 6. Configuration Module

The following configuration parameters are introduced.

```python
HISTORY_CAPACITY = 20

VELOCITY_WINDOW = 5

MIN_VALID_DT = 0.05
```

## HISTORY_CAPACITY

Maximum number of observations stored in memory.

Default:

```
20 observations
```

---

## VELOCITY_WINDOW

Number of observations used for smoothing before computing velocity.

Default:

```
5 observations
```

---

## MIN_VALID_DT

Minimum allowable time difference between two observations.

Default:

```
0.05 seconds
```

This prevents division by extremely small time intervals.

---

# 7. Updated Data Model

## SectorObservation

Version 2.0.0

```python
SectorObservation

sector_id

sector_name

distance
```

Version 2.1.0

```python
SectorObservation

sector_id

sector_name

distance

velocity
```

---

## ToFObservation

Version 2.0.0

```python
ToFObservation

sensor_id

sensor_name

status

frame_number

timestamp

fps

image

sectors
```

Version 2.1.0

```python
ToFObservation

sensor_id

sensor_name

status

frame_number

timestamp

fps

history_size

image

sectors
```

---

# 8. History Buffer

A rolling history buffer stores the most recent observations.

```
Newest

↓

Observation 20

↓

Observation 19

↓

Observation 18

↓

...

↓

Observation 2

↓

Observation 1

Oldest
```

The buffer size is fixed.

When full,

the oldest observation is discarded.

---

# 9. Velocity Estimation

Velocity is estimated independently for each sector.

```
Sector 0

Previous Distance

↓

Current Distance

↓

Velocity
```

The same computation is performed for:

- Sector 1
- Sector 2

---

# 10. Velocity Equation

Velocity is computed using

```
velocity =

(previous_distance - current_distance)

/

Δt
```

where

- distance is measured in millimetres
- time is measured in seconds

Resulting unit

```
millimetres / second
```

---

# 11. Velocity Interpretation

Velocity remains a **numeric observation**.

Interpretation is deferred to the future Context Engine.

However, during dashboard visualization:

| Velocity | Meaning |
|-----------|----------|
| Positive | Object approaching |
| Zero | Stationary |
| Negative | Object moving away |

---

# 12. Noise Reduction

Distance measurements naturally contain noise.

Velocity must **not** be estimated directly from two consecutive observations.

Instead,

the Observation Enhancer computes the average distance over a configurable moving window.

```
History Buffer

↓

Moving Average

↓

Velocity Estimation
```

This significantly reduces false velocity spikes.

---

# 13. Dashboard Updates

Each sector card is extended.

Current

```
Sector 0

Distance

345 mm
```

Updated

```
Sector 0

Distance

345 mm

Velocity

+118 mm/s
```

---

# 14. Velocity Colour Coding

Dashboard colours

| State | Colour |
|---------|---------|
| Approaching | Red |
| Stationary | Green |
| Moving Away | Blue |

---

# 15. Observation JSON

Example

```json
{
    "sensor_id": "tof_01",
    "sensor_name": "Left ToF",
    "status": "ONLINE",
    "frame_number": 1423,
    "timestamp": 58420,
    "fps": 10.8,
    "history_size": 20,
    "sectors":
    [
        {
            "sector_id": 0,
            "sector_name": "Sector 0",
            "distance": 338,
            "velocity_mmps": 145
        },
        {
            "sector_id": 1,
            "sector_name": "Sector 1",
            "distance": 331,
            "velocity_mmps": -24
        },
        {
            "sector_id": 2,
            "sector_name": "Sector 2",
            "distance": 346,
            "velocity_mmps": 0
        }
    ]
}
```

---

# 16. Validation Procedure

## Test 1

Static Environment

Expected:

```
Velocity ≈ 0 mm/s
```

---

## Test 2

Move an object slowly toward the sensor.

Expected:

```
Positive velocity
```

---

## Test 3

Move an object away from the sensor.

Expected:

```
Negative velocity
```

---

## Test 4

Move the object laterally.

Expected:

```
Velocity close to zero
```

---

## Test 5

Rapid approach.

Expected:

Large positive velocity without oscillation.

---

# 17. Out of Scope

The following features are intentionally excluded from Version 2.1.0.

- Persistence
- Confidence Estimation
- Camera Observation Engine
- Context Engine
- Attention Engine
- Spatial Audio
- Haptic Feedback

---

# 18. Roadmap

## Version 2.2.0

Persistence Engine

- Observation persistence
- Temporal stability
- Confidence estimation

---

## Version 3.0.0

Camera Observation Engine

- Object Detection
- Bounding Boxes
- CameraObservation API

---

## Version 4.0.0

Context Engine

- Multi-sensor reasoning
- Scene understanding
- Environmental context generation

---

## Version 5.0.0

Attention Engine

- Risk prioritisation
- Event generation
- Intelligent notification selection

---

## Version 6.0.0

Output Manager

- Spatial Audio
- Haptic Feedback
- User notification management

---

# 19. Design Principles

Version 2.1.0 continues the core SixthSense philosophy.

- Observation before Decision.
- Layered Architecture.
- Stable Observation Interfaces.
- Modular Evolution.
- Single Sketch + Single Python Script compatibility with Arduino App Lab.

---

# 20. Summary

Version **2.1.0** transforms the Observation Engine from a static environmental representation into a dynamic observation system.

By introducing a rolling history buffer and sector-wise velocity estimation, the Observation Engine gains the ability to describe how the environment changes over time while remaining completely independent of decision making.

This version establishes the temporal foundation required for persistence estimation, context reasoning, intelligent attention management, and multimodal feedback in future releases.
