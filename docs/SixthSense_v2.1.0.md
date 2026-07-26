# SixthSense v2.1.0

> **Temporal ToF Observation Engine**

| Item | Value |
|------|-------|
| Project | SixthSense |
| Document | Software Architecture & Design Document |
| Software Version | v2.1.0 |
| Document Version | 1.0 |
| Status | Released |
| Last Updated | July 2026 |
| Author | Eswara Venkata Kumar Dhulipala |

## Release History
| Software Version | Major Capability |
|-----------------|------------------|
| v2.0.0 | Static Observation Engine |
| v2.1.0 | Temporal Observation Engine |

---

# Table of Contents

1. Introduction
2. Objectives
3. Background
4. Motivation
5. Scope
6. Design Philosophy

7. High-Level Architecture
8. Observation Engine Overview
9. Observation Processing Stages
10. Temporal Observation History
11. Temporal Processing Strategy

12. Velocity Estimation
13. Velocity Smoothing
14. Motion State Classification
15. ToFObservation Data Model
16. Software Architecture

17. Dashboard Design
18. Software Organization
19. Validation Strategy
20. Design Decisions
21. Current Limitations

22. Runtime Execution Flow
23. Data Flow
24. Computational Characteristics
25. Reliability Considerations
26. Scalability
27. Extensibility
28. Design Trade-offs

29. Software Architecture Principles
30. Data Model Design
31. Interface Contracts
32. Non-Functional Requirements
33. Error Handling Strategy
34. Architectural Rationale

35. Evolution of the Observation Engine
36. Observation Model Evolution
37. Multi-Sensor Architecture
38. Context Engine Interface
39. Architectural Constraints
40. Assumptions
41. Dependencies
42. Design Summary

43. Architectural Decisions
44. Alternative Designs Considered
45. Lessons Learned
46. Compatibility with Future Releases

47. Engineering Considerations
48. Future Evolution
49. Validation Results
50. Key Contributions

---

# 1. Introduction

Version **v2.1.0** introduces the **Temporal ToF Observation Engine**, representing the second architectural milestone of the SixthSense project.

The previous release (**v2.0.0**) demonstrated that raw Time-of-Flight (ToF) measurements could be transformed into structured observations describing the nearest obstacle within three logical sectors.

Although this established a stable perception pipeline, every observation was generated independently. The system had no understanding of how the environment changed over time.

Version **v2.1.0** addresses this limitation by introducing temporal perception.

Instead of treating each sensor frame as an isolated measurement, the Observation Engine now maintains a short observation history and uses it to estimate the relative motion of observed obstacles.

As a result, every observation contains both spatial and temporal information.

This document describes the design, architecture, implementation, and validation of the Temporal ToF Observation Engine.

---

# 2. Objectives

The primary objective of v2.1.0 is to extend the Observation Engine with temporal reasoning while preserving the modular architecture established in v2.0.0.

Specifically, this release aims to:

- Preserve the existing Observation Engine architecture.
- Introduce temporal observation history.
- Estimate relative obstacle velocity.
- Classify obstacle motion.
- Reduce velocity noise through filtering.
- Extend the existing `ToFObservation` data model.
- Maintain compatibility with future architectural layers.

Equally important are the objectives that are intentionally **out of scope** for this release.

Version **v2.1.0** does **not** attempt to:

- Understand the surrounding environment.
- Fuse observations from multiple sensors.
- Predict future object motion.
- Estimate user motion.
- Prioritize observations.
- Generate navigation instructions.
- Produce haptic or audio feedback.

These responsibilities belong to future architectural layers and are deliberately excluded to maintain clear separation of responsibilities.

---

# 3. Background

The SixthSense project follows an **Observation-First Architecture**.

Rather than converting raw sensor measurements directly into user feedback, sensor data is progressively transformed into increasingly meaningful representations.

The complete long-term architecture is shown below.

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

Each architectural layer has a single responsibility.

The Observation Engine performs perception.

The Context Engine performs environmental understanding.

The Attention Engine prioritizes contextual information.

The Feedback Engine determines how information should be communicated to the user.

This layered architecture minimizes coupling between components and allows each layer to evolve independently.

---

# 4. Motivation

Version **v2.0.0** successfully generated structured observations from raw ToF frames.

However, every observation represented only the current sensor state.

For example, consider the following two observations generated one second apart.

```text
Observation A

Center Distance = 1200 mm
```

```text
Observation B

Center Distance = 800 mm
```

While it is obvious that the observed distance has decreased, v2.0.0 had no mechanism to determine:

- How quickly the distance changed.
- Whether the object was approaching.
- Whether the object was moving away.
- Whether the change resulted from object motion or sensor motion.

Each observation existed independently.

There was no concept of temporal continuity.

Without temporal information, higher-level reasoning modules would have very limited understanding of dynamic environments.

Version **v2.1.0** introduces the minimum temporal capabilities required to address this limitation while preserving the existing Observation Engine architecture.

---

# 5. Scope

The scope of this release is intentionally limited to extending the Observation Engine.

The following capabilities are included.

## Included

- Observation history
- Velocity estimation
- Motion state classification
- Velocity smoothing
- Enhanced observation model
- Dashboard updates
- JSON interface updates

The following capabilities are intentionally deferred.

## Excluded

- Multi-sensor observation
- Context generation
- Object tracking
- Object identification
- Environmental reasoning
- Attention modelling
- User feedback generation

Restricting the scope in this way allows each architectural milestone to remain independently testable while reducing implementation complexity.

---

# 6. Design Philosophy

The design of v2.1.0 follows several guiding principles established at the beginning of the project.

### Observation Before Interpretation

The Observation Engine should describe **what the sensor observes**, not **what the environment means**.

Interpretation belongs to the Context Engine.

---

### Incremental Evolution

The existing architecture should be extended rather than replaced.

Every new capability should integrate naturally with previous releases.

---

### Stable Interfaces

Higher-level software layers should interact only with `ToFObservation`.

Internal implementation details should remain hidden.

This allows the Observation Engine to evolve without affecting downstream modules.

---

### Independent Components

Every major software component should perform one clearly defined task.

This reduces coupling and improves maintainability.

These principles guide every design decision presented throughout this document.

# 7. High-Level Architecture

Version **v2.1.0** preserves the architectural layering introduced in v2.0.0 while extending the Observation Engine with temporal perception.

The overall software architecture remains unchanged.

```text
                    Raw ToF Frame
                          │
                          ▼
                 Observation Engine
                          │
                    ToFObservation
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

Only the Observation Engine is implemented in this release.

The Context, Attention, and Feedback Engines remain architectural placeholders for future releases.

This decision ensures that each release introduces a single major capability while preserving stable interfaces between architectural layers.

---

# 8. Observation Engine Overview

The Observation Engine is responsible for transforming raw Time-of-Flight sensor measurements into structured observations.

Its responsibility is intentionally limited to **perception**.

The Observation Engine does not attempt to:

- Interpret the environment.
- Understand user intent.
- Track objects.
- Predict future motion.
- Generate navigation instructions.

Instead, it answers a single question:

> **"What does this sensor observe right now?"**

This separation allows higher-level software layers to build increasingly sophisticated reasoning without modifying the perception layer.

---

## Observation Pipeline

The Observation Engine processes every incoming ToF frame using the following pipeline.

```text
Raw 8×8 ToF Frame
        │
        ▼
Distance Validation
        │
        ▼
Sector Extraction
        │
        ▼
Observation Builder
        │
        ▼
Observation History Update
        │
        ▼
Velocity Estimation
        │
        ▼
Velocity Smoothing
        │
        ▼
Motion Classification
        │
        ▼
ToFObservation
```

Each stage performs a single well-defined task.

This modular pipeline makes the Observation Engine easier to test, extend, and maintain.

---

# 9. Observation Processing Stages

## 9.1 Distance Validation

The raw sensor frame may contain invalid or saturated distance values.

The first stage validates incoming measurements before further processing.

Typical validation includes:

- Invalid distance detection
- Maximum range checking
- Missing measurement handling

Only validated distances are forwarded to subsequent stages.

---

## 9.2 Sector Extraction

The current prototype divides the 8×8 sensor frame into three logical sectors:

```text
+-----------------------------+
| Left (Sector 0) | Center (Sector 1) | Right (Sector 2) |
+-----------------------------+
```

Each sector is represented by a single distance measurement.

The current implementation uses the nearest valid distance within each sector as the representative obstacle distance.

This provides a simple yet robust abstraction for obstacle perception while remaining computationally efficient.

Future releases may replace or extend this strategy without changing the external observation interface.

---

## 9.3 Observation Builder

After sector distances have been computed, the Observation Builder creates a structured observation.

Each observation contains:

- Timestamp
- Frame number
- Sensor identifier
- Three sector observations

At this stage, observations contain only spatial information.

Temporal information is added in subsequent processing stages.

---

# 10. Temporal Observation History

The primary enhancement introduced in v2.1.0 is the addition of temporal observation history.

Rather than processing every frame independently, the Observation Engine now maintains a fixed-size history of previous observations.

```text
Current Observation

        │

        ▼

+----------------------+

Newest Observation

Previous Observation

Previous Observation

...

Oldest Observation

+----------------------+
```

The history acts as a short-term memory that enables temporal analysis.

Without this history, velocity estimation would not be possible.

---

## History Size

The Observation Engine stores a configurable number of previous observations.

The history length is selected to balance:

- Temporal resolution
- Memory usage
- Computational cost
- Noise reduction

The current implementation uses a history size that provides stable velocity estimates while maintaining real-time performance on the target hardware.

---

## Design Decision

A bounded history was selected instead of storing every observation indefinitely.

Advantages include:

- Constant memory usage
- Predictable execution time
- Low computational overhead
- Suitable for embedded systems

Older observations are discarded automatically as new observations arrive.

This rolling history provides sufficient temporal information for the current release while remaining scalable for future extensions.

---

# 11. Temporal Processing Strategy

Temporal processing in v2.1.0 is intentionally conservative.

The Observation Engine estimates only **relative motion** between the sensor and observed obstacles.

It does not attempt to determine:

- Whether the user is moving.
- Whether the obstacle is moving.
- Why the measured distance changed.

For example, if the measured distance decreases over time, the Observation Engine reports:

```text
Motion State

Approaching
```

This statement is always correct because it describes the observed change in relative distance.

Determining whether the user walked toward a wall or the wall moved toward the user requires additional environmental reasoning and is therefore deferred to the future Context Engine.

Maintaining this separation preserves the single responsibility of the Observation Engine and prevents perception from becoming tightly coupled with higher-level reasoning.

# 12. Velocity Estimation

The introduction of velocity estimation is the primary functional enhancement in v2.1.0.

While v2.0.0 described the spatial state of the environment, v2.1.0 additionally describes how that environment changes over time.

Velocity is estimated independently for each observation sector.

---

## Relative Velocity

The Observation Engine estimates **relative radial velocity**.

Relative radial velocity describes the rate of change of distance between the sensor and the nearest observed obstacle.

Mathematically,

```text
Velocity = ΔDistance / ΔTime
```

where

- ΔDistance is the change in observed distance
- ΔTime is the elapsed time between observations

The Observation Engine intentionally estimates only relative velocity.

It does not distinguish whether the change in distance is caused by:

- user motion,
- obstacle motion,
- or both.

Determining the cause of relative motion requires additional contextual information and is outside the scope of this release.

---

## Per-Sector Estimation

Velocity is computed independently for each logical sector.

```text
Left Sector (Sector 0)

Distance History

↓

Relative Velocity


Center Sector (Sector 1)

Distance History

↓

Relative Velocity


Right Sector (Sector 2)

Distance History

↓

Relative Velocity
```

This independent processing simplifies the software architecture and allows each sector to be analysed separately.

Future multi-sensor versions will preserve this design.

---

# 13. Velocity Smoothing

Raw velocity estimates naturally contain measurement noise.

Small fluctuations in measured distance can produce unstable velocity estimates even when the environment is static.

To improve stability, v2.1.0 applies temporal smoothing before classifying motion.

The objectives of smoothing are:

- reduce sensor noise
- improve motion stability
- avoid rapid state oscillations
- improve dashboard readability

The filtering strategy is intentionally lightweight to preserve real-time performance.

Future releases may introduce more advanced filtering techniques if required.

---

# 14. Motion State Classification

Once the smoothed velocity has been computed, each sector is classified into a discrete motion state.

Current motion states are:

| Motion State | Description |
|--------------|-------------|
| **Approaching** | Relative distance decreasing |
| **Stationary** | Relative distance approximately constant |
| **Receding** | Relative distance increasing |

The Observation Engine performs only classification.

It does not infer why the motion occurred.

For example,

```text
Approaching
```

means

> The observed distance is decreasing.

It does **not** mean

> The obstacle is moving toward the user.

This distinction is fundamental to the Observation-First Architecture.

Future versions will use the Context Engine to interpret these observations.

---

# 15. ToFObservation Data Model

The structured observation generated by the Observation Engine is represented by the `ToFObservation` model.

This model forms the interface between perception and all future architectural layers.

---

## Observation Structure

```text
ToFObservation

├── Timestamp

├── Frame Number

├── Sensor ID

├── Observation History Size

└── Sectors

        ├── Left (Sector 0)

        ├── Center (Sector 1)

        └── Right (Sector 2)
```

---

## Sector Observation

Each sector contains the following information.

```text
SectorObservation

├── Distance

├── Relative Velocity

└── Motion State
```

This structure intentionally contains only information that can be directly derived from the Time-of-Flight sensor measurements.

No environmental interpretation is included.

---

## Design Rationale

The `ToFObservation` model was designed to satisfy several objectives.

### Simplicity

Every observation should be easy to understand and serialize.

---

### Extensibility

Future releases should be able to extend the observation model without breaking existing interfaces.

---

### Sensor Independence

Higher-level software should consume observations rather than raw sensor measurements.

This allows future sensor technologies to produce compatible observation models.

---

### Stable Interface

The Context Engine should depend only on the observation interface.

Changes to the internal implementation of the Observation Engine should not require modifications to downstream software.

---

# 16. Software Architecture

The software architecture introduced in v2.1.0 follows a modular design.

```text
Raw ToF Frame

        │

        ▼

Distance Validation

        │

        ▼

Sector Extraction

        │

        ▼

Observation Builder

        │

        ▼

Observation History

        │

        ▼

Velocity Estimation

        │

        ▼

Velocity Smoothing

        │

        ▼

Motion Classification

        │

        ▼

ToFObservation
```

Each processing stage has a single responsibility.

This modular organization simplifies:

- testing,
- maintenance,
- future enhancements,
- and software reuse.

Rather than implementing one large algorithm, the Observation Engine is constructed from small, well-defined processing stages.

---

# Architectural Benefits

The modular pipeline adopted in v2.1.0 provides several advantages.

- Clear separation of responsibilities.
- Improved readability.
- Independent unit testing of processing stages.
- Easier debugging.
- Simplified future enhancements.

This design also aligns with the long-term goal of scaling from a single Time-of-Flight sensor to multiple independent Observation Engines without redesigning the perception pipeline.

# 17. Dashboard Design

The interactive dashboard is the primary visualization and validation tool for the Observation Engine.

Rather than serving as part of the final wearable system, the dashboard provides a real-time view of the perception pipeline during development.

It enables developers to observe how raw sensor measurements are transformed into structured observations and to verify the behavior of the Observation Engine under different environmental conditions.

---

## Dashboard Objectives

The dashboard was designed with the following objectives:

- Visualize the live Time-of-Flight sensor data.
- Display structured observations generated by the Observation Engine.
- Assist in debugging and validation.
- Demonstrate the capabilities introduced in each software release.
- Provide a platform for future visualization enhancements.

The dashboard is intentionally independent of the Observation Engine.

It consumes the generated `ToFObservation` objects without requiring knowledge of the internal implementation.

---

## Current Dashboard Features

Version **v2.1.0** includes the following dashboard capabilities.

### Sensor Visualization

- Live 8×8 Time-of-Flight heatmap
- Three-sector distance visualization
- Sensor connection status

### Observation Visualization

- Distance values
- Relative velocity
- Motion state
- Frame number
- Timestamp

### System Information

- Application version
- Sensor information
- Refresh rate
- System status

### Developer Tools

- Live JSON observation viewer
- Debug information
- Performance statistics

The dashboard serves as a validation interface and is not intended to represent the final user experience.

Future releases will gradually shift from visual debugging toward wearable feedback mechanisms.

---

# 18. Software Organization

The implementation of v2.1.0 follows a modular software organization.

Each module is responsible for one clearly defined task.

```text
Raw Sensor Frame
        │
        ▼
Distance Processing
        │
        ▼
Observation Generation
        │
        ▼
Temporal Processing
        │
        ▼
Motion Analysis
        │
        ▼
Observation Output
        │
        ▼
Dashboard
```

This organization minimizes coupling between processing stages and simplifies future enhancements.

As new capabilities are introduced, they can be integrated by extending individual modules rather than redesigning the entire Observation Engine.

---

# 19. Validation Strategy

The objective of validation is to verify that the Observation Engine produces consistent and reliable observations under normal operating conditions.

Validation focuses on the correctness of generated observations rather than application-specific behavior.

---

## Functional Validation

The following aspects were verified during development.

### Observation Generation

Verify that every valid sensor frame produces exactly one `ToFObservation`.

---

### Distance Processing

Verify that sector distances correctly represent the nearest valid obstacle within each logical sector.

---

### Temporal Processing

Verify that observation history updates correctly for every processed frame.

---

### Velocity Estimation

Verify that relative velocity changes consistently with changes in observed distance.

---

### Motion Classification

Verify correct classification of:

- Approaching
- Stationary
- Receding

under representative test scenarios.

---

### Dashboard

Verify that generated observations are displayed correctly and updated in real time.

---

# 20. Design Decisions

Several important architectural decisions were made during the development of v2.1.0.

---

## Decision 1

### Observation Before Interpretation

The Observation Engine reports only measurable quantities.

It does not attempt to interpret the surrounding environment.

This responsibility is intentionally deferred to the future Context Engine.

This separation preserves the single responsibility of the Observation Engine and simplifies future architectural evolution.

---

## Decision 2

### Relative Motion Only

Velocity is represented as **relative velocity**.

The Observation Engine reports changes in sensor-to-obstacle distance.

It does not distinguish between:

- user motion,
- obstacle motion,
- or combined motion.

This decision keeps the Observation Engine independent of additional sensing modalities and avoids introducing assumptions that cannot be supported by the available data.

---

## Decision 3

### Fixed Observation Structure

Every observation follows the same data model regardless of the observed environment.

A consistent observation structure simplifies downstream processing and allows future architectural layers to operate on a stable interface.

---

## Decision 4

### Modular Processing Pipeline

The Observation Engine is implemented as a sequence of independent processing stages.

This approach provides:

- improved readability,
- easier debugging,
- simpler testing,
- straightforward extensibility.

Future processing stages can be added without redesigning the existing pipeline.

---

# 21. Current Limitations

Version **v2.1.0** intentionally focuses on perception.

The following limitations are acknowledged.

### Single Sensor

The current implementation processes observations from one Time-of-Flight sensor.

Multi-sensor perception will be introduced in v3.0.0.

---

### Relative Motion

Motion estimates describe only changes in relative distance.

The Observation Engine cannot determine the cause of the observed motion.

---

### No Environmental Understanding

The Observation Engine does not recognize:

- rooms,
- corridors,
- walls,
- doors,
- people,
- or other semantic entities.

These capabilities belong to the future Context Engine.

---

### No Prediction

The Observation Engine describes the current state of the environment.

It does not predict future motion or estimate future obstacle positions.

---

### No User Feedback

Version **v2.1.0** ends with structured observations.

User interaction through haptic or audio feedback will be introduced in future releases.

---

# Summary

Despite these limitations, version **v2.1.0** successfully establishes the temporal perception capabilities required for future architectural layers.

By maintaining a clear separation between perception and reasoning, the Observation Engine provides a stable foundation upon which increasingly sophisticated contextual understanding can be built.

# 22. Runtime Execution Flow

The Observation Engine executes continuously while the application is running.

For every incoming Time-of-Flight frame, the same processing sequence is performed.

The runtime execution flow is illustrated below.

```text
Receive Raw ToF Frame
          │
          ▼
 Validate Distance Measurements
          │
          ▼
   Divide Frame into Sectors
          │
          ▼
 Generate Spatial Observation
          │
          ▼
 Update Observation History
          │
          ▼
 Estimate Relative Velocity
          │
          ▼
 Smooth Velocity Estimates
          │
          ▼
 Classify Motion State
          │
          ▼
 Generate ToFObservation
          │
          ▼
 Publish Observation
          │
          ▼
 Update Dashboard
```

The execution sequence remains identical for every processed frame, resulting in predictable execution time and deterministic behavior.

---

# 23. Data Flow

The Observation Engine transforms raw sensor measurements into structured observations through a sequence of processing stages.

```text
Raw Sensor Frame

        │

        ▼

Validated Distances

        │

        ▼

Sector Distances

        │

        ▼

Spatial Observation

        │

        ▼

Temporal Observation

        │

        ▼

ToFObservation

        │

        ▼

Dashboard
```

Each processing stage enriches the available information while preserving the outputs generated by previous stages.

This progressive transformation is one of the fundamental principles of the Observation-First Architecture.

---

# 24. Computational Characteristics

Version **v2.1.0** was designed for real-time execution on resource-constrained embedded platforms.

Several implementation decisions support this objective.

## Fixed Processing Pipeline

Every incoming frame follows exactly the same sequence of operations.

The execution path does not depend on the observed environment.

This simplifies testing and provides predictable execution time.

---

## Bounded Memory Usage

Observation history is maintained using a fixed-size rolling buffer.

Memory consumption therefore remains constant regardless of application runtime.

---

## Lightweight Processing

The Observation Engine performs only local computations on the current observation and a limited history.

No global optimization or computationally intensive algorithms are required.

This keeps processing latency low while maintaining sufficient temporal information for motion estimation.

---

# 25. Reliability Considerations

Reliable observations are essential because every future architectural layer depends upon them.

Several design decisions contribute to the robustness of the Observation Engine.

## Invalid Measurement Handling

Invalid sensor measurements are identified before observation generation.

Invalid values are prevented from propagating through the processing pipeline whenever possible.

---

## Observation Consistency

Every processed frame generates observations using the same processing stages and data model.

This consistency simplifies downstream software development and validation.

---

## Stable Interfaces

The external observation interface remains independent of the internal implementation.

Future improvements to velocity estimation or filtering can therefore be introduced without affecting higher-level architectural layers.

---

# 26. Scalability

Although version **v2.1.0** supports a single Time-of-Flight sensor, the Observation Engine was designed to scale naturally.

The planned multi-sensor architecture is illustrated below.

```text
            ToF Sensor 1
                  │
                  ▼
       Observation Engine 1
                  │

            ToF Sensor 2
                  │
                  ▼
       Observation Engine 2
                  │

            ToF Sensor 3
                  │
                  ▼
       Observation Engine 3
                  │

                 ...

            ToF Sensor 6
                  │
                  ▼
       Observation Engine 6
                  │
                  ▼
            Context Engine
```

Each Observation Engine operates independently.

The Context Engine will consume the observations produced by all Observation Engines.

This architecture allows the system to scale by replication rather than redesign.

---

# 27. Extensibility

The Observation Engine has been intentionally designed so that future capabilities can be added with minimal impact on the existing software.

Examples include:

- Improved temporal filtering
- Additional motion states
- Confidence estimation
- Sector-specific enhancements
- Alternative observation models

These enhancements can be incorporated while preserving the external `ToFObservation` interface.

Similarly, future sensor technologies may introduce their own Observation Engines that generate compatible observation models for consumption by the Context Engine.

---

# 28. Design Trade-offs

Several trade-offs were considered during the development of v2.1.0.

## Simplicity vs Complexity

Preference was given to simple, modular processing stages rather than complex monolithic algorithms.

This improves maintainability and simplifies future evolution.

---

## Real-Time Performance vs Richness

The Observation Engine focuses on producing reliable observations with low computational overhead.

Higher-level interpretation is intentionally deferred to later architectural layers.

---

## Generality vs Application-Specific Logic

The Observation Engine remains application-independent.

It produces structured observations without embedding assumptions about navigation, obstacle avoidance, or user interaction.

This design allows the same Observation Engine to be reused in future Physical AI applications beyond assistive navigation.

---

# 29. Software Architecture Principles

The architecture of v2.1.0 is guided by a small set of software engineering principles that influence every design decision within the Observation Engine.

These principles ensure that the software remains maintainable, scalable, and extensible as the project evolves toward a complete Physical AI perception framework.

---

## 29.1 Single Responsibility Principle

Each software component is responsible for exactly one well-defined task.

Examples include:

| Component | Responsibility |
|-----------|----------------|
| Distance Validation | Validate incoming sensor measurements |
| Sector Extraction | Compute representative sector distances |
| Observation Builder | Construct structured observations |
| Observation History | Maintain temporal observation history |
| Velocity Estimator | Compute relative velocity |
| Velocity Smoother | Reduce measurement noise |
| Motion Classifier | Classify relative motion |

Separating these responsibilities improves readability and simplifies testing.

---

## 29.2 Layered Architecture

Each architectural layer performs one level of abstraction.

```text
Raw Measurements
        │
        ▼
Observation
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

Each layer consumes only the outputs of the previous layer.

No layer bypasses another.

This creates a predictable information flow throughout the system.

---

## 29.3 Stable Interfaces

Communication between architectural layers occurs through structured data models.

For v2.1.0, the primary interface is:

```text
ToFObservation
```

Higher-level layers interact only with this interface rather than with the internal implementation of the Observation Engine.

This allows internal algorithms to evolve without affecting downstream components.

---

## 29.4 Modularity

The Observation Engine is intentionally decomposed into independent processing stages.

Advantages include:

- Improved maintainability.
- Easier debugging.
- Independent unit testing.
- Simplified future enhancements.
- Better software reuse.

This modularity is expected to become increasingly valuable as additional sensors are introduced in future releases.

---

# 30. Data Model Design

The Observation Engine does not expose raw sensor measurements directly.

Instead, it publishes structured observation objects.

The primary data model introduced in v2.1.0 is shown below.

```text
ToFObservation

├── Timestamp
├── Frame Number
├── Sensor Identifier
├── Observation History Size
└── Sector Observations
```

Each sector observation contains:

```text
SectorObservation

├── Distance
├── Relative Velocity
└── Motion State
```

This abstraction allows downstream software to consume observations without requiring knowledge of the underlying sensor hardware.

---

## Design Goals

The observation model was designed to satisfy several objectives.

### Consistency

Every processed frame generates observations with the same structure.

---

### Simplicity

Only information that can be directly derived from Time-of-Flight measurements is included.

---

### Extensibility

Future releases should be able to extend the observation model without breaking existing interfaces.

---

### Hardware Independence

Higher-level software should remain independent of sensor-specific implementation details.

---

# 31. Interface Contracts

The Observation Engine provides a contract to downstream architectural layers.

This contract guarantees that:

- every processed frame produces one observation,
- every observation follows the same structure,
- every sector contains valid observation data,
- observations are generated in chronological order.

The Observation Engine does **not** guarantee:

- environmental understanding,
- obstacle identity,
- object tracking,
- prediction,
- navigation guidance.

These responsibilities belong to future architectural layers.

---

# 32. Non-Functional Requirements

In addition to functional requirements, the Observation Engine was designed to satisfy several non-functional objectives.

## Real-Time Execution

Observation generation should keep pace with the incoming sensor frame rate.

---

## Predictable Behaviour

The processing pipeline should execute deterministically for every frame.

---

## Low Memory Usage

Memory consumption should remain bounded regardless of application runtime.

---

## Scalability

The architecture should support future expansion from one Time-of-Flight sensor to multiple independent Observation Engines.

---

## Maintainability

Future improvements should require minimal modification to existing software components.

---

## Testability

Individual processing stages should be independently verifiable.

---

# 33. Error Handling Strategy

The Observation Engine adopts a defensive approach to error handling.

Examples include:

- invalid distance measurements,
- missing sensor data,
- communication failures,
- incomplete observations.

Where possible:

- invalid measurements are filtered,
- processing continues using valid information,
- observations remain structurally consistent.

The objective is graceful degradation rather than unexpected system failure.

---

# 34. Architectural Rationale

Several alternative architectures were considered during the design of v2.1.0.

One possible approach would have been to combine perception and environmental understanding within a single processing module.

This approach was rejected because it would tightly couple sensor processing with application-specific reasoning.

Instead, SixthSense separates these responsibilities into independent architectural layers.

This separation provides several advantages:

- simpler software components,
- clearer responsibilities,
- improved scalability,
- easier testing,
- independent evolution of architectural layers.

Although this results in additional architectural layers, it significantly improves long-term maintainability.

This architectural decision forms the foundation upon which all future versions of SixthSense will be developed.

# 35. Evolution of the Observation Engine

The Observation Engine is designed to evolve incrementally while preserving a stable external interface.

Each software release introduces one major capability without changing the fundamental responsibility of the Observation Engine.

The planned evolution is illustrated below.

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

Multi-Sensor Observation
```

Although each release extends the capabilities of the Observation Engine, its primary responsibility remains unchanged:

> **Generate structured observations from raw sensor measurements.**

This stability ensures that higher-level architectural layers remain independent of internal implementation changes.

---

# 36. Observation Model Evolution

The observation model introduced in v2.0.0 was intentionally designed to support future extensions.

The progression of the observation model is expected to follow the pattern below.

## v2.0.0

```text
Sector Observation

├── Distance
```

---

## v2.1.0

```text
Sector Observation

├── Distance
├── Relative Velocity
└── Motion State
```

---

## Planned v2.2.0

```text
Sector Observation

├── Distance
├── Relative Velocity
├── Motion State
├── Persistence
└── Confidence
```

The additional fields are expected to describe the temporal stability and reliability of each observation.

Importantly, these enhancements extend the observation model without changing its overall structure.

---

# 37. Multi-Sensor Architecture

Version **v3.0.0** is planned to extend the current prototype from one Time-of-Flight sensor to six independent sensors.

The software architecture scales by replicating the Observation Engine.

```text
ToF Sensor 1
      │
      ▼
Observation Engine 1
      │

ToF Sensor 2
      │
      ▼
Observation Engine 2
      │

ToF Sensor 3
      │
      ▼
Observation Engine 3
      │

...

ToF Sensor 6
      │
      ▼
Observation Engine 6
      │
      ▼
Context Engine
```

Each Observation Engine processes data independently and publishes a `ToFObservation`.

The Context Engine receives these observations and reasons about the environment as a whole.

No Observation Engine communicates directly with another Observation Engine.

This design minimizes coupling and allows each sensor to operate independently.

---

# 38. Context Engine Interface

The Observation Engine is intentionally unaware of the Context Engine.

Its only responsibility is to publish structured observations.

The Context Engine defines how these observations are interpreted.

The interface between the two layers is shown below.

```text
Observation Engine

        │

        ▼

ToFObservation

        │

        ▼

Context Engine
```

This interface provides several advantages.

- Independent development.
- Stable software boundaries.
- Simplified testing.
- Improved maintainability.
- Support for future sensor technologies.

Because the interface is observation-based rather than sensor-specific, the Context Engine can consume observations from multiple sources in future releases without requiring changes to the Observation Engine.

---

# 39. Architectural Constraints

Several architectural constraints were intentionally adopted during the design of v2.1.0.

These constraints should be preserved in future releases.

## Constraint 1

The Observation Engine shall not perform environmental reasoning.

---

## Constraint 2

The Observation Engine shall not depend upon higher-level architectural layers.

---

## Constraint 3

The Observation Engine shall expose only structured observations.

---

## Constraint 4

The Observation Engine shall remain deterministic for identical sensor inputs.

---

## Constraint 5

The Observation Engine shall support independent execution for each sensor instance.

These constraints maintain a clear separation between perception and reasoning and help preserve the modular architecture of the project.

---

# 40. Assumptions

The current implementation makes several assumptions.

These assumptions simplify the implementation while remaining appropriate for the scope of v2.1.0.

The Observation Engine assumes that:

- sensor measurements are received sequentially,
- timestamps are monotonically increasing,
- observations are processed in chronological order,
- each sensor operates independently,
- only one observation is generated for each processed frame.

These assumptions are expected to remain valid in future versions.

---

# 41. Dependencies

Version **v2.1.0** depends on several software and hardware components.

## Hardware

- Arduino UNO Q
- SparkFun VL53L5CX Time-of-Flight Sensor

---

## Firmware

- Arduino Sketch
- Arduino Bridge RPC

---

## Backend

- Python Observation Engine

---

## Frontend

- HTML
- CSS
- JavaScript
- Arduino App Lab WebUI

The Observation Engine itself remains independent of the dashboard implementation.

This separation allows the visualization layer to evolve without affecting perception.

---

# 42. Design Summary

The architectural evolution introduced in v2.1.0 demonstrates how additional capabilities can be incorporated while preserving the original software structure.

The Observation Engine has evolved from describing **where obstacles are** to describing **how observations change over time**.

This progression establishes the foundation required for subsequent architectural layers while maintaining a clear separation between perception and interpretation.

The resulting software architecture remains:

- Modular
- Deterministic
- Extensible
- Scalable
- Maintainable

These characteristics are expected to remain fundamental principles throughout the continued development of the SixthSense project.

# 43. Architectural Decisions

This section records the major architectural decisions made during the development of **v2.1.0**.

Unlike implementation details, these decisions are expected to remain valid across future releases and provide the rationale behind the software architecture.

---

## AD-01: Observation-First Architecture

### Decision

The system shall transform raw sensor measurements into structured observations before performing any environmental reasoning.

### Rationale

Separating perception from reasoning provides a clean architectural boundary.

Each software layer focuses on one level of abstraction.

```text
Raw Measurements
        │
        ▼
Observation
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

### Benefits

- Clear separation of responsibilities
- Easier testing
- Independent evolution of software layers
- Improved maintainability

---

## AD-02: Relative Motion Instead of Absolute Motion

### Decision

The Observation Engine estimates only **relative motion**.

### Rationale

A Time-of-Flight sensor measures changes in distance.

It cannot determine whether the observed distance change is caused by:

- user motion,
- obstacle motion,
- or both.

Attempting to infer the cause would introduce assumptions that cannot be validated using the available sensor data.

### Benefits

- Physically correct observations
- Sensor-independent implementation
- No hidden assumptions
- Simple observation model

Future Context Engines may combine observations from multiple sensors to infer the cause of relative motion.

---

## AD-03: One Observation Engine per Sensor

### Decision

Every Time-of-Flight sensor shall have its own independent Observation Engine.

### Rationale

Each Observation Engine processes only the measurements produced by its associated sensor.

Observation Engines do not communicate with one another.

Future environmental understanding is performed by the Context Engine.

### Benefits

- Independent processing
- Easy scalability
- Better fault isolation
- Natural support for multi-sensor systems

---

## AD-04: Stable Observation Interface

### Decision

The Observation Engine shall expose observations through a stable data model.

### Rationale

Higher-level architectural layers should depend only upon observations rather than implementation details.

### Benefits

- Loose coupling
- Easier software evolution
- Backward compatibility
- Simplified integration

---

# 44. Alternative Designs Considered

Several alternative architectures were considered during development.

The following sections summarize these alternatives and explain why they were not adopted.

---

## Alternative 1

### Direct Sensor-to-Feedback Pipeline

```text
ToF Sensor

↓

Feedback
```

### Advantages

- Extremely simple implementation
- Minimal software layers

### Disadvantages

- No environmental understanding
- Difficult to extend
- Poor software reuse
- Tight coupling

### Decision

Rejected.

The architecture does not scale beyond simple obstacle detection.

---

## Alternative 2

### Monolithic Processing Engine

```text
Sensor

↓

Large Processing Module

↓

Feedback
```

### Advantages

- Single implementation

### Disadvantages

- Difficult to maintain
- Difficult to test
- Poor modularity
- Limited extensibility

### Decision

Rejected.

The Observation-First Architecture provides a much cleaner separation of responsibilities.

---

## Alternative 3

### Environmental Reasoning Inside the Observation Engine

One possible design was to allow the Observation Engine to infer environmental meaning directly.

Examples include:

- Detecting walls
- Detecting corridors
- Detecting people
- Predicting motion

### Decision

Rejected.

These tasks belong to the future Context Engine.

Keeping the Observation Engine focused exclusively on perception preserves a clean architectural boundary.

---

# 45. Lessons Learned from v2.1.0

The development of the Temporal Observation Engine provided several important insights.

---

## Observation History is Essential

Temporal reasoning cannot be performed using isolated observations.

Maintaining a bounded observation history provides the minimum temporal context required for velocity estimation.

---

## Stable Interfaces Simplify Evolution

Preserving the existing `ToFObservation` interface while extending its contents greatly simplified implementation.

Future versions should continue extending existing interfaces rather than replacing them.

---

## Modular Pipelines Improve Maintainability

Breaking the Observation Engine into independent processing stages proved significantly easier to develop and debug than implementing one large processing algorithm.

This modular organization should be preserved in future releases.

---

## Observation and Context Should Remain Independent

One of the most important architectural lessons from v2.1.0 is that perception and interpretation should remain separate.

The Observation Engine should describe what the sensor observes.

The Context Engine should explain what those observations mean.

Maintaining this distinction significantly simplifies both architectural layers.

---

# 46. Compatibility with Future Releases

Version **v2.1.0** establishes several software contracts that future releases are expected to preserve.

These include:

- Observation-based architecture
- Stable observation interface
- Independent Observation Engines
- Layered software architecture
- Modular processing pipeline

Future releases may extend these capabilities but should avoid introducing unnecessary coupling between architectural layers.

Maintaining backward compatibility where practical will simplify future development and testing.

---

# 47. Engineering Considerations

Version **v2.1.0** was developed with the objective of establishing a robust perception layer rather than maximizing application features.

Several engineering priorities influenced the design.

---

## Simplicity

Preference was consistently given to simple and modular solutions over complex algorithms.

The objective of this release is to establish a reliable architectural foundation rather than implement sophisticated perception techniques.

Future releases can introduce more advanced algorithms without requiring architectural changes.

---

## Predictability

The Observation Engine processes every incoming sensor frame using the same sequence of operations.

This deterministic execution model simplifies:

- debugging,
- validation,
- performance analysis,
- future optimization.

Predictable software behavior is particularly important for real-time perception systems.

---

## Maintainability

Every processing stage performs one clearly defined task.

This modular organization makes the software easier to:

- understand,
- modify,
- test,
- document.

As additional capabilities are introduced, existing modules can be extended without redesigning the overall architecture.

---

## Extensibility

The Observation Engine was designed with future releases in mind.

The software architecture allows new capabilities to be introduced by extending existing components rather than replacing them.

Examples include:

- persistence estimation,
- confidence estimation,
- additional motion states,
- richer observation models.

---

# 48. Future Evolution

Version **v2.1.0** establishes the temporal perception capabilities required for subsequent architectural milestones.

The planned evolution of the software is summarized below.

---

## v2.2.0 — Persistent Observation Engine

The next release extends temporal observations by introducing persistence.

Persistence describes how consistently an observation remains present over time.

The objective is to distinguish between:

- stable observations,
- transient observations,
- intermittent observations.

This additional temporal information will improve the quality of observations provided to future reasoning modules.

---

## v3.0.0 — Six Independent Observation Engines

Version **v3.0.0** expands the current architecture from one Time-of-Flight sensor to six sensors.

The software architecture evolves through replication rather than redesign.

```text
One Sensor
        │
        ▼
One Observation Engine

↓

Six Sensors
        │
        ▼
Six Independent Observation Engines
```

Each Observation Engine continues to operate independently.

The architectural interface established in v2.1.0 remains unchanged.

---

## v4.0.0 — Context Engine

Once multiple Observation Engines are available, the Context Engine becomes responsible for interpreting their outputs.

Unlike the Observation Engine, the Context Engine does not process raw sensor measurements.

Instead, it consumes structured observations and generates an understanding of the surrounding environment.

Examples of future responsibilities include:

- spatial understanding,
- environmental understanding,
- motion understanding,
- situation assessment.

---

## v5.0.0 and Beyond

Higher-level architectural layers will continue building upon the outputs of the previous layers.

```text
Observation

↓

Context

↓

Attention

↓

Feedback
```

Each layer increases the semantic meaning of the available information while preserving clear architectural boundaries.

---

# 49. Validation Results

The implementation of v2.1.0 successfully demonstrates the feasibility of temporal observation generation using a Time-of-Flight sensor.

The following capabilities were validated during development.

| Capability | Status |
|------------|:------:|
| Live Time-of-Flight acquisition | ✅ |
| Three-sector observation model | ✅ |
| Observation history | ✅ |
| Relative velocity estimation | ✅ |
| Motion state classification | ✅ |
| Velocity smoothing | ✅ |
| Interactive dashboard | ✅ |
| Live JSON observations | ✅ |

These results confirm that the Observation Engine can reliably generate structured temporal observations suitable for higher-level architectural layers.

---

# 50. Key Contributions

Version **v2.1.0** introduces several significant architectural contributions.

## Temporal Perception

The Observation Engine evolves from describing static observations to describing temporal observations.

---

## Structured Observation Interface

A stable observation interface is established between perception and future reasoning modules.

---

## Modular Processing Pipeline

Independent processing stages improve software quality and simplify future development.

---

## Observation-First Architecture

Perception and environmental understanding remain cleanly separated.

This architectural decision forms the foundation for future Context, Attention, and Feedback Engines.

---

## Scalable Design

The Observation Engine can be replicated for multiple Time-of-Flight sensors without architectural modification.

This enables straightforward expansion to the planned six-sensor prototype.

---
