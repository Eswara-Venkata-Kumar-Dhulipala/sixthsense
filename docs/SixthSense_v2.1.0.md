# SixthSense v2.1.0

# Temporal ToF Observation Engine

**Version:** 2.1.0

**Status:** Design Specification

**Previous Version:** v2.0.0 – First Stable ToF Observation Engine

---

# 1. Overview

Version **2.1.0** extends the static observation engine introduced in v2.0.0.

Instead of treating every ToF frame independently, the Observation Engine now maintains temporal information across consecutive observations.

This enables the system to estimate **relative object motion** while keeping the Observation Layer independent from higher-level reasoning.

The Observation Engine still does **not** make decisions.

It only answers:

> **What changed since the previous observation?**

Future modules (Context Engine, Attention Engine, Output Manager) will decide **what that change means**.

---

# 2. Objectives

Version 2.1.0 introduces temporal reasoning into the Observation Layer.

Objectives:

- Maintain observation history.
- Estimate sector-wise velocity.
- Filter noisy velocity measurements.
- Extend the Observation API.
- Preserve backward compatibility.

---

# 3. Design Philosophy

The Observation Engine remains completely objective.

```
Sensor

↓

Observation

↓

Enhanced Observation

↓

Context

↓

Decision

↓

Output
```

The Observation Layer never classifies observations.

It only measures them.

---

# 4. Updated Architecture

```
VL53L5CX

↓

Arduino Sketch

↓

Bridge RPC

↓

Observation Builder

↓

ToFObservation

↓

History Buffer

↓

Instantaneous Velocity

↓

Velocity History

↓

Velocity Filter

↓

Enhanced ToFObservation

↓

Dashboard

↓

Future Context Engine
```

Notice that velocity estimation is now its own pipeline.

---

# 5. Processing Pipeline

For every incoming ToF frame:

```
Acquire Frame

↓

Build ToFObservation

↓

Estimate Instantaneous Velocity

↓

Update Velocity History

↓

Filter Velocity

↓

Update Observation

↓

Append Observation to History

↓

Publish Dashboard
```

This order is important.

The current observation is **not** added to the history until velocity estimation has completed.

---

# 6. Configuration

```python
HISTORY_CAPACITY = 20

VELOCITY_WINDOW = 5

MIN_VALID_DT = 0.05
```

---

## HISTORY_CAPACITY

Maximum observations retained.

Default

```
20
```

---

## VELOCITY_WINDOW

Number of velocity samples used for smoothing.

Default

```
5
```

---

## MIN_VALID_DT

Minimum elapsed time between two observations.

Default

```
0.05 seconds
```

---

# 7. Data Model

## SectorObservation

```python
SectorObservation

sector_id

sector_name

distance_mm

velocity_mmps
```

---

## ToFObservation

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

The Observation Engine stores complete observations.

```
Newest

↓

Observation

↓

Observation

↓

Observation

↓

...

↓

Oldest
```

The History Buffer is shared by all future temporal algorithms.

---

# 9. Velocity Estimation

Velocity estimation consists of three stages.

---

## Stage 1

Instantaneous Velocity

```
Previous Observation

↓

Current Observation

↓

Instantaneous Velocity
```

Formula

```
velocity =

(previous_distance - current_distance)

/

Δt
```

---

## Stage 2

Velocity History

Each sector maintains its own velocity history.

```
Sector 0

+120

+135

+140

+118

+126
```

---

## Stage 3

Velocity Filter

A moving average is applied **to velocity**, not distance.

```
Velocity History

↓

Moving Average

↓

Filtered Velocity
```

This produces smoother estimates while preserving object motion.

---

# 10. Dashboard

Each sector card becomes

```
Sector 0

Distance

345 mm

Velocity

+126 mm/s
```

---

## Velocity Colours

| State | Colour |
|--------|---------|
| Approaching | 🔴 Red |
| Stationary | 🟢 Green |
| Moving Away | 🔵 Blue |

---

# 11. Observation JSON

```json
{
  "sensor_id": "tof_01",
  "history_size": 20,
  "sectors": [
    {
      "sector_id": 0,
      "distance_mm": 338,
      "velocity_mmps": 126
    },
    {
      "sector_id": 1,
      "distance_mm": 331,
      "velocity_mmps": -22
    },
    {
      "sector_id": 2,
      "distance_mm": 347,
      "velocity_mmps": 0
    }
  ]
}
```

---

# 12. Validation

## Test 1

Static scene

Expected

```
Velocity ≈ 0 mm/s
```

---

## Test 2

Slow approach

Expected

Positive velocity

---

## Test 3

Slow retreat

Expected

Negative velocity

---

## Test 4

Lateral movement

Expected

Velocity ≈ 0

---

## Test 5

Rapid motion

Expected

Stable filtered velocity without spikes.

---

# 13. Out of Scope

The following remain outside Version 2.1.0.

- Persistence
- Confidence
- Camera Observation
- Context Engine
- Sensor Fusion
- Spatial Audio
- Haptic Feedback

---

# 14. Roadmap

## v2.2.0

Persistent ToF Observation Engine

- Persistence estimation
- Temporal stability
- Confidence score

---

## v3.0.0

Camera Observation Engine

- Object detection
- CameraObservation API

---

## v4.0.0

Context Engine

- Multi-sensor reasoning
- Scene understanding

---

## v5.0.0

Attention Engine

- Risk prioritisation
- Event generation

---

## v6.0.0

Output Manager

- Spatial Audio
- Haptic Feedback

---

# 15. Design Principles

SixthSense continues to follow these principles.

- Observation before Decision
- Layered Architecture
- Stable APIs
- Incremental Development
- Single Sketch + Single Python Script compatibility

---

# 16. Summary

Version **2.1.0** transforms the Observation Engine from a static sensing layer into a temporal sensing layer.

By introducing observation history, instantaneous velocity estimation, velocity history, and filtered velocity, the Observation Layer gains the ability to describe how the environment changes over time while remaining independent from semantic interpretation.

This architecture provides a stable foundation for persistence estimation, camera observations, context reasoning, attention management, and multimodal feedback in future releases.
