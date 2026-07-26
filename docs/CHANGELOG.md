# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by **Keep a Changelog**, and the project follows **Semantic Versioning**.

---

# [2.1.0] - 2026-07-26

## Overview

Version **2.1.0** introduces the **Temporal ToF Observation Engine**, extending the static observation capabilities introduced in v2.0.0.

The Observation Engine now maintains temporal observation history, estimates relative obstacle velocity, classifies motion states, and provides enhanced visualization through an improved real-time dashboard.

This release establishes the foundation for future Context, Attention, and Feedback Engines while preserving the modular Observation-First Architecture.

---

## Added

### Observation Engine

- Temporal observation history.
- Relative velocity estimation.
- Motion state classification.
- Velocity smoothing.
- Enhanced `ToFObservation` data model.
- Observation history management.
- Temporal processing pipeline.

### Dashboard

- Three-sector observation cards.
- Live velocity visualization.
- Motion state indicators.
- Enhanced JSON observation viewer.
- Improved dashboard layout.
- Improved responsive UI.

### Documentation

- Redesigned project README.
- New **Software Architecture & Design Document** (`SixthSense_v2.1.0.md`).
- Updated project documentation structure.
- Expanded architectural documentation.
- Updated release documentation.

---

## Changed

### Observation Engine

- Extended the static Observation Engine introduced in v2.0.0.
- Refactored observation generation pipeline.
- Improved software modularity.
- Improved processing pipeline readability.
- Improved separation between perception and future reasoning layers.

### Dashboard

- Redesigned dashboard layout.
- Improved sector visualization.
- Improved sensor status display.
- Improved observation rendering.
- Improved real-time updates.

### Software Architecture

- Reinforced Observation-First Architecture.
- Standardized observation interfaces.
- Improved processing pipeline organization.
- Improved scalability for future multi-sensor support.

---

## Fixed

- Fixed WebUI Socket.IO event handling.
- Fixed browser initialization issues.
- Fixed dashboard rendering inconsistencies.
- Fixed observation serialization issues.
- Fixed sector visualization alignment.
- Fixed UI responsiveness.
- Fixed sensor initialization handling.
- Fixed application startup issues.
- Fixed observation update synchronization.

---

## Performance

- Reduced observation processing overhead.
- Improved dashboard refresh performance.
- Improved velocity estimation stability.
- Optimized temporal processing.
- Improved real-time responsiveness.

---

## Compatibility

### Hardware

- Arduino UNO Q
- SparkFun VL53L5CX Time-of-Flight Sensor

### Software

- Arduino App Lab
- Python Backend
- Web Dashboard

---

## Known Limitations

Current release supports:

- One Time-of-Flight sensor.
- Relative motion estimation only.
- Observation generation.
- Dashboard visualization.

Current release does not yet provide:

- Multi-sensor perception.
- Context generation.
- Attention modelling.
- Navigation planning.
- Haptic feedback.
- Audio feedback.

These capabilities are planned for future releases.

---

# [2.0.0] - 2026-07-01

## Initial Release

### Added

- Static ToF Observation Engine.
- Three-sector obstacle observation.
- Live Time-of-Flight heatmap.
- Interactive web dashboard.
- JSON observation output.
- Modular Observation-First software architecture.
- Arduino UNO Q integration.
- SparkFun VL53L5CX integration.
