# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by **Keep a Changelog**, and the project follows **Semantic Versioning**.

---
# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by **Keep a Changelog**, and the project follows **Semantic Versioning**.

---

# [2.3.0] - 2026-08-09

## Overview

Version **2.3.0** introduces the **Persistent ToF Observation Engine**, extending the Confidence-Aware Temporal ToF Observation Engine introduced in v2.2.1.

The major capability added in this release is the **Motion Persistence Engine**.

SixthSense can now preserve bounded temporal evidence for the three velocity-derived motion classifications:

```text
Approaching
Stationary
Receding
```

rather than reporting only the current instantaneous velocity state.

This release introduces:

- Explicit velocity validity
- `Unknown` velocity state for unavailable velocity
- Valid-only velocity smoothing
- Motion Persistence Engine
- Independent Approaching / Stationary / Receding persistence counters
- Bounded persistence range from `0` to `100`
- General decay behavior for `Unknown` or other classifications
- Motion persistence in structured `SectorObservation` output
- Motion persistence counter diagnostics in JSON
- Updated sector cards with **Velocity State**
- Updated dashboard with **Motion Persistence**
- Clearer public sensor-quality field names
- Updated v2.3.0 README and Software Architecture & Design documentation

The release preserves the existing **Observation-First Architecture** and all v2.2.1 confidence-aware sensing capabilities.

The Persistence Engine operates on velocity classifications and intentionally does **not** implement object identity tracking, obstacle-presence probability, or statistical persistence probability.

---

## Added

### Motion Persistence Engine

Added a dedicated Python-side `MotionPersistenceEngine`.

The engine maintains independent bounded temporal evidence for:

```text
Approaching
Stationary
Receding
```

for every logical sector.

Each sector therefore owns three counters:

```text
Approaching Persistence
Stationary Persistence
Receding Persistence
```

The counters are initialized to:

```text
0
```

and constrained to:

```text
0 ... 100
```

Configuration:

```text
MOTION_PERSISTENCE_MIN  = 0
MOTION_PERSISTENCE_MAX  = 100
MOTION_PERSISTENCE_STEP = 1
```

The Persistence Engine is executed after velocity-state classification.

The v2.3.0 temporal pipeline is:

```text
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

---

### Persistence Update Rules

Added deterministic counter reinforcement and decay rules.

#### Approaching

When:

```text
velocity_state = Approaching
```

the counters are updated as:

```text
Approaching += 1
Stationary  -= 1
Receding    -= 1
```

#### Stationary

When:

```text
velocity_state = Stationary
```

the counters are updated as:

```text
Approaching -= 1
Stationary  += 1
Receding    -= 1
```

#### Receding

When:

```text
velocity_state = Receding
```

the counters are updated as:

```text
Approaching -= 1
Stationary  -= 1
Receding    += 1
```

#### Unknown / Other

For any classification outside:

```text
Approaching
Stationary
Receding
```

all recognized counters decay:

```text
Approaching -= 1
Stationary  -= 1
Receding    -= 1
```

Every counter update is saturated to:

```text
0 ... 100
```

---

### Current-State Motion Persistence

Added:

```text
motion_persistence
```

to each sector observation.

The published value corresponds to the counter for the **current recognized velocity state**.

Example:

```text
Velocity State     = Approaching

Approaching counter = 80
Stationary counter  = 3
Receding counter    = 0
```

The sector publishes:

```text
Motion Persistence = 80
```

If the velocity state is:

```text
Unknown
```

the published current-state persistence is:

```text
motion_persistence = 0
```

while the internal recognized-state counters decay.

---

### Motion Persistence Counter Diagnostics

Added all three internal persistence counters to structured JSON output.

Example:

```json
"motion_persistence": 100,
"motion_persistence_counters": {
    "approaching": 0,
    "stationary": 100,
    "receding": 0
}
```

These counters are exposed for:

- Validation
- Debugging
- Transition analysis
- Future Context Engine integration
- Future persistence tuning

The dashboard sector cards display only the current:

```text
Motion Persistence
```

value to avoid unnecessary UI clutter.

---

### Explicit Velocity Validity

Added:

```text
velocity_valid
```

to `SectorObservation`.

A velocity is considered valid only when the current and previous sector observations both contain usable trusted measurements.

The current validity gate requires:

```text
current.distance_mm > 0
previous.distance_mm > 0
current.confidence > 0
previous.confidence > 0
```

A valid velocity is represented as:

```text
velocity_valid = true
```

An unavailable velocity is represented as:

```text
velocity_valid = false
```

This distinguishes:

```text
velocity_mmps = 0.0
velocity_valid = true
```

from:

```text
velocity_mmps = 0.0
velocity_valid = false
```

The first case represents a valid near-zero range velocity.

The second case represents an unavailable velocity calculation.

---

### `Unknown` Velocity State

Added:

```text
Unknown
```

as an explicit velocity state.

The recognized states are now:

```text
Approaching
Stationary
Receding
Unknown
```

When:

```text
velocity_valid = false
```

the velocity state becomes:

```text
Unknown
```

rather than interpreting the placeholder numerical velocity:

```text
0.0
```

as:

```text
Stationary
```

This prevents invalid measurement transitions from artificially strengthening Stationary motion persistence.

---

### Valid-Only Velocity Smoothing

Changed the velocity smoothing input so that only valid calculated velocity samples enter the per-sector history.

Each sector continues to use:

```text
VELOCITY_WINDOW = 5
```

but an invalid transition now performs:

```text
velocity_mmps = 0.0
velocity_valid = false
```

without appending that placeholder zero to the smoothing history.

This prevents unavailable velocity values from biasing the moving average toward zero.

The current implementation does **not** explicitly clear previously stored valid velocity samples when an invalid transition occurs.

The current invalid frame does not use the stored smoothed value, but older valid samples remain in the deque and can contribute after valid velocity processing resumes.

---

### Motion Classification Constants

Added explicit motion-state constants:

```text
MOTION_APPROACHING
MOTION_STATIONARY
MOTION_RECEDING
MOTION_UNKNOWN
```

and the recognized-state collection:

```text
MOTION_STATES
```

This centralizes velocity-state semantics and provides a stable input contract for the Persistence Engine.

---

### Extended `SectorObservation`

Extended `SectorObservation` with temporal-state fields.

The v2.3.0 sector model includes:

```text
velocity_mmps
velocity_valid
velocity_state

motion_persistence

approaching_persistence
stationary_persistence
receding_persistence
```

The three per-state persistence values are maintained internally and serialized through:

```text
motion_persistence_counters
```

---

### Motion Persistence Dashboard Display

Added Motion Persistence to every sector card.

Each sector now displays:

```text
Distance
Confidence
Zone
Velocity
Velocity State
Motion Persistence
```

Example:

```text
Distance             617 mm
Confidence            81.3 % HIGH
Zone                  63
Velocity              -5.0 mm/s
Velocity State        Stationary
Motion Persistence    100
```

Motion Persistence is intentionally displayed **without a percentage symbol**.

---

### `Unknown` Dashboard Presentation

Added dashboard handling for:

```text
Unknown
```

velocity state.

Unknown velocity is presented as a neutral state rather than being displayed as Stationary.

When:

```text
velocity_valid = false
```

the dashboard can avoid presenting the placeholder zero as a valid physical velocity.

---

### Explicit Public Signal Naming

Improved public sector-observation field names for VL53L5CX SPAD-normalized rates.

Changed:

```text
signal
```

to:

```text
signal_kcps_per_spad
```

and:

```text
ambient
```

to:

```text
ambient_kcps_per_spad
```

in the public sector observation interface.

This makes the meaning and units of these sensor-quality fields more explicit.

The lower-level `ToFFrame` and Arduino Bridge interfaces continue to use their existing internal names.

---

### v2.3.0 Software Architecture Documentation

Added:

```text
docs/SixthSense_v2.3.0.md
```

documenting:

- Persistent ToF Observation Engine architecture
- Velocity validity
- Valid-only velocity smoothing
- Velocity-state classification
- Motion Persistence Engine
- Persistence counter model
- Persistence update rules
- Unknown-state handling
- Confidence-to-persistence relationship
- Sector-level persistence semantics
- Observation-based persistence
- Runtime architecture
- Data models
- Public observation schema
- Validation strategy
- Design decisions
- Trade-offs
- Known limitations
- Future multi-sensor evolution

---

### Updated Project README

Updated the project README for:

```text
v2.3.0 — Persistent ToF Observation Engine
```

The README now describes:

- Motion persistence
- Velocity validity
- Unknown velocity state
- Per-state persistence counters
- Updated processing pipeline
- Updated dashboard
- Updated structured JSON
- Updated roadmap
- Updated current capabilities
- Updated limitations
- Multi-ToF integration as the next major milestone

---

## Changed

### Temporal Observation Pipeline

Changed the temporal processing pipeline from:

```text
Velocity Estimation
        │
        ▼
Velocity Smoothing
        │
        ▼
Motion Classification
        │
        ▼
Observation History
```

to:

```text
Velocity Estimation
        │
        ▼
Velocity Smoothing
        │
        ▼
Velocity State Classification
        │
        ▼
Motion Persistence
        │
        ▼
Observation History
```

Persistence is therefore calculated from the finalized current velocity classification before the observation is stored in temporal history.

---

### Velocity Processing

Changed invalid velocity handling.

Previously, an invalid current/previous measurement transition could produce:

```text
velocity = 0.0
```

which could enter the velocity smoothing history.

Version 2.3.0 now distinguishes:

```text
velocity_mmps
```

from:

```text
velocity_valid
```

and only valid calculated velocity samples are appended to the velocity history.

---

### Motion State Terminology

Standardized the public classification field as:

```text
velocity_state
```

and the dashboard label as:

```text
Velocity State
```

instead of the generic dashboard label:

```text
State
```

This makes it explicit that:

```text
Approaching
Stationary
Receding
Unknown
```

are derived from relative velocity.

---

### Persistence Terminology

Replaced the generic persistence concept with the explicit field:

```text
motion_persistence
```

The generic:

```text
persistence
```

field is no longer required in the final v2.3.0 public observation schema.

This avoids ambiguity between:

- Motion persistence
- Object persistence
- Occupancy persistence
- Measurement persistence

---

### Observation JSON

Changed the public sector JSON toward the v2.3.0 schema.

Example:

```json
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
```

Removed the need for duplicate public fields such as:

```text
motion_state
persistence
```

when the same information is already represented by:

```text
velocity_state
motion_persistence
```

---

### Dashboard

Updated the dashboard version to:

```text
v2.3.0
```

and extended the three sector cards with:

```text
Motion Persistence
```

Changed the card label:

```text
State
```

to:

```text
Velocity State
```

The existing:

- Sensor information
- Distance heatmap
- Confidence heatmap
- Observation history
- JSON viewer
- System status
- Debug information

remain part of the dashboard.

---

### Roadmap

Updated the roadmap to mark the persistence milestone complete.

Previous:

```text
v2.3.0
Persistent ToF Observation Engine
        🚧
```

Current:

```text
v2.3.0
Persistent ToF Observation Engine
        ✅
```

The next major milestone is now:

```text
v3.0.0
Multi-ToF Sensor Integration
```

---

### Persistence Definition

Refined the meaning of persistence from a generic future obstacle-presence concept to the actual v2.3.0 implementation:

```text
Temporal consistency of velocity classification
within each logical sector
```

Version 2.3.0 does **not** claim:

```text
same physical object persistence
```

or:

```text
persistent obstacle identity
```

---

## Fixed

### Invalid Zero Velocity Interpretation

Fixed the semantic ambiguity where an unavailable velocity could be numerically represented as:

```text
0.0
```

and therefore appear equivalent to genuine Stationary motion.

Version 2.3.0 adds:

```text
velocity_valid
```

so unavailable velocity becomes:

```text
Unknown
```

instead.

---

### Invalid Velocity Smoothing Bias

Fixed invalid placeholder zero velocities entering the smoothing history.

Previously:

```text
valid approaching samples
+
invalid 0.0
```

could reduce the magnitude of the smoothed velocity.

Version 2.3.0 only appends valid calculated velocity samples.

---

### Persistence Strengthening from Invalid Velocity

Prevented invalid/unavailable velocity from strengthening:

```text
Stationary
```

persistence.

The new flow is:

```text
Invalid velocity
       │
       ▼
velocity_valid = false
       │
       ▼
velocity_state = Unknown
       │
       ▼
A -1
S -1
R -1
```

---

### Ambiguous Persistence Field

Removed the need to expose both:

```text
motion_persistence
```

and:

```text
persistence
```

for the same value.

The v2.3.0 public interface uses:

```text
motion_persistence
```

only.

---

### Duplicate Motion-State Naming

Removed the need to expose both:

```text
velocity_state
```

and:

```text
motion_state
```

for the same classification.

The final public terminology is:

```text
velocity_state
```

---

### Dashboard State Label

Changed the ambiguous:

```text
State
```

label to:

```text
Velocity State
```

to clearly identify the origin of the classification.

---

### Sensor-Quality Field Naming

Improved the public JSON names:

```text
signal
ambient
```

to:

```text
signal_kcps_per_spad
ambient_kcps_per_spad
```

to better communicate the meaning of the values.

---

## Performance

### Persistence Engine Complexity

Motion persistence is calculated for:

```text
3 sectors
```

with:

```text
3 counters per sector
```

for each processed observation.

The work per update is therefore approximately:

```text
3 sectors × 3 bounded counter updates
```

and is negligible relative to RouterBridge communication overhead.

---

### Velocity Smoothing

Each sector continues to use a maximum of:

```text
5 valid velocity samples
```

for moving-average smoothing.

Invalid samples are excluded from the history.

---

### Observation History

The Observation Engine continues to retain:

```text
20 ToFObservation objects
```

for temporal processing.

---

### Sensor Acquisition Rate

The VL53L5CX continues to operate at:

```text
15 Hz
```

with:

```text
20 ms
```

integration time.

---

### Python Observation Rate

The effective Python observation rate remains lower than the configured sensor ranging rate because a snapshot requires multiple RouterBridge operations.

The Persistence Engine operates at the **processed observation rate**, not directly at 15 Hz.

---

### Persistence Is Observation-Based

Persistence increments or decrements once for every processed observation.

Therefore:

```text
Motion Persistence = 100
```

does not represent:

```text
100 seconds
```

or:

```text
100%
```

At approximately:

```text
5 observations / second
```

100 consecutive reinforcing observations require approximately:

```text
20 seconds
```

At approximately:

```text
6 observations / second
```

the same counter saturation requires approximately:

```text
16.7 seconds
```

No time normalization is implemented in v2.3.0.

---

## Data Retention

### Arduino Sensor Data

Arduino storage remains unchanged.

The MCU retains:

```text
Latest LIVE frame
+
Latest SNAPSHOT frame
```

No Arduino-side historical frame queue is introduced by v2.3.0.

---

### Python Observation History

Python continues to store:

```text
20 ToFObservation objects
```

in memory.

---

### Velocity History

Python stores up to:

```text
5 valid velocity samples
```

per sector.

Invalid placeholder zero velocities are not added.

Existing valid velocity history is currently retained across invalid transitions.

---

### Motion Persistence State

Added in-memory persistence state:

```text
3 motion counters
×
3 sectors
=
9 counters
```

These counters are maintained for the lifetime of the running application.

---

### Persistent Storage

Version 2.3.0 does not write persistence or sensor history to:

- CSV
- JSON files
- SQLite
- Database
- Cloud storage
- Long-term local storage

All temporal state is reset when the application restarts.

---

## Compatibility

### Hardware

Version 2.3.0 remains compatible with the current prototype hardware:

- Arduino UNO Q
- SparkFun VL53L5CX Time-of-Flight Sensor
- Qwiic / I²C interface
- USB-C connection

No hardware changes are required for the Motion Persistence Engine.

---

### Arduino Firmware

No persistence-specific change is required to the Arduino sketch.

The existing v2.2.1 snapshot and RouterBridge interfaces remain sufficient because motion persistence is derived entirely from Python-side temporal observations.

---

### Sensor Configuration

| Parameter | Value |
|-----------|------:|
| Resolution | 8 × 8 |
| Number of Zones | 64 |
| Ranging Frequency | 15 Hz |
| Integration Time | 20 ms |
| Target Order | Closest |
| Target Index | 0 |
| I²C Address | `0x29` |
| I²C Clock | 400 kHz |

---

### Software

The release continues to use:

- Arduino App Lab
- Arduino RouterBridge
- SparkFun VL53L5CX Arduino Library
- Python
- NumPy
- Arduino App Lab WebUI
- HTML
- CSS
- JavaScript
- Socket.IO

---

## Known Limitations

### Single ToF Sensor

The current prototype still uses:

```text
1 × VL53L5CX
```

Multi-ToF integration is planned for v3.0.0.

---

### Motion Persistence Is Not Object Tracking

The Persistence Engine maintains:

```text
velocity-state consistency per sector
```

It does not maintain:

```text
physical object identity
```

Two different objects observed successively inside the same sector can therefore contribute to the same sector persistence state.

---

### Zone Changes Do Not Reset Persistence

Persistence is indexed by:

```text
sector_id
```

rather than:

```text
zone_id
```

A change in the nearest trusted source zone within the same logical sector does not automatically reset persistence.

---

### Persistence Is Not Probability

A value such as:

```text
Motion Persistence = 80
```

does not mean:

```text
80% probability
```

The score is a bounded temporal evidence counter.

---

### Persistence Is Not Time-Normalized

Counter evolution depends on the effective Python observation-processing rate.

---

### Velocity Is Relative Range Change

Velocity continues to represent:

```text
change in measured sensor-to-obstacle distance
```

rather than a complete object velocity vector.

---

### Velocity History Across Invalid Gaps

Invalid velocity samples are excluded from smoothing.

However, previously stored valid velocity samples are not explicitly cleared by an invalid transition in the current implementation.

They can therefore contribute when valid velocity processing resumes.

---

### Heuristic Confidence

The Confidence Engine remains an engineering measurement-quality model rather than a statistically calibrated probability model.

---

### Single Target Per Zone

The current implementation continues to use:

```text
TARGET_INDEX = 0
```

with closest-target ordering.

---

### Raw Frame Retention

Not every sensor frame produced at 15 Hz is retained or processed by Python.

---

### Persistent Storage

Persistence counters and observation histories are stored only in memory.

---

### Snapshot Locking

The snapshot-copy architecture still does not use an explicit mutex around live-buffer update and snapshot-copy operations.

---

## Validation

Version 2.3.0 has been validated through live operation of the SixthSense dashboard and structured observations.

Validated functionality includes:

- VL53L5CX initialization
- Continuous 8×8 ranging
- Snapshot-based Bridge transport
- 64-zone confidence calculation
- Confidence-aware sector selection
- Relative velocity estimation
- Explicit velocity validity
- Valid near-zero velocity handling
- `Unknown` velocity state
- Valid-only velocity smoothing
- Approaching classification
- Stationary classification
- Receding classification
- Motion Persistence Engine updates
- Approaching persistence counter
- Stationary persistence counter
- Receding persistence counter
- Counter floor at `0`
- Counter saturation at `100`
- Per-sector persistence independence
- Motion persistence in JSON output
- Velocity State dashboard display
- Motion Persistence dashboard display
- Distance heatmap
- Confidence heatmap
- Live structured JSON observations
- Backend version display
- Dashboard version display

Recommended regression cases include:

```text
Continuous Approaching
Continuous Stationary
Continuous Receding
Single-state glitch
Sustained A → S transition
Sustained A → R transition
Unknown / invalid velocity
Counter saturation
Counter floor
Cross-sector independence
Zone change within same sector
Recovery after invalid measurement
```

---

## Architectural Evolution

The Observation Engine has now evolved through four major stages.

### v2.0.0

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

### v2.1.0

```text
Raw Distance
    │
    ▼
Sector Observation
    │
    ▼
Observation History
    │
    ▼
Relative Velocity
    │
    ▼
Motion State
```

---

### v2.2.1

```text
Complete VL53L5CX Measurement
             │
             ▼
      Confidence Engine
             │
             ▼
     Confidence Image
             │
             ▼
      Trusted Zones
             │
             ▼
Nearest Trusted Sector Measurement
             │
             ▼
      Temporal History
             │
             ▼
     Relative Velocity
             │
             ▼
        Motion State
```

---

### v2.3.0

```text
Complete VL53L5CX Measurement
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
     Relative Velocity
             │
             ▼
     Velocity Validity
             │
             ▼
     Velocity Smoothing
             │
             ▼
       Velocity State
             │
             ▼
  Motion Persistence Engine
             │
             ▼
      ToFObservation
```

Version 2.3.0 therefore represents the transition from:

```text
Confidence-aware current-state perception
```

to:

```text
Confidence-aware temporal perception
with bounded motion-state memory
```

---

## Next Milestone

The next planned major capability is:

# **v3.0.0 — Multi-ToF Sensor Integration**

The objective is to scale the Observation-First Architecture from:

```text
1 ToF sensor
```

toward:

```text
Multiple independent ToF sensing directions
```

while preserving a consistent structured observation interface.

The planned progression is:

```text
v2.0.0
Static ToF Observation Engine
        │
        ▼
v2.1.0
Temporal ToF Observation Engine
        │
        ▼
v2.2.1
Confidence-Aware Temporal
ToF Observation Engine
        │
        ▼
v2.3.0
Persistent ToF Observation Engine
        │
        ▼
v3.0.0
Multi-ToF Sensor Integration
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

## Release Summary

Version **2.3.0** introduces temporal memory for SixthSense velocity classifications.

The current perception pipeline is:

```text
VL53L5CX
    │
    ▼
15 Hz Sensor Acquisition
    │
    ▼
Live Sensor Buffers
    │
    ▼
Snapshot Capture
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
Relative Velocity
    │
    ▼
Velocity Validity
    │
    ▼
Valid-Only Velocity Smoothing
    │
    ▼
Velocity State
    │
    ▼
Motion Persistence Engine
    │
    ├── Approaching Counter
    ├── Stationary Counter
    └── Receding Counter
    │
    ▼
ToFObservation
    │
    ▼
Persistent Observation Dashboard
```

This release establishes the distinction between:

```text
Current velocity classification
```

and:

```text
Temporal consistency of that classification
```

while deliberately avoiding claims of:

- Same-object tracking
- Object identity
- Statistical persistence probability
- Obstacle-presence probability

Version 2.3.0 completes the planned single-ToF persistence milestone and prepares SixthSense for the next architectural step:

```text
v3.0.0 — Multi-ToF Sensor Integration
```

---

# [2.2.1] - 2026-08-08

## Overview

Version **2.2.1** introduces the **Confidence-Aware Temporal ToF Observation Engine**, extending the temporal perception capabilities introduced in v2.1.0.

The Observation Engine now evaluates the quality of every VL53L5CX ranging zone using multiple sensor-provided measurement signals instead of relying on distance alone.

This release introduces:

- Complete VL53L5CX measurement acquisition
- Arduino-side snapshot-based sensor transport
- 64-zone confidence estimation
- Confidence-aware sector selection
- Sensor-quality metadata in observations
- Confidence-aware velocity processing
- Improved sensor initialization diagnostics
- Distance and confidence heatmap visualization
- Enhanced confidence-aware dashboard

The release preserves the existing **Observation-First Architecture** while improving measurement reliability and preparing the perception layer for future persistence and multi-sensor capabilities.

---

## Added

### Confidence Engine

Added per-zone confidence estimation for all **64 VL53L5CX zones**.

The Confidence Engine now produces a measurement-quality score in the range:

```text
0.0 – 100.0
```

The confidence calculation uses the following VL53L5CX measurement signals:

- Target status
- Signal per SPAD
- Range sigma
- Ambient per SPAD
- Reflectance
- Number of detected targets
- Number of enabled SPADs

The current confidence weights are:

| Measurement | Weight |
|-------------|-------:|
| Target Status | 30% |
| Signal per SPAD | 30% |
| Range Sigma | 20% |
| Ambient per SPAD | 5% |
| Reflectance | 5% |
| Targets Detected | 5% |
| SPADs Enabled | 5% |
| **Total** | **100%** |

The confidence model also introduces fundamental measurement validity gates.

A zone receives:

```text
Confidence = 0
```

when:

- Distance is invalid
- Distance exceeds the configured perception range
- No target is detected
- Target status is not accepted by the current validity model

The Confidence Engine produces a complete:

```text
8 × 8 confidence image
```

corresponding spatially to the 8×8 distance image.

---

### Target Status Handling

Added target-status interpretation based on VL53L5CX confidence guidance.

The current implementation uses:

| Target Status | Status Confidence |
|--------------:|------------------:|
| `5` | 100% |
| `6` | 50% |
| `9` | 50% |
| Other statuses | Conservatively rejected |

The normalized implementation is:

```text
Status 5
    ↓
   1.0

Status 6 or 9
    ↓
   0.5

Other Status
    ↓
   0.0
```

The VL53L5CX guidance identifies other statuses as having confidence below 50%.

Because exact confidence values are not available for each lower-confidence status, the current implementation intentionally avoids assigning arbitrary values.

This is a conservative engineering decision and can later be refined through sensor characterization.

---

### Complete VL53L5CX Measurement Acquisition

The Arduino firmware now acquires the complete set of sensor measurements required by the Confidence Engine.

For every ToF zone, SixthSense now retrieves:

- Distance
- Signal per SPAD
- Range sigma
- Target status
- Reflectance
- Ambient per SPAD
- Number of detected targets
- Number of enabled SPADs

The measurements are divided into two categories.

#### Per-Target Measurements

```text
distance_mm
signal_per_spad
range_sigma_mm
target_status
reflectance
```

The current implementation uses:

```text
TARGET_INDEX = 0
```

with:

```text
Target Order = Closest
```

The target index is calculated as:

```text
targetIndex =
    zone × VL53L5CX_NB_TARGET_PER_ZONE
    + TARGET_INDEX
```

#### Per-Zone Measurements

```text
ambient_per_spad
nb_target_detected
nb_spads_enabled
```

These measurements are indexed directly using the ToF zone number.

---

### Arduino Live Measurement Buffers

Added dedicated live measurement buffers on the Arduino.

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

These arrays contain the most recently acquired VL53L5CX sensor frame.

The Arduino also maintains:

```text
liveFrameCounter
liveTimestamp
```

The live buffers are continuously updated as new ToF frames become available.

---

### Arduino Snapshot Architecture

Added a second set of Arduino-side buffers specifically for Python data retrieval.

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

Snapshot metadata includes:

```text
snapshotFrameCounter
snapshotTimestamp
```

Added:

```text
capture_snapshot()
```

to copy the latest complete live sensor state into the snapshot buffers.

The architecture is:

```text
VL53L5CX
    │
    ▼
LIVE Buffers
    │
    │ capture_snapshot()
    ▼
SNAPSHOT Buffers
    │
    ▼
RouterBridge
    │
    ▼
Python
```

This architecture reduces the possibility of combining measurement arrays originating from different sensor frames.

---

### Arduino Bridge Interface

Added and expanded RouterBridge interfaces for diagnostics, snapshot control, metadata retrieval, and sensor-data transfer.

#### Diagnostics

```text
sensor_ready
get_sensor_init_code
get_live_frame_counter
get_snapshot_frame_counter
```

#### Snapshot Control

```text
capture_snapshot
```

#### Snapshot Metadata

```text
get_timestamp
```

#### Sensor Measurements

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

The interface separates:

```text
Continuous Arduino sensor acquisition
```

from:

```text
Python-side perception processing
```

---

### Snapshot Validation

Added Python-side snapshot validation.

The backend now checks:

- Arduino Bridge availability
- Sensor readiness
- Sensor initialization result
- Availability of the first ranging frame
- Snapshot frame number
- Snapshot metadata consistency
- Duplicate frames
- Array availability
- Expected 64-zone array size
- RouterBridge communication errors

The expected snapshot acquisition sequence is:

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
get_timestamp()
      │
      ▼
Read Sensor Arrays
      │
      ▼
Validate 64 Zones
      │
      ▼
Create ToFFrame
```

Duplicate snapshots are rejected using the frame counter.

---

### RouterBridge `uint8_t` Handling

Added support for RouterBridge returning Arduino `uint8_t` arrays as binary data.

The Python conversion layer now supports:

```text
bytes
bytearray
memoryview
list
tuple
NumPy-compatible arrays
```

Binary values are converted using:

```python
np.frombuffer()
```

before being reshaped into 8×8 NumPy arrays.

This resolves conversion failures for arrays such as:

```text
target_status
reflectance
nb_target_detected
```

---

### Complete `ToFFrame`

Extended the Python `ToFFrame` data model.

A complete frame now contains:

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

Each measurement is represented as an oriented:

```text
8 × 8 NumPy array
```

The `ToFFrame` represents one complete Python-side sensor snapshot.

---

### Confidence Normalization

Added normalized measurement-quality functions for all Confidence Engine inputs.

All quality components are converted into:

```text
0.0 – 1.0
```

before weighted fusion.

#### Signal

Reference:

```text
CONF_SIGNAL_REFERENCE = 1000
```

Normalization:

```text
signal_score =

log10(signal + 1)
-----------------
log10(1000 + 1)
```

Signal uses logarithmic normalization because sensor signal values can vary over a large numerical range.

---

#### Sigma

Reference:

```text
CONF_SIGMA_REFERENCE = 64
```

Normalization:

```text
sigma_score =

1 - sigma / 64
```

Lower ranging uncertainty results in a higher confidence contribution.

---

#### Ambient

Reference:

```text
CONF_AMBIENT_REFERENCE = 128
```

Normalization:

```text
ambient_score =

1 - ambient / 128
```

Lower ambient interference currently results in a higher confidence contribution.

---

#### Reflectance

Reference:

```text
CONF_REFLECTANCE_REFERENCE = 255
```

Normalization:

```text
reflectance_score =

reflectance / 255
```

---

#### Target Detection

Normalization:

```text
targets > 0
    ↓
1.0

targets = 0
    ↓
0.0
```

---

#### Enabled SPADs

Reference:

```text
CONF_SPADS_REFERENCE = 3840
```

Normalization:

```text
spad_score =

spads / 3840
```

All normalized values are clamped to:

```text
0.0 – 1.0
```

---

### Weighted Confidence Fusion

Added multi-signal confidence fusion.

The confidence score is calculated as:

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

The result is limited to:

```text
0 – 100
```

and rounded to one decimal place.

---

### Confidence Validity Gates

Added fundamental validity checks before weighted fusion.

A measurement immediately receives:

```text
Confidence = 0
```

when:

```text
distance <= 0
```

or:

```text
distance > 3000 mm
```

or:

```text
targets <= 0
```

or:

```text
status_score <= 0
```

These gates prevent fundamentally invalid measurements from receiving confidence purely from other quality signals.

---

### Confidence-Aware Sector Selection

Changed sector obstacle selection from:

```text
Nearest valid distance
```

to:

```text
Nearest trusted distance
```

A zone is rejected when:

```text
distance <= 0
```

or:

```text
distance > MAX_DISTANCE_MM
```

or:

```text
confidence <= 0
```

Rejected zones are internally replaced with:

```text
INVALID_DISTANCE_MM = 4000
```

during nearest-distance selection.

The new selection process is:

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

This prevents unreliable sensor measurements from becoming the primary sector obstacle simply because they report the smallest distance.

---

### Three-Sector Observation Model

Preserved the existing three-sector architecture.

The oriented 8×8 ToF frame is divided as:

```text
Columns

0   1 | 2   3   4 | 5   6   7
───────|───────────|───────────
Sector0|  Sector1  |  Sector2
```

Sector ranges are:

```text
Sector 0 → columns [0, 2)

Sector 1 → columns [2, 5)

Sector 2 → columns [5, 8)
```

Each sector produces one structured `SectorObservation`.

---

### Source Zone Identification

Added reporting of the original VL53L5CX zone associated with each selected sector observation.

Because the Python sensor image is horizontally flipped for display and sector orientation, the original raw sensor column is recovered using:

```text
raw_column =
    IMAGE_COLS
    - 1
    - oriented_column
```

The source zone is then calculated as:

```text
zone_id =
    row × IMAGE_COLS
    + raw_column
```

This provides measurement traceability between:

```text
Dashboard observation
```

and:

```text
Physical VL53L5CX sensor zone
```

---

### Extended `SectorObservation`

Extended each `SectorObservation` with sensor-quality information.

Each sector now contains:

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

All sensor-quality values correspond to the **same selected zone** as the reported distance.

This avoids combining:

```text
Distance from one zone
```

with:

```text
Quality data from another zone
```

---

### Confidence-Aware Velocity Estimation

Velocity estimation now validates measurement confidence.

Velocity is not calculated when either the current or previous observation contains:

```text
distance_mm <= 0
```

or:

```text
confidence <= 0
```

Instead:

```text
velocity = 0
```

This reduces artificial velocity spikes caused by invalid or unreliable measurements.

---

### Observation History

Preserved the temporal observation history introduced in v2.1.0.

The Observation Engine currently maintains:

```text
TOF_HISTORY_SIZE = 20
```

using:

```text
deque(maxlen=20)
```

The history contains processed:

```text
ToFObservation
```

objects.

It does **not** contain complete histories of all 64-zone raw sensor frames.

---

### Velocity Smoothing

Preserved velocity smoothing from v2.1.0.

Each sector maintains:

```text
VELOCITY_WINDOW = 5
```

recent velocity values.

Smoothed velocity is calculated using:

```text
Smoothed Velocity =

Sum of recent velocity samples
------------------------------
Number of velocity samples
```

---

### Motion State Classification

Preserved relative motion classification.

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

The velocity represents relative change in sensor-to-obstacle distance.

---

### Sensor Initialization Diagnostics

Added improved sensor initialization and startup diagnostics.

The new initialization sequence includes:

```text
Wire1.begin()
      │
      ▼
400 kHz I²C
      │
      ▼
Startup Delay
      │
      ▼
I²C Probe at 0x29
      │
      ▼
tof.begin()
      │
      ▼
8×8 Resolution
      │
      ▼
15 Hz Ranging Frequency
      │
      ▼
20 ms Integration Time
      │
      ▼
Closest Target Order
      │
      ▼
startRanging()
```

---

### Sensor Initialization Retry

Added repeated VL53L5CX initialization attempts.

Configuration:

```text
SENSOR_INIT_RETRIES = 10
```

with:

```text
SENSOR_RETRY_DELAY_MS = 500
```

The sensor is therefore probed and initialization is retried before startup is declared unsuccessful.

---

### I²C Sensor Probe

Added direct I²C probing at:

```text
0x29
```

This allows the firmware to distinguish between:

```text
No I²C response from sensor
```

and:

```text
I²C device detected but tof.begin() failed
```

This significantly improves hardware and driver debugging.

---

### Initialization Status Codes

Added structured sensor initialization diagnostic codes.

| Code | Meaning |
|-----:|---------|
| `0` | Initialization not completed |
| `1` | Sensor initialized successfully |
| `-1` | Sensor detection or `tof.begin()` failed |
| `-2` | 8×8 resolution configuration failed |
| `-3` | 15 Hz ranging frequency configuration failed |
| `-4` | 20 ms integration-time configuration failed |
| `-5` | `startRanging()` failed |

The Arduino Bridge diagnostic interface remains available even if sensor initialization fails.

This allows Python to report the specific failure condition.

---

### Distance Heatmap

Preserved the 8×8 distance heatmap.

The heatmap provides a spatial representation of measured obstacle distance.

Conceptually:

```text
Near
 │
 ▼
Red → Orange → Yellow → Green
                           ▲
                           │
                          Far
```

---

### Confidence Heatmap

Added a second 8×8 heatmap showing the confidence assigned to every corresponding sensor zone.

Conceptually:

```text
Low Confidence
      │
      ▼
     Red → Orange → Yellow → Green
                               ▲
                               │
                          High Confidence
```

Zones rejected by the confidence validity model appear as zero-confidence measurements.

The two heatmaps allow direct comparison between:

```text
What distance did the sensor report?
```

and:

```text
How much does the current system trust that measurement?
```

---

### Confidence-Aware Dashboard

Updated the dashboard to:

```text
SixthSense v2.2.1
```

The dashboard now displays:

- Sensor ID
- Sensor name
- Sensor status
- Frame number
- Timestamp
- Effective processing FPS
- Arduino Bridge status
- Browser status
- Observation history
- Three sector observation cards
- Distance
- Confidence
- Confidence classification
- Source zone
- Relative velocity
- Motion state
- 8×8 distance heatmap
- 8×8 confidence heatmap
- Live JSON observation
- Dashboard version
- Backend version

---

### Confidence Presentation Levels

Added dashboard-only confidence labels.

```text
Confidence >= 80%
        ↓
       HIGH
```

```text
50% <= Confidence < 80%
        ↓
      MEDIUM
```

```text
0% < Confidence < 50%
        ↓
       LOW
```

```text
Confidence = 0%
        ↓
      INVALID
```

These categories are presentation-only.

They do not modify the backend Confidence Engine calculation or obstacle-selection logic.

---

### Documentation

Updated project documentation for the new confidence-aware perception architecture.

Added:

- Updated project README
- Confidence Engine documentation
- Confidence normalization documentation
- Confidence weighting documentation
- Snapshot architecture documentation
- Arduino Bridge interface documentation
- Sensor initialization diagnostics documentation
- Sensor measurement retention explanation
- Sensor acquisition-rate versus Python processing-rate explanation
- Confidence-aware dashboard documentation
- `SixthSense_v2.2.1.md` Software Architecture & Design Document

---

## Changed

### Observation Engine

Extended the Temporal ToF Observation Engine introduced in v2.1.0.

Changed the primary perception pipeline from:

```text
Raw Distance
     │
     ▼
Sector Selection
     │
     ▼
Temporal Observation
```

to:

```text
Complete VL53L5CX Measurement
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
    Temporal Observation
```

The Observation Engine now considers both:

```text
Distance
```

and:

```text
Measurement Quality
```

before generating a sector observation.

---

### Sector Selection

Changed sector selection from:

```text
Nearest measured obstacle
```

to:

```text
Nearest trusted obstacle
```

This improves resistance to unreliable close-range measurements.

---

### Sensor Data Retrieval

Changed Arduino-to-Python sensor retrieval to use dedicated snapshot buffers.

Earlier conceptual access:

```text
Python
  │
  ├── Read distance
  ├── Read signal
  ├── Read sigma
  ├── Read status
  └── ...
```

could potentially span multiple changing live sensor frames.

The new architecture uses:

```text
LIVE Sensor State
       │
       ▼
capture_snapshot()
       │
       ▼
Frozen SNAPSHOT
       │
       ▼
Python Measurement Retrieval
```

---

### Arduino-to-Python Communication

The Arduino now continuously acquires sensor frames while Python consumes snapshots independently.

Sensor acquisition therefore no longer needs to stop while the full set of measurement arrays is retrieved.

---

### Sensor Observation Metadata

Sector observations now expose the source and quality of the selected measurement.

Added:

```text
zone_id
confidence
signal
sigma
target_status
reflectance
ambient
targets
spads
```

---

### Velocity Processing

Velocity estimation now incorporates confidence validity.

Untrusted measurements are excluded from relative-velocity calculation.

---

### Dashboard

Changed the dashboard description from:

```text
Temporal ToF Observation Engine
```

to:

```text
Temporal ToF Observation + Confidence Engine
```

Added explicit visualization of measurement reliability.

---

### Roadmap

Updated the planned release progression.

Previous roadmap:

```text
v2.2.0
Persistent ToF Observation Engine
```

Current progression:

```text
v2.2.1
Confidence-Aware Temporal ToF Observation Engine
        │
        ▼
v2.3.0
Persistent ToF Observation Engine
```

This reflects the addition of measurement confidence as a dedicated architectural milestone before persistence.

---

## Fixed

### Snapshot Consistency

Fixed inconsistent measurement retrieval across multiple RouterBridge calls by introducing dedicated snapshot buffers.

---

### `uint8_t` Bridge Conversion

Fixed Python conversion failures for Arduino `uint8_t` arrays serialized by RouterBridge as binary buffers.

Added explicit handling for:

```text
bytes
bytearray
memoryview
```

using:

```python
np.frombuffer()
```

---

### Sensor Initialization Reliability

Improved handling of transient VL53L5CX initialization failures.

Added:

- I²C probing
- Startup delay
- Repeated initialization attempts
- Diagnostic error codes

---

### Sensor Failure Diagnostics

Improved differentiation between:

```text
No sensor responding on I²C
```

and:

```text
Sensor visible on I²C but VL53L5CX driver initialization failed
```

---

### Duplicate Snapshot Processing

Added frame-counter validation to prevent the same snapshot from being processed repeatedly.

---

### Snapshot Metadata Validation

Added comparison between:

```text
capture_snapshot()
```

and:

```text
get_snapshot_frame_counter()
```

to detect snapshot metadata mismatch.

---

### Invalid Array Handling

Added checks requiring every sensor array to contain:

```text
64 values
```

before frame processing continues.

---

### Invalid Velocity Calculation

Prevented invalid or zero-confidence measurements from generating misleading velocity estimates.

---

### Dashboard Version Consistency

Fixed the frontend/backend version mismatch.

Both now report:

```text
v2.2.1
```

---

### Dashboard Resize Handling

Updated heatmap redraw behavior to retain the complete most recent backend message rather than attempting to retrieve image data from the processed observation object.

---

## Performance

### Sensor Acquisition Rate

The VL53L5CX is configured for:

```text
15 Hz
```

which corresponds to approximately:

```text
1 frame every 66.7 ms
```

---

### Continuous Arduino Acquisition

The Arduino continues acquiring new sensor measurements independently of the Python backend.

The live buffers always represent the latest successfully acquired sensor frame.

---

### Python Processing Rate

Python currently performs several RouterBridge calls for every processed snapshot.

Typical snapshot processing includes:

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

As a result, the effective Python observation rate may be lower than the underlying 15 Hz sensor ranging frequency.

---

### Latest-State Processing

The runtime architecture intentionally prioritizes:

```text
Newest available sensor state
```

rather than:

```text
Processing every historical sensor frame
```

This is appropriate for real-time assistive perception, where stale environmental measurements are generally less useful than the most recent available state.

---

### Confidence Engine Complexity

Confidence is calculated independently for:

```text
64 zones
```

per accepted Python snapshot.

The computational complexity is approximately:

```text
O(N)
```

where:

```text
N = 64
```

The primary runtime overhead is currently RouterBridge communication rather than confidence calculation.

---

## Data Retention

Version **2.2.1** does not store every raw sensor measurement produced by the VL53L5CX.

### Arduino Live Data

Arduino stores only the most recent sensor frame in the live buffers.

For example:

```text
Frame 100
    ↓
LIVE Buffers

Frame 101
    ↓
Overwrites Frame 100

Frame 102
    ↓
Overwrites Frame 101
```

There is currently no Arduino-side historical frame queue.

---

### Arduino Snapshot Data

Arduino also stores one captured snapshot.

```text
Latest LIVE Frame
        │
        │ capture_snapshot()
        ▼
Latest SNAPSHOT Frame
```

The snapshot is replaced when Python requests another snapshot.

---

### Python Raw Frame

Python creates a complete `ToFFrame` containing:

```text
64-zone distance
64-zone signal
64-zone sigma
64-zone status
64-zone reflectance
64-zone ambient
64-zone targets
64-zone SPADs
64-zone confidence
```

The complete raw frame is used temporarily for:

- Confidence calculation
- Sector extraction
- Dashboard rendering

The application does not currently retain a history of complete `ToFFrame` objects.

---

### Python Observation History

Python stores:

```text
20 ToFObservation objects
```

using:

```text
deque(maxlen=20)
```

Each stored observation contains the three processed sector observations.

It does not contain the complete 64-zone raw frame.

---

### Velocity History

Each sector maintains:

```text
5 recent velocity samples
```

for smoothing.

---

### Persistent Storage

Version 2.2.1 does not currently persist sensor measurements to:

- CSV
- JSON files
- SQLite
- Database
- Cloud storage
- Long-term local storage

All in-memory measurements and observation history are lost when the application stops.

---

### Unprocessed 15 Hz Frames

Because the sensor can produce frames faster than Python processes complete snapshots, some intermediate sensor frames may never reach Python.

Example:

```text
Arduino Sensor Frames

100
101
102
103
104
105
106
```

Python may process:

```text
100
103
106
```

while:

```text
101
102
104
105
```

are overwritten in the Arduino live buffers before Python captures them.

This behavior is intentional in the current real-time perception architecture.

---

## Compatibility

### Hardware

Version 2.2.1 has been developed and tested with:

- Arduino UNO Q
- SparkFun VL53L5CX Time-of-Flight Sensor
- Qwiic / I²C interface
- USB-C connection

---

### Sensor Configuration

| Parameter | Value |
|-----------|------:|
| Resolution | 8 × 8 |
| Number of Zones | 64 |
| Ranging Frequency | 15 Hz |
| Integration Time | 20 ms |
| Target Order | Closest |
| Target Index | 0 |
| I²C Address | `0x29` |
| I²C Clock | 400 kHz |

---

### Software

The release uses:

- Arduino App Lab
- Arduino RouterBridge
- SparkFun VL53L5CX Arduino Library
- Python
- NumPy
- Arduino App Lab WebUI
- HTML
- CSS
- JavaScript
- Socket.IO

---

## Known Limitations

### Single ToF Sensor

The current prototype uses:

```text
1 × VL53L5CX
```

Multi-sensor integration is planned for a future release.

---

### Single Target Per Zone

The current implementation uses:

```text
TARGET_INDEX = 0
```

with closest-target ordering.

Multi-target reasoning is not currently implemented.

---

### Heuristic Confidence

The confidence value is currently an **engineering measurement-quality score**.

For example:

```text
Confidence = 85%
```

means:

```text
Weighted Confidence Score = 85 / 100
```

It does **not** currently mean:

```text
There is exactly an 85% statistical probability
that the measured distance is correct.
```

Statistical calibration requires controlled ground-truth testing.

---

### Lower-Confidence Target Statuses

Target statuses outside:

```text
5
6
9
```

are currently treated conservatively as invalid.

Future calibration may assign more nuanced confidence values.

---

### Raw Frame Retention

Not every 15 Hz sensor frame is retained or processed by Python.

---

### Persistent Storage

No raw sensor measurements or observation histories are currently stored permanently.

---

### Persistence

Persistent obstacle tracking has not yet been implemented.

The existing:

```text
persistence
```

field remains:

```text
0.0
```

and is reserved for a future release.

---

### Relative Motion Only

Velocity represents:

```text
Change in measured sensor-to-obstacle distance
```

It does not independently distinguish between:

- User motion
- Sensor motion
- Object motion
- Combined relative motion

---

### Snapshot Locking

The snapshot-copy architecture currently does not use an explicit mutex around live-buffer updates and snapshot copying.

Current live testing has not demonstrated a coherence problem.

Stronger synchronization can be introduced later if future execution models demonstrate a need for it.

---

### RouterBridge Overhead

Retrieving multiple sensor arrays through individual RouterBridge calls reduces the Python-side processing rate relative to the underlying sensor acquisition rate.

A future optimization may transfer an entire sensor frame using fewer Bridge transactions.

---

## Validation

Version 2.2.1 has been validated through live operation using the Arduino UNO Q and SparkFun VL53L5CX.

Validated functionality includes:

- VL53L5CX initialization
- I²C device detection
- Initialization retries
- 8×8 ranging
- 15 Hz sensor configuration
- 20 ms integration time
- Continuous Arduino acquisition
- Distance acquisition
- Signal acquisition
- Sigma acquisition
- Target-status acquisition
- Reflectance acquisition
- Ambient acquisition
- Target-count acquisition
- SPAD acquisition
- Snapshot-based Bridge transport
- 64-zone confidence calculation
- Confidence validity filtering
- Confidence-aware sector selection
- Source-zone recovery
- Observation history
- Relative velocity estimation
- Velocity smoothing
- Motion-state classification
- Distance heatmap
- Confidence heatmap
- Sector confidence display
- Live JSON observations
- Arduino Bridge status
- Browser connection status
- Backend version display
- Dashboard version display

---

## Architectural Evolution

The Observation Engine has evolved through three major stages.

### v2.0.0

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

### v2.1.0

```text
Raw Distance
    │
    ▼
Sector Observation
    │
    ▼
Observation History
    │
    ▼
Relative Velocity
    │
    ▼
Motion State
```

---

### v2.2.1

```text
Complete VL53L5CX Measurement
             │
             ▼
      Confidence Engine
             │
             ▼
     Confidence Image
             │
             ▼
      Trusted Zones
             │
             ▼
Nearest Trusted Sector Measurement
             │
             ▼
      Temporal History
             │
             ▼
     Relative Velocity
             │
             ▼
        Motion State
```

Version 2.2.1 therefore represents the transition from:

```text
Distance-based perception
```

to:

```text
Measurement-quality-aware perception
```

---

## Next Milestone

The next planned Observation Engine capability is:

# **v2.3.0 — Persistent ToF Observation Engine**

The objective will be to determine whether a trusted obstacle remains consistently observable across multiple temporal observations.

The system currently answers:

```text
Is a trusted obstacle present right now?
```

The Persistence Engine is expected to additionally answer:

```text
Has this obstacle remained consistently present over time?
```

The planned architectural progression is:

```text
v2.0.0
Static ToF Observation Engine
        │
        ▼
v2.1.0
Temporal ToF Observation Engine
        │
        ▼
v2.2.1
Confidence-Aware Temporal
ToF Observation Engine
        │
        ▼
v2.3.0
Persistent ToF Observation Engine
        │
        ▼
v3.0.0
Multi-ToF Sensor Integration
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

## Release Summary

Version **2.2.1** establishes a critical distinction inside SixthSense between:

```text
A measured distance
```

and:

```text
A trusted observation
```

The current perception pipeline is:

```text
VL53L5CX
    │
    ▼
15 Hz Sensor Acquisition
    │
    ▼
Live Sensor Buffers
    │
    ▼
Snapshot Capture
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
Temporal Observation History
    │
    ▼
Relative Velocity
    │
    ▼
Motion State
    │
    ▼
ToFObservation
    │
    ▼
Confidence-Aware Dashboard
```

This release establishes the measurement-quality foundation required for future:

- Persistence
- Multi-sensor perception
- Environmental context
- Attention modelling
- Assistive feedback generation

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
