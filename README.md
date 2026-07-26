# SixthSense

> **A Modular Physical AI Perception Framework for Assistive Navigation**

<div align="center">

![Version](https://img.shields.io/badge/Version-v2.1.0-blue)
![Status](https://img.shields.io/badge/Status-Active-success)
![Platform](https://img.shields.io/badge/Platform-Arduino%20UNO%20Q-red)
![Sensor](https://img.shields.io/badge/Sensor-VL53L5CX-brightgreen)
![License](https://img.shields.io/badge/License-MPL--2.0-yellow)

</div>

---

# Overview

**SixthSense** is an open-source Physical AI project that explores how wearable systems can perceive and understand their surroundings using Time-of-Flight (ToF) sensors.

Instead of directly converting raw sensor measurements into feedback, SixthSense follows an **Observation-First Architecture**. Raw sensor data is first transformed into structured observations, which are then interpreted by higher-level reasoning modules.

This layered approach keeps perception, reasoning, decision-making, and user feedback independent, making the system easier to develop, validate, and extend.

The long-term goal is to build a wearable assistive navigation system capable of understanding the environment and providing intuitive guidance to visually impaired users.

---

# Current Release

## **v2.1.0 — Temporal ToF Observation Engine**

Current implementation provides:

- Real-time 8×8 Time-of-Flight sensing
- Three-sector obstacle observation
- Temporal observation history
- Per-sector velocity estimation
- Motion state classification
- Velocity smoothing
- Interactive web dashboard
- Live JSON observation viewer

---

# Current Status

| Item | Status |
|------|--------|
| Version | **v2.1.0** |
| Milestone | Temporal ToF Observation Engine |
| Hardware | Arduino UNO Q + VL53L5CX |
| ToF Sensors | 1 *(Planned: 6)* |
| Dashboard | ✅ Available |
| Observation History | ✅ |
| Velocity Estimation | ✅ |
| Motion Classification | ✅ |
| Context Engine | 🚧 Planned |
| Attention Engine | 🚧 Planned |
| Feedback Engine | 🚧 Planned |

---

# Dashboard

The current prototype includes a real-time web dashboard for visualizing sensor observations during development.

Current dashboard features include:

- Live 8×8 heatmap
- Three-sector observation panel
- Distance visualization
- Velocity visualization
- Motion state visualization
- Live JSON observation viewer
- Sensor and connection status
- Frame counter and FPS

<img width="1152" height="586" alt="demo_trimmed_v_2_1_0" src="https://github.com/user-attachments/assets/72230cf2-6e47-4ef2-8f9e-a5721f7f68c5" />

---

# Why SixthSense?

Most obstacle detection systems answer a single question:

> **"Where is the obstacle?"**

SixthSense aims to answer richer questions:

- What does each sensor observe?
- Is an object approaching or moving away?
- Which observations remain stable over time?
- What is happening around the user?
- Which information deserves the user's attention?
- How should that information be communicated?

By separating perception from reasoning, SixthSense builds a foundation that can evolve from simple obstacle detection toward intelligent environmental understanding.

---

# Design Philosophy

SixthSense is developed incrementally.

Each software release introduces one major architectural capability while preserving the existing software foundation.

The project follows four guiding principles:

- **Observation First** — Convert raw sensor data into structured observations.
- **Modularity** — Keep every architectural layer independent.
- **Incremental Evolution** — Add one capability at a time through stable releases.
- **Scalability** — Design components that naturally extend to multiple sensors.

Detailed implementation and architectural decisions for each release are documented separately in the `docs/` directory.

# Architecture

SixthSense follows an **Observation-First Architecture**, where every layer has a single, well-defined responsibility.

Rather than converting sensor measurements directly into user feedback, the system progressively transforms information into increasingly meaningful representations.

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

This separation keeps perception, reasoning, prioritization, and feedback independent, making the software easier to extend and maintain.

---

# Current Prototype

The current prototype validates the **Temporal ToF Observation Engine** using a single **SparkFun VL53L5CX Time-of-Flight sensor** connected to an **Arduino UNO Q**.

Current runtime architecture:

```text
VL53L5CX Sensor
        │
        ▼
Arduino UNO Q
        │
        ▼
Arduino Bridge RPC
        │
        ▼
Python Backend
        │
        ▼
Observation Engine
        │
        ▼
Interactive Dashboard
```

Although the current prototype uses a single ToF sensor, the architecture is designed to scale to six independent sensors without redesigning the Observation Engine.

---

# Observation Engine

The Observation Engine is the core perception component of SixthSense.

Its responsibility is to convert raw Time-of-Flight frames into structured observations.

It performs **perception only**.

Environmental understanding, prioritization, and user feedback are intentionally handled by higher-level architectural layers.

Current capabilities include:

- Three-sector observation model
- Observation history
- Temporal processing
- Velocity estimation
- Motion state classification
- Velocity smoothing

The output of the Observation Engine is a structured **ToFObservation**, which serves as the common interface between perception and future reasoning modules.

For implementation details, see:

```text
docs/SixthSense_v2.1.0.md
```

---

# ToFObservation

Every processed sensor frame generates a single **ToFObservation**.

Each observation contains:

- Timestamp
- Frame number
- Sensor identifier
- Observation history size
- Three sector observations

Each sector currently provides:

- Distance
- Relative velocity
- Motion state

This observation model allows higher-level software layers to work with structured information rather than raw sensor measurements.

---

# Current Capabilities

Version **v2.1.0** provides the following capabilities:

| Capability | Status |
|------------|:------:|
| Static obstacle observation | ✅ |
| Temporal observation history | ✅ |
| Velocity estimation | ✅ |
| Motion state classification | ✅ |
| Velocity smoothing | ✅ |
| Interactive dashboard | ✅ |
| Live JSON observations | ✅ |
| Multi-sensor support | 🚧 Planned |
| Context reasoning | 🚧 Planned |
| Attention model | 🚧 Planned |
| User feedback engine | 🚧 Planned |

---

# Current Scope

The current implementation intentionally focuses on **perception**.

It does **not** attempt to:

- Interpret the surrounding environment
- Estimate user intent
- Prioritize observations
- Generate navigation guidance
- Produce haptic or audio feedback

These capabilities will be introduced progressively through the Context, Attention, and Feedback Engines in future releases.

# Hardware & Software

## Current Hardware

The current prototype uses a minimal hardware configuration to validate the Observation Engine before scaling to a complete wearable system.

| Component | Quantity |
|-----------|---------:|
| Arduino UNO Q | 1 |
| SparkFun VL53L5CX Time-of-Flight Sensor | 1 |
| Qwiic JST Cable | 1 |
| USB-C Cable | 1 |

Future releases will expand the prototype to six Time-of-Flight sensors while preserving the same Observation Engine architecture.

<img width="960" height="1280" alt="Arduino UNO Q with VL53L5CX" src="https://github.com/user-attachments/assets/4968e3f6-217f-41ab-af97-992710e7f006" />
---

## Software Stack

| Layer | Technology |
|--------|------------|
| Firmware | Arduino Sketch (C++) |
| Backend | Python |
| Frontend | HTML, CSS, JavaScript |
| Communication | Arduino Bridge RPC |
| Dashboard | Arduino App Lab WebUI |

---

# Repository Structure

```text
SixthSense/
│
├── README.md
├── CHANGELOG.md
├── LICENSE
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
    ├── SixthSense_v2.0.0.md
    ├── SixthSense_v2.1.0.md
    └── ...
```

The **README** provides a high-level overview of the project, while the `docs/` directory contains detailed design documents for individual releases.

---

# Development

SixthSense follows an incremental development approach.

Each release introduces **one major architectural capability**, ensuring every version is independently functional, testable, and documented before moving to the next milestone.

Development is performed on the `develop` branch. Stable releases are merged into `main` and published as GitHub Releases.

---

# Roadmap

| Version | Milestone | Status |
|----------|-----------|:------:|
| **v2.0.0** | Static ToF Observation Engine | ✅ |
| **v2.1.0** | Temporal ToF Observation Engine | ✅ |
| **v2.2.0** | Persistent ToF Observation Engine | 🚧 |
| **v3.0.0** | Six ToF Sensor Integration | 🚧 |
| **v4.0.0** | Context Engine | 🚧 |
| **v5.0.0** | Attention Engine | 🚧 |
| **v6.0.0** | Feedback Engine | 🚧 |
| **v7.0.0** | Complete SixthSense Prototype | 🎯 |

---

## Roadmap Overview

```text
v2.0.0
Static Observation
        │
        ▼
v2.1.0
Temporal Observation
        │
        ▼
v2.2.0
Persistent Observation
        │
        ▼
v3.0.0
Six ToF Sensors
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
Complete Prototype
```

---

# Future Direction

The current release establishes a robust **Observation Engine** capable of generating structured temporal observations from a single Time-of-Flight sensor.

Future releases will extend this foundation by:

- Scaling from one to six ToF sensors.
- Building environmental understanding through the **Context Engine**.
- Prioritizing observations using the **Attention Engine**.
- Delivering intuitive haptic and audio guidance through the **Feedback Engine**.

The long-term objective is to develop a modular Physical AI perception framework that separates perception, understanding, prioritization, and feedback into independent architectural layers.

---

# Contributing

Contributions are welcome.

Areas where contributions can have the greatest impact include:

- Time-of-Flight perception algorithms
- Embedded firmware
- Python backend
- Dashboard improvements
- Documentation
- Testing and validation

If you plan to contribute:

1. Fork the repository.
2. Create a feature branch from `develop`.
3. Implement and test your changes.
4. Update documentation where applicable.
5. Submit a Pull Request.

For bug reports and feature requests, please use **GitHub Issues**.

For architectural discussions and ideas, please use **GitHub Discussions**.

# Documentation

The repository documentation is organized into two levels.

## README

This document provides:

- Project overview
- Current implementation
- Architecture
- Setup instructions
- Development roadmap

## Design Documents

Detailed implementation notes for each release are available in the `docs/` directory.

```text
docs/

├── SixthSense_v2.0.0.md

├── SixthSense_v2.1.0.md

├── SixthSense_v2.2.0.md

└── ...
```

These documents describe the architecture, design decisions, implementation details, and validation of each release.

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

This project builds upon the excellent open-source ecosystem.

Special thanks to:

- Arduino
- Arduino App Lab
- SparkFun Electronics
- STMicroelectronics
- Python Community
- Open Source Community

Their hardware, software, libraries, and documentation make projects like SixthSense possible.

---

# Contact

Questions, suggestions, bug reports, and feature requests are always welcome.

Please use:

- GitHub Issues
- GitHub Discussions
- Pull Requests

Constructive feedback and contributions are greatly appreciated.

