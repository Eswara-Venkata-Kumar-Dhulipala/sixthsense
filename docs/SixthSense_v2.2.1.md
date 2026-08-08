# SixthSense v2.2.1

> **Confidence-Aware Temporal ToF Observation Engine**

| Item | Value |
|------|-------|
| Project | SixthSense |
| Document | Software Architecture & Design Document |
| Software Version | v2.2.1 |
| Document Version | 1.0 |
| Status | Released |
| Last Updated | August 2026 |
| Author | Eswara Venkata Kumar Dhulipala |

---

# Release History

| Software Version | Major Capability |
|-----------------|------------------|
| v2.0.0 | Static ToF Observation Engine |
| v2.1.0 | Temporal ToF Observation Engine |
| v2.2.1 | Confidence-Aware Temporal ToF Observation Engine |

---

# Table of Contents

1. Introduction
2. Objectives
3. Background
4. Motivation
5. Scope
6. Design Philosophy
7. High-Level Architecture
8. Runtime Architecture
9. VL53L5CX Sensor Configuration
10. Sensor Measurement Model
11. Arduino Acquisition Architecture
12. Snapshot-Based Bridge Architecture
13. Python Snapshot Acquisition
14. Image Orientation
15. Confidence Engine
16. Target Status Interpretation
17. Confidence Normalization
18. Confidence Fusion
19. Confidence Validity Gates
20. Confidence-Aware Sector Selection
21. Three-Sector Observation Model
22. Zone Identification
23. Temporal Observation Engine
24. Velocity Estimation
25. Velocity Smoothing
26. Motion State Classification
27. Data Models
28. ToFFrame
29. SectorObservation
30. ToFObservation
31. Data Storage and Retention
32. Sensor Acquisition Rate vs Processing Rate
33. Dashboard Design
34. Arduino Bridge Interface
35. Sensor Initialization and Diagnostics
36. Error Handling
37. Runtime Execution Flow
38. Data Flow
39. Validation Strategy
40. Validation Results
41. Computational Characteristics
42. Reliability Considerations
43. Design Decisions
44. Design Trade-offs
45. Current Limitations
46. Scalability
47. Extensibility
48. Compatibility with Future Releases
49. Evolution of the Observation Engine
50. Future Evolution
51. Key Contributions
52. Design Summary

---

# 1. Introduction

Version **v2.2.1** introduces the **Confidence-Aware Temporal ToF Observation Engine**, representing the third major perception milestone of the SixthSense project.

Version **v2.0.0** introduced structured static obstacle observations.

Version **v2.1.0** added temporal history, relative velocity estimation, velocity smoothing, and motion-state classification.

Although those releases provided spatial and temporal information, they still relied primarily on the measured distance value.

A Time-of-Flight sensor measurement contains significantly more information than distance alone.

The VL53L5CX also provides measurement-quality information such as:

- Signal strength
- Range uncertainty
- Target status
- Target reflectance
- Ambient light
- Number of detected targets
- Number of enabled SPADs

Version **v2.2.1** introduces a Confidence Engine that uses these signals to estimate the quality of every ToF measurement before it is used by the Observation Engine.

The resulting perception pipeline now answers three increasingly useful questions:

```text
Where is the obstacle?

How is its distance changing?

How much should the measurement be trusted?
```

This document describes the architecture, implementation, design decisions, and validation of the Confidence-Aware Temporal ToF Observation Engine.

---

# 2. Objectives

The primary objective of v2.2.1 is to improve the reliability of the Observation Engine by incorporating measurement-quality information provided by the VL53L5CX.

The release aims to:

- Acquire the complete required VL53L5CX measurement set.
- Preserve measurement alignment across Arduino-to-Python communication.
- Generate a confidence score for every one of the 64 ToF zones.
- Reject measurements that fail fundamental validity conditions.
- Select obstacles using confidence-aware filtering.
- Attach sensor-quality information to sector observations.
- Preserve temporal observation history.
- Preserve relative velocity estimation.
- Preserve velocity smoothing.
- Preserve motion-state classification.
- Improve sensor initialization diagnostics.
- Extend the dashboard with confidence visualization.
- Preserve the modular Observation-First Architecture.

The release intentionally does **not** attempt to:

- Perform statistical confidence calibration.
- Persistently track objects.
- Fuse multiple ToF sensors.
- Identify objects.
- Interpret environmental context.
- Prioritize observations.
- Generate navigation decisions.
- Produce haptic feedback.
- Produce spatial audio feedback.

These responsibilities remain outside the scope of the current Observation Engine.

---

# 3. Background

SixthSense follows an **Observation-First Architecture**.

Raw sensor information is transformed into structured observations before any higher-level environmental interpretation is performed.

The long-term architecture remains:

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

Each layer has a clearly defined responsibility.

### Observation Engine

Determines what the sensors currently observe.

### Context Engine

Interprets observations and builds environmental understanding.

### Attention Engine

Determines which environmental information is most relevant.

### Feedback Engine

Determines how relevant information should be communicated to the user.

Version v2.2.1 remains entirely inside the **Observation Engine** layer.

---

# 4. Motivation

A distance measurement alone does not indicate whether that measurement is reliable.

Consider two hypothetical VL53L5CX zones:

```text
Zone A

Distance       = 600 mm
Target Status  = 5
Strong Signal
Low Sigma
Target Detected
```

and:

```text
Zone B

Distance       = 450 mm
Invalid Status
Weak Signal
High Uncertainty
```

A nearest-distance-only algorithm would select:

```text
Zone B = 450 mm
```

because it is physically closer.

However, the measurement may be unreliable.

For assistive navigation, blindly selecting the smallest reported distance could cause:

- False obstacle detections
- Unstable observations
- Incorrect velocity estimates
- Frequent changes in selected obstacle zones
- Unnecessary feedback
- Reduced user confidence in the system

Therefore, the Observation Engine requires a mechanism to evaluate measurement quality before selecting an obstacle.

Version v2.2.1 introduces that mechanism through the **Confidence Engine**.

---

# 5. Scope

## Included

Version v2.2.1 includes:

- 8×8 VL53L5CX ranging
- Complete 64-zone sensor measurement acquisition
- Signal-per-SPAD acquisition
- Range-sigma acquisition
- Target-status acquisition
- Reflectance acquisition
- Ambient-per-SPAD acquisition
- Target-count acquisition
- Enabled-SPAD acquisition
- Arduino live measurement buffers
- Arduino snapshot buffers
- Snapshot-based RouterBridge communication
- Sensor initialization diagnostics
- Confidence normalization
- Confidence fusion
- Per-zone confidence map
- Confidence-aware sector selection
- Zone identification
- Sensor-quality metadata in sector observations
- Observation history
- Relative velocity estimation
- Velocity smoothing
- Motion-state classification
- Distance heatmap
- Confidence heatmap
- Confidence-aware dashboard

## Excluded

The following capabilities are deferred:

- Persistent obstacle tracking
- Raw frame recording to disk
- Database storage
- Full 15 Hz frame retention
- Object identification
- Object tracking
- Multi-ToF fusion
- Context reasoning
- Attention modelling
- Navigation planning
- Haptic feedback
- Audio feedback

---

# 6. Design Philosophy

The design follows the existing SixthSense architectural principles.

## Observation Before Interpretation

The Observation Engine reports what the sensor observes and how trustworthy that observation appears.

It does not determine what the object is or what the user should do.

---

## Measurement Quality Before Selection

A measured distance should not automatically become an obstacle observation.

Measurement validity and quality are evaluated before sector selection.

---

## Incremental Evolution

The architecture established in v2.0.0 and v2.1.0 is preserved.

Confidence is added as another perception capability rather than replacing the Observation Engine.

---

## Stable External Observations

Higher-level modules should operate on structured `ToFObservation` objects instead of raw sensor arrays.

---

## Latest-State Perception

The runtime system prioritizes recent environmental state over processing a backlog of old sensor frames.

This is important for real-time assistive perception.

---

# 7. High-Level Architecture

The v2.2.1 processing architecture is:

```text
VL53L5CX
    │
    ▼
Arduino Sensor Acquisition
    │
    ▼
Live Measurement Buffers
    │
    ▼
Snapshot Capture
    │
    ▼
RouterBridge
    │
    ▼
Python ToFFrame
    │
    ▼
Confidence Engine
    │
    ▼
64-Zone Confidence Map
    │
    ▼
Confidence-Aware Sector Extraction
    │
    ▼
Temporal Observation Engine
    │
    ├── Observation History
    ├── Velocity Estimation
    ├── Velocity Smoothing
    └── Motion Classification
    │
    ▼
ToFObservation
    │
    ▼
Web Dashboard
```

---

# 8. Runtime Architecture

The current implementation runs across the two processing environments available on the Arduino UNO Q platform.

```text
                    VL53L5CX
                        │
                       I²C
                        │
                        ▼
               Arduino Sketch / MCU
                        │
                15 Hz Acquisition
                        │
                        ▼
                   LIVE Buffers
                        │
                capture_snapshot()
                        │
                        ▼
                 SNAPSHOT Buffers
                        │
                  RouterBridge
                        │
                        ▼
                 Python Backend
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
 Confidence Engine             Observation Engine
        │                               │
        └───────────────┬───────────────┘
                        │
                        ▼
                WebUI / Dashboard
```

The Arduino sketch is responsible for deterministic sensor acquisition.

Python is responsible for perception processing and visualization.

---

# 9. VL53L5CX Sensor Configuration

The current prototype uses one SparkFun VL53L5CX sensor.

Configuration:

| Parameter | Value |
|-----------|------:|
| Resolution | 8 × 8 |
| Zones | 64 |
| Ranging Frequency | 15 Hz |
| Integration Time | 20 ms |
| I²C Address | `0x29` |
| I²C Clock | 400 kHz |
| Target Index | 0 |
| Target Order | Closest |

The sensor therefore attempts to generate approximately:

```text
15 measurement frames / second
```

with approximately:

```text
66.7 ms
```

between sensor frames.

---

# 10. Sensor Measurement Model

For every zone, the current implementation retrieves the following measurements.

## Per-Target Measurements

```text
distance_mm
signal_per_spad
range_sigma_mm
target_status
reflectance
```

The implementation uses:

```text
TARGET_INDEX = 0
```

with closest-target ordering.

The per-target index is calculated as:

```text
targetIndex =
    zone × VL53L5CX_NB_TARGET_PER_ZONE
    + TARGET_INDEX
```

---

## Per-Zone Measurements

```text
ambient_per_spad
nb_target_detected
nb_spads_enabled
```

These arrays are indexed directly by zone.

---

## Measurements Used by Confidence Engine

| Measurement | Interpretation |
|-------------|----------------|
| Distance | Target range |
| Signal per SPAD | Returned signal strength |
| Range Sigma | Measurement uncertainty |
| Target Status | Sensor-provided validity state |
| Reflectance | Target reflectivity information |
| Ambient per SPAD | Background optical condition |
| Targets Detected | Whether a target exists |
| SPADs Enabled | Active detector information |

---

# 11. Arduino Acquisition Architecture

The Arduino maintains two independent groups of measurement buffers.

## Live Buffers

```text
liveDistance
liveSignal
liveSigma
liveStatus
liveReflectance
liveAmbient
liveTargets
liveSpads
```

Whenever `updateFrame()` retrieves a new VL53L5CX result, these arrays are updated.

Metadata is also updated:

```text
liveFrameCounter
liveTimestamp
```

The live buffers therefore represent the most recently acquired sensor frame.

---

## Snapshot Buffers

A second set of arrays is maintained:

```text
snapshotDistance
snapshotSignal
snapshotSigma
snapshotStatus
snapshotReflectance
snapshotAmbient
snapshotTargets
snapshotSpads
```

with:

```text
snapshotFrameCounter
snapshotTimestamp
```

These arrays are exposed to Python through RouterBridge.

---

# 12. Snapshot-Based Bridge Architecture

Retrieving eight sensor arrays through eight separate Bridge calls directly from live data creates a potential frame-alignment problem.

For example:

```text
Python reads distance       → Sensor Frame 100
Python reads signal         → Sensor Frame 101
Python reads sigma          → Sensor Frame 101
Python reads status         → Sensor Frame 102
```

The resulting Python structure would combine information from different sensor frames.

Version v2.2.1 avoids this through a snapshot-copy architecture.

```text
Sensor
  │
  ▼
LIVE Frame 100
  │
  │ capture_snapshot()
  ▼
SNAPSHOT Frame 100
  │
  ├── distance
  ├── signal
  ├── sigma
  ├── status
  ├── reflectance
  ├── ambient
  ├── targets
  └── spads
        │
        ▼
      Python
```

When Python calls:

```text
capture_snapshot()
```

the latest live arrays are copied to snapshot arrays.

Subsequent getter RPCs read only the snapshot buffers.

This allows Python to retrieve a logically consistent captured sensor state while the acquisition loop continues operating.

---

# 13. Python Snapshot Acquisition

Python retrieves a ToF frame through the following sequence.

```text
sensor_ready()
      │
      ▼
get_sensor_init_code()
      │
      ▼
get_live_frame_counter()
      │
      ▼
capture_snapshot()
      │
      ▼
get_snapshot_frame_counter()
      │
      ▼
Validate frame metadata
      │
      ▼
Read timestamp
      │
      ▼
Read eight measurement arrays
      │
      ▼
Validate 64-element arrays
      │
      ▼
Convert to oriented 8×8 arrays
      │
      ▼
Calculate confidence image
      │
      ▼
Create ToFFrame
```

Duplicate snapshots are ignored by comparing the captured frame counter with the previously processed frame counter.

---

# 14. Image Orientation

Raw 64-zone arrays are reshaped into:

```text
8 × 8
```

NumPy arrays.

The image is then horizontally flipped:

```python
np.fliplr(image)
```

This provides the orientation used by the dashboard and sector model.

Because the image is flipped, the visual image coordinate does not directly equal the raw VL53L5CX zone identifier.

Raw zone recovery is therefore handled explicitly during sector observation construction.

---

# 15. Confidence Engine

The Confidence Engine estimates measurement quality independently for every sensor zone.

Output:

```text
0.0 – 100.0
```

For each zone:

```text
Distance
Signal
Sigma
Status
Reflectance
Ambient
Targets
SPADs
   │
   ▼
Normalization
   │
   ▼
Validity Checks
   │
   ▼
Weighted Fusion
   │
   ▼
Confidence Score
```

The result for a complete frame is:

```text
8 × 8 confidence image
```

corresponding spatially to the 8×8 distance image.

---

# 16. Target Status Interpretation

VL53L5CX target status is treated as an important measurement-quality indicator.

The current interpretation is:

| Status | Normalized Status Score |
|-------:|------------------------:|
| 5 | 1.0 |
| 6 | 0.5 |
| 9 | 0.5 |
| All other statuses | 0.0 |

The underlying guidance identifies status `5` as fully valid and statuses `6` and `9` as approximately 50% confidence.

Other statuses are documented as having less than 50% confidence.

Because exact confidence values are not available for every lower-confidence status, the current implementation intentionally uses a conservative strategy:

```text
All other statuses → 0.0
```

This prevents uncertain target states from being promoted to trusted obstacles.

---

# 17. Confidence Normalization

Each raw measurement has a different numerical range.

The Confidence Engine converts measurements to:

```text
0.0 – 1.0
```

before weighted fusion.

The clamp function is:

```text
clamp(x) = max(0, min(1, x))
```

---

## 17.1 Signal Score

Reference:

```text
CONF_SIGNAL_REFERENCE = 1000
```

Signal normalization uses a logarithmic relationship:

```text
signal_score =

log10(signal + 1)
-----------------
log10(1000 + 1)
```

followed by clamping to `[0, 1]`.

The logarithmic transformation is used because signal strength can vary over a wide numerical range.

---

## 17.2 Sigma Score

Reference:

```text
CONF_SIGMA_REFERENCE = 64
```

Lower uncertainty is considered better.

```text
sigma_score =

1 - sigma / 64
```

The result is clamped to `[0, 1]`.

---

## 17.3 Ambient Score

Reference:

```text
CONF_AMBIENT_REFERENCE = 128
```

Lower ambient interference is currently considered preferable.

```text
ambient_score =

1 - ambient / 128
```

The result is clamped.

---

## 17.4 Reflectance Score

Reference:

```text
CONF_REFLECTANCE_REFERENCE = 255
```

```text
reflectance_score =

reflectance / 255
```

followed by clamping.

---

## 17.5 Target Score

```text
targets > 0 → 1.0
targets = 0 → 0.0
```

---

## 17.6 SPAD Score

Reference:

```text
CONF_SPADS_REFERENCE = 3840
```

```text
spad_score =

spads / 3840
```

followed by clamping.

---

# 18. Confidence Fusion

The normalized measurements are combined using a weighted sum.

Current weights:

| Component | Weight |
|-----------|-------:|
| Target Status | 30 |
| Signal | 30 |
| Sigma | 20 |
| Ambient | 5 |
| Reflectance | 5 |
| Target Detection | 5 |
| Enabled SPADs | 5 |
| **Total** | **100** |

The confidence score is:

```text
Confidence =

30 × status_score
+
30 × signal_score
+
20 × sigma_score
+
5 × ambient_score
+
5 × reflectance_score
+
5 × target_score
+
5 × spad_score
```

The result is constrained to:

```text
0 – 100
```

and rounded to one decimal place.

---

# 19. Confidence Validity Gates

Before weighted confidence fusion, several fundamental conditions are checked.

A zone immediately receives:

```text
Confidence = 0
```

if any of the following conditions apply.

### Invalid Distance

```text
distance <= 0
```

### Outside Configured Perception Range

```text
distance > 3000 mm
```

### No Target

```text
targets <= 0
```

### Unaccepted Target Status

```text
status_score <= 0
```

Therefore, confidence is not merely a weighted score.

It also performs fundamental measurement validation.

---

# 20. Confidence-Aware Sector Selection

Earlier Observation Engine versions selected the nearest valid distance within each sector.

Version v2.2.1 selects the nearest **trusted** zone.

A zone is excluded if:

```text
distance <= 0
```

or:

```text
distance > 3000 mm
```

or:

```text
confidence <= 0
```

Excluded distances are replaced internally with:

```text
4000 mm
```

which acts as an invalid sentinel during minimum-distance selection.

The selected sector obstacle is therefore:

```text
Nearest zone
AND
valid distance
AND
positive confidence
```

Conceptually:

```text
All Sector Zones
       │
       ▼
Distance Valid?
       │
       ▼
Confidence > 0?
       │
       ▼
Trusted Zones
       │
       ▼
Nearest Trusted Zone
       │
       ▼
SectorObservation
```

---

# 21. Three-Sector Observation Model

The oriented sensor image is divided into three logical sectors.

```text
Columns

0   1 | 2   3   4 | 5   6   7
───────|───────────|───────────
Sector0|  Sector1  |  Sector2
```

Configuration:

```text
Sector 0 → columns [0, 2)
Sector 1 → columns [2, 5)
Sector 2 → columns [5, 8)
```

Each sector produces one `SectorObservation`.

This provides a lightweight spatial abstraction while preserving a path toward future multi-sensor perception.

---

# 22. Zone Identification

Because sensor images are horizontally flipped before perception processing, the selected image coordinate must be converted back to the original VL53L5CX zone identifier.

The raw column is recovered using:

```text
raw_column =
    IMAGE_COLS
    - 1
    - oriented_column
```

The raw zone identifier is then:

```text
zone_id =
    row × IMAGE_COLS
    + raw_column
```

This allows dashboard and diagnostic data to refer to the physical sensor zone from which the selected observation originated.

---

# 23. Temporal Observation Engine

The temporal processing introduced in v2.1.0 remains active.

The Observation Engine maintains:

```text
TOF_HISTORY_SIZE = 20
```

processed observations.

For each new frame:

```text
ToFFrame
    │
    ▼
Sector Observation Construction
    │
    ▼
ToFObservation
    │
    ▼
Velocity Estimation
    │
    ▼
Velocity Filtering
    │
    ▼
Observation History
```

Confidence is now incorporated into this pipeline so unreliable measurements do not directly participate in velocity estimation.

---

# 24. Velocity Estimation

Relative velocity is calculated from consecutive sector observations.

For a sector:

```text
velocity =

current_distance - previous_distance
------------------------------------
              Δt
```

Units:

```text
mm/s
```

Timestamp differences are converted from milliseconds to seconds.

The minimum accepted time step is:

```text
MIN_VALID_DT = 0.02 seconds
```

If:

```text
Δt < 0.02
```

the implementation uses:

```text
Δt = 0.02
```

to avoid unstable division by extremely small time intervals.

---

## Confidence-Aware Velocity Validation

Velocity is set to zero if either observation contains:

```text
distance <= 0
```

or:

```text
confidence <= 0
```

This prevents invalid measurements from generating artificial velocity spikes.

---

# 25. Velocity Smoothing

The system maintains a separate velocity history for each sector.

Configuration:

```text
VELOCITY_WINDOW = 5
```

For every sector:

```text
Smoothed Velocity =

sum(recent velocity samples)
----------------------------
number of samples
```

The resulting value is rounded to one decimal place.

This reduces frame-to-frame noise while preserving simple computational behavior.

---

# 26. Motion State Classification

Relative velocity is converted into a qualitative motion state.

Configuration:

```text
STATIONARY_THRESHOLD = 50 mm/s
```

Classification:

```text
velocity < -50 mm/s
        ↓
   Approaching
```

```text
-50 mm/s <= velocity <= +50 mm/s
        ↓
     Stationary
```

```text
velocity > +50 mm/s
        ↓
     Receding
```

The state represents **relative range change**.

It does not independently distinguish whether motion originates from:

- The obstacle
- The sensor
- The user
- A combination of these

---

# 27. Data Models

Version v2.2.1 uses three major data structures:

```text
ToFFrame
    │
    ▼
SectorObservation
    │
    ▼
ToFObservation
```

Each has a different architectural responsibility.

---

# 28. ToFFrame

`ToFFrame` represents one complete Python-side sensor snapshot.

It contains:

```text
frame_number
timestamp

distance
signal
sigma
status
reflectance
ambient
targets
spads
confidence
```

Each sensor measurement is represented as an oriented:

```text
8 × 8 NumPy array
```

The confidence field is also:

```text
8 × 8
```

and spatially corresponds to the same zones.

---

# 29. SectorObservation

Each logical sector produces one `SectorObservation`.

Current fields:

```text
sector_id
sector_name

distance_mm

zone_id
confidence

signal
sigma
target_status
reflectance
ambient
targets
spads

velocity_mmps
persistence
```

The sensor-quality values correspond to the **same selected zone** as the reported distance.

This is an important requirement.

The implementation does not select:

```text
distance from one zone
signal from another zone
sigma from another zone
```

All selected quality values refer to the same physical measurement.

---

## Persistence Field

The data model currently contains:

```text
persistence
```

with a default value of:

```text
0.0
```

This field is reserved for future development.

Version v2.2.1 does **not** implement a Persistence Engine.

---

# 30. ToFObservation

Each successfully processed snapshot generates one `ToFObservation`.

Fields:

```text
sensor_id
sensor_name
status
frame_number
timestamp
fps
sectors
history_size
```

Example:

```json
{
    "sensor_id": "tof_01",
    "sensor_name": "Prototype ToF",
    "status": "ONLINE",
    "frame_number": 934,
    "timestamp": 88774,
    "fps": 5.8,
    "history_size": 20,
    "sectors": [
        {
            "sector_id": 0,
            "sector_name": "Sector 0",
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
            "persistence": 0.0
        }
    ]
}
```

The full observation normally contains three sector entries.

---

# 31. Data Storage and Retention

It is important to distinguish between:

- Sensor acquisition
- Temporary sensor-frame processing
- Observation history
- Persistent storage

Version v2.2.1 does **not** store every sensor frame.

---

## Arduino Storage

The Arduino holds only:

```text
Latest LIVE frame
+
Latest SNAPSHOT frame
```

The live buffers are overwritten whenever the next VL53L5CX frame arrives.

For example:

```text
Frame 100 → LIVE buffers

Frame 101 → overwrites Frame 100

Frame 102 → overwrites Frame 101
```

There is currently no Arduino-side historical frame queue.

---

## Python Raw Frame Storage

Python constructs a `ToFFrame` containing all 64 zones.

This object is used for:

- Confidence calculation
- Sector extraction
- Dashboard heatmaps

The system does not maintain a history of complete raw `ToFFrame` objects.

---

## Observation History

Python stores:

```text
20 ToFObservation objects
```

using:

```text
deque(maxlen=20)
```

These contain three processed sector observations, not all 64 raw zones.

---

## Velocity History

Python separately maintains:

```text
5 velocity samples per sector
```

for smoothing.

---

## Persistent Storage

Version v2.2.1 does not write sensor data to:

- Files
- CSV
- SQLite
- Database
- Cloud storage

All runtime data is lost when the application stops.

---

# 32. Sensor Acquisition Rate vs Processing Rate

The VL53L5CX is configured to acquire data at:

```text
15 Hz
```

However, Python does not necessarily process all 15 frames each second.

The snapshot interface requires several RouterBridge transactions.

Typical Python snapshot retrieval involves:

```text
sensor_ready
get_sensor_init_code
get_live_frame_counter
capture_snapshot
get_snapshot_frame_counter
get_timestamp
get_distance
get_signal
get_sigma
get_status
get_reflectance
get_ambient
get_targets
get_spads
```

During these operations, the Arduino continues acquiring sensor frames.

Therefore, a sequence can look like:

```text
Arduino:

Frame 100
Frame 101
Frame 102
Frame 103
Frame 104
Frame 105
Frame 106
```

while Python processes:

```text
Frame 100
Frame 103
Frame 106
```

Frames that are overwritten before Python captures them are not retained.

This is intentional for the current real-time architecture.

The design prioritizes:

> **the freshest available environmental state rather than processing an accumulated backlog of old frames.**

The displayed Python FPS therefore represents the effective observation-processing rate, not the underlying VL53L5CX ranging frequency.

---

# 33. Dashboard Design

The v2.2.1 dashboard provides visual access to the confidence-aware perception pipeline.

Major components include:

## Sensor Information

Displays:

- Sensor ID
- Sensor name
- Online status
- Frame number
- Timestamp
- Effective FPS

---

## Sector Observation Cards

Each sector displays:

- Distance
- Confidence
- Confidence classification
- Source zone
- Velocity
- Motion state

---

## Confidence Presentation Levels

The dashboard currently uses presentation-level categories:

```text
Confidence >= 80
        ↓
       HIGH
```

```text
50 <= Confidence < 80
        ↓
       MEDIUM
```

```text
0 < Confidence < 50
        ↓
       LOW
```

```text
Confidence = 0
        ↓
      INVALID
```

These classifications are **dashboard visualization categories**.

They do not alter the Confidence Engine calculation.

---

## Distance Heatmap

The distance heatmap shows the spatial ranging output from all 64 zones.

Near values are represented toward red.

Farther values progressively move toward green.

---

## Confidence Heatmap

The confidence heatmap displays the confidence calculated for every corresponding sensor zone.

This allows direct visual comparison between:

```text
What did the sensor measure?
```

and:

```text
How much does the current algorithm trust it?
```

---

## JSON Viewer

The dashboard also displays the complete serialized `ToFObservation`.

This is useful for:

- Development
- Validation
- Debugging
- Future interface design

---

# 34. Arduino Bridge Interface

The Arduino currently exposes the following RouterBridge functions.

## Diagnostic RPCs

```text
sensor_ready
get_sensor_init_code
get_live_frame_counter
get_snapshot_frame_counter
```

## Snapshot Control

```text
capture_snapshot
```

## Metadata

```text
get_timestamp
```

## Sensor Data

```text
get_distance
get_signal
get_sigma
get_status
get_reflectance
get_ambient
get_targets
get_spads
```

This interface separates:

```text
Sensor acquisition
```

from:

```text
Python consumption
```

and allows either side to evolve independently.

---

# 35. Sensor Initialization and Diagnostics

Version v2.2.1 introduces improved VL53L5CX initialization diagnostics.

The sensor initialization process performs:

```text
Wire1.begin()
      │
      ▼
400 kHz I²C configuration
      │
      ▼
500 ms startup delay
      │
      ▼
I²C probe at 0x29
      │
      ▼
tof.begin()
      │
      ▼
8×8 resolution
      │
      ▼
15 Hz frequency
      │
      ▼
20 ms integration time
      │
      ▼
Closest target order
      │
      ▼
startRanging()
```

---

## Initialization Retries

Sensor detection is retried up to:

```text
10 attempts
```

with:

```text
500 ms
```

between attempts.

The direct I²C probe distinguishes:

```text
No device responding at 0x29
```

from:

```text
I²C device detected but VL53L5CX driver initialization failed
```

This significantly improves startup diagnostics.

---

## Initialization Codes

| Code | Meaning |
|-----:|---------|
| `0` | Initialization not completed |
| `1` | Sensor successfully initialized |
| `-1` | `tof.begin()` / sensor detection failed |
| `-2` | 8×8 resolution configuration failed |
| `-3` | 15 Hz ranging frequency configuration failed |
| `-4` | 20 ms integration-time configuration failed |
| `-5` | `startRanging()` failed |

The Bridge remains available after initialization failure so Python can retrieve the diagnostic code.

---

# 36. Error Handling

The implementation contains multiple error-detection layers.

## Bridge Availability

Python catches RouterBridge communication exceptions and waits for the Arduino interface.

---

## Sensor Initialization

Python queries:

```text
sensor_ready()
```

and:

```text
get_sensor_init_code()
```

before attempting frame acquisition.

---

## First Frame

If:

```text
liveFrameCounter == 0
```

Python waits for the first valid ranging frame.

---

## Snapshot Metadata

Python validates:

```text
capture_snapshot() result
```

against:

```text
get_snapshot_frame_counter()
```

---

## Duplicate Frames

If:

```text
frame_counter == last_frame_counter
```

the frame is ignored.

---

## Snapshot Arrays

Every received array must contain exactly:

```text
64 values
```

before it is accepted.

---

## RouterBridge `uint8_t` Handling

Some Arduino `std::array<uint8_t, 64>` values may arrive in Python as binary byte buffers instead of ordinary Python lists.

The conversion layer therefore supports:

```text
bytes
bytearray
memoryview
list
tuple
NumPy-compatible arrays
```

Binary values are interpreted with:

```python
np.frombuffer()
```

before reshaping.

---

# 37. Runtime Execution Flow

The complete runtime flow is:

```text
Application Startup
       │
       ▼
Arduino Buffer Initialization
       │
       ▼
VL53L5CX Initialization
       │
       ▼
RouterBridge Registration
       │
       ▼
15 Hz Sensor Acquisition
       │
       ▼
LIVE Buffers Updated
       │
       │
       │ Python Application Loop
       │
       ▼
sensor_ready()
       │
       ▼
capture_snapshot()
       │
       ▼
SNAPSHOT Buffers
       │
       ▼
Bridge Measurement Retrieval
       │
       ▼
64-Zone Validation
       │
       ▼
8×8 Orientation
       │
       ▼
Confidence Engine
       │
       ▼
Confidence Image
       │
       ▼
Three-Sector Extraction
       │
       ▼
Nearest Trusted Zone Selection
       │
       ▼
ToFObservation
       │
       ▼
Velocity Estimation
       │
       ▼
Velocity Smoothing
       │
       ▼
Observation History
       │
       ▼
JSON Serialization
       │
       ▼
Web Dashboard
```

---

# 38. Data Flow

The data transformation hierarchy is:

```text
VL53L5CX_ResultsData
          │
          ▼
Arduino LIVE arrays
          │
          ▼
Arduino SNAPSHOT arrays
          │
          ▼
Bridge RPC
          │
          ▼
Python 64-element values
          │
          ▼
8×8 NumPy arrays
          │
          ▼
ToFFrame
          │
          ▼
64-zone Confidence Map
          │
          ▼
3 × SectorObservation
          │
          ▼
ToFObservation
          │
          ▼
Dashboard / Future Modules
```

---

# 39. Validation Strategy

Version v2.2.1 was validated incrementally.

## Sensor Validation

Raw VL53L5CX measurements were first inspected directly.

Observed measurements included:

- Distance
- Signal
- Sigma
- Target status
- Reflectance
- Ambient
- Target count
- Enabled SPADs

---

## Bridge Validation

Individual sensor arrays were verified through RouterBridge.

---

## Snapshot Validation

Frame counters and measurement snapshots were inspected to verify that Python retrieves a captured Arduino state rather than directly reading continuously changing live arrays.

---

## Confidence Validation

Confidence outputs were visually compared against:

- Target status
- Signal strength
- Sigma
- Target detection
- Other quality measurements

---

## Dashboard Validation

The following were validated live:

- Sensor connection
- Browser connection
- Distance heatmap
- Confidence heatmap
- Three sector cards
- Zone identifier
- Confidence score
- Velocity
- Motion state
- JSON observation
- Observation history
- Backend version
- Dashboard version

---

# 40. Validation Results

The current implementation successfully demonstrates:

```text
VL53L5CX acquisition        ✅
Arduino initialization      ✅
15 Hz ranging configuration ✅
Snapshot capture            ✅
RouterBridge communication  ✅
64-zone distance data       ✅
64-zone quality data        ✅
Confidence calculation      ✅
Confidence heatmap          ✅
Trusted zone selection      ✅
Three-sector observation    ✅
Velocity estimation         ✅
Velocity smoothing          ✅
Motion classification       ✅
20-observation history      ✅
Web dashboard               ✅
JSON output                 ✅
```

Live testing also demonstrated measurements with high-confidence zones and zero-confidence zones existing simultaneously within the same frame.

This confirms that confidence computation is providing information distinct from distance alone.

---

# 41. Computational Characteristics

The Confidence Engine processes:

```text
64 zones per accepted snapshot
```

For each zone it performs:

- Validity checks
- Several normalization operations
- One logarithmic calculation for signal
- Weighted fusion

The computational complexity is:

```text
O(N)
```

where:

```text
N = 64
```

Sector extraction is also linear in the number of sensor zones.

The computational burden is therefore small relative to the UNO Q Linux-side processing capability.

The current performance limitation is primarily communication overhead rather than confidence computation.

---

# 42. Reliability Considerations

The current architecture improves reliability in several ways.

## Sensor Initialization Retries

Transient startup issues do not immediately result in permanent sensor failure.

---

## I²C Probe

Physical bus visibility can be distinguished from library initialization failure.

---

## Snapshot Buffers

Python reads a captured sensor state rather than independently sampling continuously changing live arrays.

---

## Array Validation

Incorrectly sized Bridge results are rejected.

---

## Frame Counter Validation

Duplicate and inconsistent snapshots are detected.

---

## Confidence Gates

Invalid sensor measurements are prevented from becoming trusted obstacle observations.

---

## Confidence-Aware Velocity

Invalid measurements do not produce relative-velocity calculations.

---

# 43. Design Decisions

## 43.1 Why Use Multiple Quality Signals?

No single measurement-quality variable completely characterizes ranging reliability.

Combining multiple available sensor signals provides a richer quality estimate.

---

## 43.2 Why Use Target Status as a Strong Signal?

Target status contains explicit sensor-provided validity information.

It therefore receives one of the highest weights.

---

## 43.3 Why Use Signal with a High Weight?

Strong returned signal generally provides useful information about measurement quality.

Signal therefore receives:

```text
30%
```

of the current confidence score.

---

## 43.4 Why Use Sigma?

Sigma directly represents ranging uncertainty and therefore receives:

```text
20%
```

of the current score.

---

## 43.5 Why Keep Other Components at 5%?

Ambient, reflectance, targets, and SPADs contribute useful supporting information without dominating the primary quality indicators.

---

## 43.6 Why Reject Other Target Statuses?

The exact confidence value for every lower-confidence target status is not currently established.

Assigning arbitrary values such as:

```text
0.2
0.3
0.4
```

would imply a degree of calibration that has not yet been performed.

The current conservative implementation therefore maps them to zero.

---

## 43.7 Why Select the Nearest Trusted Zone?

Obstacle avoidance remains distance-sensitive.

Among measurements considered valid, the nearest obstacle remains the most immediately relevant representative of the sector.

---

## 43.8 Why Use Latest-State Processing?

For assistive perception, recently captured environmental state is generally more useful than processing an increasingly delayed queue of historical sensor frames.

---

# 44. Design Trade-offs

## Multiple Bridge Calls

### Advantage

Simple RPC interface and clear separation of measurements.

### Disadvantage

Higher communication overhead and lower Python observation rate than the 15 Hz sensor acquisition rate.

---

## Snapshot Copy

### Advantage

Improves alignment of measurements read through multiple RPC calls.

### Disadvantage

Requires two complete sets of sensor buffers on the Arduino.

---

## Conservative Status Filtering

### Advantage

Reduces use of uncertain measurements.

### Disadvantage

Potentially useful lower-confidence measurements may be discarded.

---

## Heuristic Confidence

### Advantage

Provides immediately useful quality-aware perception.

### Disadvantage

The score is not yet statistically calibrated.

---

# 45. Current Limitations

## Single ToF Sensor

Only one VL53L5CX is currently used.

---

## Confidence Is Heuristic

The confidence value is an engineering quality score.

For example:

```text
Confidence = 85%
```

means:

```text
Current weighted quality score = 85 / 100
```

It does **not** mean:

```text
There is exactly an 85% probability
that the measured distance is correct.
```

Statistical calibration requires controlled ground-truth experiments.

---

## Raw Sensor Frames Are Not Recorded

The system does not retain all 15 Hz measurements.

Intermediate Arduino frames can be overwritten before Python reads them.

---

## No Persistent Storage

Measurements are not written to disk or a database.

---

## No Persistent Obstacle Tracking

The `persistence` field currently remains a placeholder.

---

## Relative Motion Only

Velocity represents change in measured range.

It is not complete object-state estimation.

---

## Snapshot Synchronization Has No Explicit Mutex

The snapshot mechanism copies live arrays into separate buffers, but the current implementation does not introduce an explicit locking primitive around live-buffer updates and snapshot copying.

The architecture has operated correctly during current testing, but stronger synchronization may be considered if future multi-threaded execution introduces evidence of concurrent modification.

---

## Single Target Used Per Zone

The current implementation uses:

```text
TARGET_INDEX = 0
```

with closest-target ordering.

Multi-target reasoning is not implemented.

---

# 46. Scalability

The Observation Engine has been designed so the current single-sensor implementation can later scale to multiple sensors.

Conceptually:

```text
ToF Sensor 1 ──► Observation Engine 1
ToF Sensor 2 ──► Observation Engine 2
ToF Sensor 3 ──► Observation Engine 3
ToF Sensor 4 ──► Observation Engine 4
ToF Sensor 5 ──► Observation Engine 5
ToF Sensor 6 ──► Observation Engine 6
                         │
                         ▼
                   Context Engine
```

Each sensor can independently produce a structured `ToFObservation`.

The Context Engine can later combine those observations without requiring raw sensor processing logic.

---

# 47. Extensibility

The current architecture supports several future improvements.

## Confidence Calibration

Replace heuristic reference values with experimentally calibrated functions.

---

## Raw Data Logger

Store Python-received complete snapshots for offline analysis.

Possible formats:

```text
CSV
Parquet
SQLite
NumPy
```

---

## High-Rate Transport

Reduce Bridge overhead by transferring an entire packed sensor frame through a smaller number of RPC calls.

---

## Arduino Ring Buffer

Store multiple 15 Hz sensor frames if future applications require complete frame retention.

---

## Persistence Engine

Determine whether obstacles remain consistently present over time.

---

## Multi-Sensor Confidence

Apply the same Confidence Engine independently to every ToF sensor.

---

# 48. Compatibility with Future Releases

The v2.2.1 observation model is designed as the perception interface for future modules.

Future processing can consume:

```text
distance
confidence
velocity
motion state
sensor quality
```

without directly accessing VL53L5CX raw arrays.

This supports:

```text
Observation Engine
        │
        ▼
Persistence
        │
        ▼
Context Engine
        │
        ▼
Attention Engine
        │
        ▼
Feedback Engine
```

---

# 49. Evolution of the Observation Engine

## v2.0.0

```text
Raw Distance
    │
    ▼
Sector Distance
    │
    ▼
Static Observation
```

---

## v2.1.0

```text
Raw Distance
    │
    ▼
Sector Distance
    │
    ▼
Observation History
    │
    ▼
Velocity
    │
    ▼
Motion State
```

---

## v2.2.1

```text
Complete Sensor Measurement
          │
          ▼
     Confidence Engine
          │
          ▼
   Trusted Measurement
          │
          ▼
Confidence-Aware Sector
          │
          ▼
   Observation History
          │
          ▼
       Velocity
          │
          ▼
     Motion State
```

This represents a transition from:

```text
Distance-based perception
```

to:

```text
Measurement-quality-aware perception
```

---

# 50. Future Evolution

The expected architectural progression is:

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
Confidence-Aware Observation
        │
        ▼
v2.3.0
Persistent Observation
        │
        ▼
v3.0.0
Multi-ToF Perception
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

---

## Persistence Engine

The next Observation Engine capability is expected to determine whether an obstacle remains consistently observable over time.

Instead of answering only:

```text
Is something present now?
```

the system should eventually answer:

```text
Has this obstacle remained consistently present?
```

---

## Multi-Sensor Perception

The architecture can then expand from one ToF sensor toward complete surrounding perception.

---

## Context Engine

Structured observations from several sensing directions can be combined into environmental context.

---

## Attention Engine

Context can be prioritized based on relevance and potential risk.

---

## Feedback Engine

Selected information can finally be converted into:

- Haptic guidance
- Spatial audio
- Navigation cues

---

# 51. Key Contributions

Version **v2.2.1** introduces the following major contributions to SixthSense.

### 1. Complete VL53L5CX Measurement Acquisition

The system now uses several quality signals instead of relying on distance alone.

### 2. Snapshot-Based Arduino Bridge

A dedicated live/snapshot architecture improves measurement alignment across multiple RouterBridge calls.

### 3. 64-Zone Confidence Engine

Every ranging zone receives an independent quality score.

### 4. Conservative Target-Status Validation

Sensor-provided target validity is incorporated directly into measurement acceptance.

### 5. Multi-Signal Confidence Fusion

Status, signal, sigma, ambient, reflectance, targets, and SPADs are combined into one quality metric.

### 6. Confidence-Aware Sector Selection

The Observation Engine selects the nearest trusted obstacle instead of simply selecting the nearest reported distance.

### 7. Confidence-Aware Temporal Processing

Invalid observations are excluded from relative-velocity estimation.

### 8. Source-Zone Traceability

Every sector observation reports the physical VL53L5CX zone associated with its measurement.

### 9. Improved Sensor Diagnostics

I²C probing, retries, and structured initialization codes improve startup debugging.

### 10. Confidence Visualization

The dashboard provides both distance and confidence heatmaps together with per-sector confidence information.

---

# 52. Design Summary

Version **v2.2.1** transforms SixthSense from a purely distance-and-motion-based perception system into a **measurement-quality-aware perception system**.

The complete current perception chain is:

```text
VL53L5CX
    │
    ▼
15 Hz Sensor Acquisition
    │
    ▼
Live Measurement Buffers
    │
    ▼
Snapshot
    │
    ▼
RouterBridge
    │
    ▼
Complete ToFFrame
    │
    ▼
Confidence Engine
    │
    ▼
64-Zone Confidence Map
    │
    ▼
Nearest Trusted Zone
    │
    ▼
SectorObservation
    │
    ▼
Temporal History
    │
    ▼
Relative Velocity
    │
    ▼
Motion State
    │
    ▼
ToFObservation
```

The release establishes an important distinction between:

```text
A sensor measurement
```

and:

```text
A trusted observation
```

This distinction is fundamental for future assistive perception.

The current system does not yet claim statistically calibrated measurement probabilities, persistent object tracking, environmental understanding, or navigation intelligence.

Instead, v2.2.1 establishes a clean and extensible foundation for those capabilities by ensuring that future reasoning layers receive structured observations containing not only:

```text
Where?
```

and:

```text
How is it moving?
```

but also:

```text
How much should this measurement be trusted?
```

---

# End of Document

**SixthSense v2.2.1**

**Confidence-Aware Temporal ToF Observation Engine**

**Observation → Confidence → Understanding → Attention → Feedback**
