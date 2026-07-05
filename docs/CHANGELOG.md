# SixthSense

## Changelog

This document records the history of every software release.

---

# v2.0.0

Status

🚧 In Development

---

## Added

### Architecture

- Layered software architecture
- Configuration Module
- Versioning strategy
- Documentation standards
- Software Design Document

### Observation Engine

- ToF Observation Engine framework
- Rolling history buffer
- Three-sector architecture
- ToFObservation data model

### Dashboard

- Sensor Information panel
- ToF Observation panel
- Heatmap panel
- Observation JSON panel

### Repository

- Standard folder structure
- Documentation folder
- README
- CHANGELOG

---

## Changed

- Project reorganized into layered architecture.
- Observation-first development strategy adopted.
- Sensor-independent sector naming (`Sector 0`, `Sector 1`, `Sector 2`) introduced.

---

## Fixed

- Standardized software responsibilities between:
  - `sketch.ino`
  - `main.py`
  - `app.js`

---

# Planned Releases

## v2.1.0

Velocity Engine

Planned

- Distance history
- Velocity estimation
- Velocity dashboard

---

## v2.2.0

Motion Engine

Planned

- Static detection
- Approaching detection
- Moving away detection

---

## v2.3.0

Persistence Engine

Planned

- Persistence counter
- Stable obstacle filtering

---

## v2.4.0

Confidence Engine

Planned

- Confidence estimation
- Sensor stability
- Noise rejection

---

## v3.0.0

Camera Observation Engine

Planned

- Object detection
- CameraObservation
- Bounding boxes
- Camera sectors
- Motion estimation

---

## v4.0.0

Context Engine

Planned

- Observation fusion
- Attention prioritization
- Global sector mapping
- AttentionEvent generation

---

## v5.0.0

Output Manager

Planned

- Haptic feedback
- Speech synthesis
- Spatial audio
- User notification engine

---

# Long-Term Goal

Final SixthSense system

- 6 × VL53L5CX ToF sensors
- 2 × USB cameras
- 4 × vibration motors
- Stereo earbuds
- Observation-driven architecture
- Context-aware attention engine
- Near 360° situational awareness