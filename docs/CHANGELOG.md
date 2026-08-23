# Changelog

All notable changes to SixthSense are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-08-23

### Release name

**Multi-ToF Attention and Haptic Feedback Prototype**

### Overview

Version 3.0.0 is a major expansion from a single-sensor observation engine into a closed-loop Physical AI prototype. Six ToF sensors now create 18 temporal sector observations around the user. The new Attention Engine selects sustained approaching sectors, and the Feedback Engine converts them into a four-bit command for four directional vibration motors.

Several milestones from the earlier roadmap were integrated into this release rather than published as separate intermediate major versions. Version 3.0.0 remains the correct number because it directly follows v2.3.0 and matches the implementation's version identifiers.

### Added

#### Multi-ToF acquisition

- Added support for 6 × VL53L5CX sensors through an 8-channel I2C multiplexer.
- Added the fixed physical mapping:
  - T1 / CH0 / Front-right
  - T2 / CH1 / Front
  - T3 / CH2 / Front-left
  - T4 / CH5 / Rear-left
  - T5 / CH6 / Rear
  - T6 / CH7 / Rear-right
- Added 4×4 acquisition with 16 zones per sensor and 96 zones in each complete six-sensor observation.
- Added per-sensor initialization codes, ready flags, frame counters, timestamps, read-error counters, and FPS estimates.
- Added a six-sensor publication barrier: an observation is published only when every sensor has contributed a fresh frame.
- Added immutable published buffers that remain stable until Python consumes the observation.
- Added flattened RouterBridge transfer functions for distance, signal, sigma, target status, reflectance, ambient activity, target count, and enabled SPADs.

#### Multi-sensor observations

- Added sensor configuration and structured observation models for T1–T6.
- Added independent 20-observation histories for every sensor.
- Added independent five-value valid-velocity histories for every sensor-sector pair.
- Added 18 independent Motion Persistence Engine instances at sector scope through the six per-sensor observation engines.
- Added complete multi-sensor JSON serialization while retaining selected single-front-sensor compatibility fields.

#### Sector model

- Added three sectors to each oriented 4×4 image:
  - S0 = column 0
  - S1 = columns 1–2
  - S2 = column 3
- Added source-zone recovery for diagnostic display after orientation correction.
- Added nearest-valid-zone selection within each sector.

#### Attention Engine

- Added a deterministic `AttentionEngine` that examines all 18 sectors.
- Added the v3 activation rule:

  ```text
  velocity_state == Approaching
  AND motion_persistence >= 10
  ```

- Added `AttentionSource` and `AttentionDecision` data models.
- Added the complete 18-sector-to-motor mapping.
- Added bitwise-OR composition when several sectors request feedback at the same time.
- Added attention diagnostics containing the source sensor, sector, velocity state, persistence, mask, and motor names.

#### Feedback Engine

- Added a Python `FeedbackEngine` that sends requested motor masks through RouterBridge.
- Added mask-change detection and a 500 ms keep-alive refresh.
- Added MCU acknowledgement checking by comparing requested and returned masks.
- Added requested/applied masks and motor-name lists to the WebUI payload.
- Added throttled Bridge error reporting and keep-alive-interval retry behavior.

#### Haptic motor control

- Added four PWM outputs:
  - M1 / Front / bit 0 / `0x01` / D5
  - M2 / Left / bit 1 / `0x02` / D6
  - M3 / Rear / bit 2 / `0x04` / D9
  - M4 / Right / bit 3 / `0x08` / D10
- Added MCU RouterBridge endpoints `set_motor_mask` and `get_motor_mask`.
- Added mask validation that discards bits outside `0x0F`.
- Added a 1000 ms MCU watchdog that turns all active motors off when command refresh stops.
- Added startup initialization with all motor outputs off.

#### Dashboard

- Added six sensor overview cards with online state, FPS, frame number, and S0/S1/S2 distances.
- Added selectable T1–T6 detailed views.
- Added selected-sensor 4×4 distance and confidence heatmaps.
- Added full distance, confidence, source zone, velocity, velocity state, and persistence observations.
- Added a top-view M1–M4 haptic display.
- Added requested and MCU-applied mask displays.
- Added feedback health state and MCU-confirmed motor names.
- Added active attention-source rendering.
- Added six-sensor structured JSON output.
- Added responsive and accessible active, idle, waiting, unavailable, and fault motor states.

### Changed

- Changed sensing resolution from one 8×8 sensor to six 4×4 sensors.
- Changed total raw coverage from 64 zones to 96 zones.
- Changed the logical observation count from 3 sectors to 18 sectors.
- Increased each motion-state persistence counter maximum from 100 to 200.
- Set the tested attention activation threshold to 10 observations.
- Changed the main WebUI data contract from single-sensor top-level data to `sensors`, `attention`, and `feedback` objects.
- Changed acquisition transport from a single snapshot to a synchronized ready/read/consume multi-sensor bridge.
- Capped dashboard publication to a lighter 10 Hz while allowing the observation pipeline to process available observations.

### Preserved

- Preserved confidence-aware validity and sector selection.
- Preserved the confidence weighting model from v2.2.1/v2.3.0 pending new 4×4 calibration.
- Preserved valid-only velocity smoothing and explicit `Unknown` handling.
- Preserved observation-based persistence reinforcement and decay semantics.
- Preserved modular separation between acquisition, observation, attention, feedback, and visualization.

### Safety

- Motor outputs are intended for motor-driver inputs only; motors must not be connected directly to Arduino GPIO pins.
- Added a fail-safe motor-command watchdog on the MCU.
- All motor masks are constrained to four valid bits.
- Feedback status distinguishes the requested decision from the MCU-applied state.

### Validation

- Confirmed successful prototype motor activation with a persistence threshold of 10; further tuning remains planned.
- Recorded an approximate retrieved sensor rate of 14 Hz in the tested acquisition configuration.
- Confirmed Python syntax compilation.
- Confirmed JavaScript syntax with `node --check`.
- Confirmed that the submitted JavaScript, HTML, sketch, and CSS match the `develop` branch after line-ending normalization.

### Known limitations

- Confidence remains a heuristic quality score rather than a calibrated probability.
- Persistence is observation-count based rather than elapsed-time normalized.
- Velocity is relative range change and can be affected by user or sensor motion.
- No object identity, cross-sensor object fusion, Time-to-Collision, or trained ML inference is included.
- Simultaneous qualifying sectors are combined; they are not ranked by urgency.
- Motor intensity is fixed rather than proportional to distance or risk.
- This is a research prototype, not a certified assistive or safety device.

### Migration notes

- v3 consumers should read `message["sensors"]`, `message["attention"]`, and `message["feedback"]`.
- Existing consumers that assume one 8×8 `image` should migrate to the six 4×4 sensor payloads.
- Hardware requires an I2C multiplexer and four motor-driver channels in addition to the six ToF sensors and four vibration motors.
- Review the complete release documentation in `docs/SixthSense_v3.0.0.md` before tagging.

## [2.3.0] - 2026-08-09

### Release name

**Persistent ToF Observation Engine**

### Added

- Added explicit velocity validity and an `Unknown` state for unavailable velocity.
- Added valid-only velocity smoothing.
- Added independent Approaching, Stationary, and Receding persistence counters for every sector.
- Added bounded reinforcement and decay behavior in the range 0–100.
- Added motion-persistence fields and counter diagnostics to structured observations and the dashboard.

### Clarified

- Defined persistence as a temporal velocity-state evidence score rather than a percentage, probability, or object-tracking confidence.
- Clarified public SPAD-normalized signal and ambient field names.

See `docs/SixthSense_v2.3.0.md` for the full release design.

## [2.2.1] - 2026-08-08

### Release name

**Confidence-Aware Temporal ToF Observation Engine**

### Added

- Added acquisition of the full set of VL53L5CX quality signals.
- Added per-zone engineering confidence estimation.
- Added confidence-aware nearest-obstacle selection.
- Added confidence heatmap and quality diagnostics.

### Changed

- Rejected invalid measurements before they entered the temporal observation path.
- Clarified that confidence is a heuristic measurement-quality score, not a calibrated probability.

See `docs/SixthSense_v2.2.1.md` for the full release design.

## [2.1.0] - 2026-07-26

### Release name

**Temporal ToF Observation Engine**

### Added

- Added per-sector temporal observation history.
- Added relative range-velocity estimation.
- Added velocity smoothing and Approaching, Stationary, and Receding classification.
- Added temporal observation data to the dashboard.

See `docs/SixthSense_v2.1.0.md` for the full release design.

## [2.0.0] - 2026-07-01

### Release name

**Static ToF Observation Engine**

### Added

- Established the observation-first architecture.
- Added VL53L5CX ranging, three logical sectors, structured observations, RouterBridge transport, and a real-time dashboard.

See `docs/SixthSense_v2.0.0.md` for the full release design.
