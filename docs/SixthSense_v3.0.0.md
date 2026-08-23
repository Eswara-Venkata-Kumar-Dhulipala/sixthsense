# SixthSense v3.0.0

## Multi-ToF Attention and Haptic Feedback Prototype

| Field | Value |
|---|---|
| Version | **3.0.0** |
| Release name | **Multi-ToF Attention and Haptic Feedback Prototype** |
| Release type | Major architectural release |
| Target platform | Arduino UNO Q |
| License identifier | MPL-2.0 |

## Version decision

The correct release number is **v3.0.0**.

The latest documented release on `main` is v2.3.0, while the current firmware, Python backend, JavaScript, HTML, and CSS already identify the implementation as 3.0.0. The `develop` branch introduces a major incompatible expansion from one sensor and three sectors to six sensors and eighteen sectors, while also closing the loop through attention selection and physical haptic feedback.

The earlier roadmap allocated separate future numbers to multi-sensor perception, context, attention, and feedback. During development, several planned capabilities were integrated together. Keeping this release at v3.0.0:

- follows v2.3.0 without inventing unreleased v4–v6 tags;
- matches the implementation's existing version identifiers;
- correctly signals a major architecture and data-contract change; and
- allows later releases to evolve from the code that was actually shipped rather than from an obsolete numeric roadmap.

The canonical document name is therefore:

```text
SixthSense_v3.0.0.md
```

## Release summary

SixthSense v3.0.0 is the first closed-loop prototype in the project history. It expands the observation-first perception pipeline to six VL53L5CX sensors, divides their 96 ranging zones into 18 directional sectors, identifies sustained approaching motion, converts qualifying sectors into a four-bit motor mask, and applies the result through four directional vibration motors.

The release preserves the earlier confidence, temporal velocity, motion-state, and persistence work while changing their scale and integrating them with user feedback.

```text
6 × VL53L5CX
       ↓
96 confidence-aware zones
       ↓
18 directional sector observations
       ↓
smoothed relative velocity
       ↓
velocity state + motion persistence
       ↓
Attention Engine
       ↓
four-bit motor mask
       ↓
Feedback Engine + MCU watchdog
       ↓
M1 / M2 / M3 / M4 haptic feedback
```

## Major changes from v2.3.0

| Area | v2.3.0 | v3.0.0 |
|---|---|---|
| ToF sensors | 1 | 6 |
| Resolution | 8×8 | 4×4 per sensor |
| Raw zones | 64 | 96 total |
| Logical sectors | 3 | 18 total |
| Sensor directions | Front prototype | Front-right, front, front-left, rear-left, rear, rear-right |
| Multiplexer | Not required | 8-channel I2C multiplexer |
| Persistence maximum | 100 | 200 |
| Attention selection | Planned | Implemented |
| Haptic feedback | Planned | Four directional motors |
| MCU command | Sensor RPC only | Sensor RPC plus four-bit motor mask |
| Dashboard | Single-sensor observation | Six-sensor, attention, feedback, and motor-state dashboard |

## Fixed runtime configuration

| Parameter | Value |
|---|---:|
| Sensors | 6 × VL53L5CX |
| Sensor address | `0x29` |
| I2C multiplexer address | `0x70` |
| Resolution | 4×4 |
| Zones per sensor | 16 |
| Total zones | 96 |
| Requested ranging frequency | 30 Hz |
| Integration time | 20 ms |
| I2C clock | 400 kHz |
| SparkFun transfer packet | 128 bytes |
| Measured retrieved rate | approximately 14 Hz per sensor |
| Observation history | 20 per sensor |
| Velocity smoothing window | 5 valid values |
| Stationary threshold | 50 mm/s |
| Maximum trusted distance | 3000 mm |
| Motion-persistence range | 0–200 |
| Attention activation threshold | 10 |
| Feedback refresh | 500 ms |
| MCU command timeout | 1000 ms |

The 14 Hz value is a measured acquisition-side benchmark recorded in the source. It is not a guaranteed rate.

## Physical sensor layout

| Sensor | Index | Mux channel | Position |
|---|---:|---:|---|
| T1 | 0 | CH0 | Front-right |
| T2 | 1 | CH1 | Front |
| T3 | 2 | CH2 | Front-left |
| T4 | 3 | CH5 | Rear-left |
| T5 | 4 | CH6 | Rear |
| T6 | 5 | CH7 | Rear-right |

Each sensor retains its own observation history, velocity history, and three-state persistence counters. Temporal state is not shared between sensors.

## Six-sensor publication contract

The MCU acquires all six sensors continuously through the I2C multiplexer. A publishable observation is created only after every sensor has produced at least one fresh frame since the preceding publication.

The published frame is copied into dedicated buffers and remains immutable until Python calls `consume_observation()`. Zone arrays are flattened signal-by-signal for RouterBridge transfer and reconstructed into six oriented 4×4 images by Python.

This is a synchronization barrier for a complete six-sensor observation, not a claim that every sensor performed its physical measurement at the exact same instant.

## Sector model

After horizontal orientation correction, the 4×4 image is divided by column:

```text
S0 = column 0
S1 = columns 1 and 2
S2 = column 3
```

The nearest valid zone in each sector becomes the sector observation. A zone is rejected when its distance is invalid or outside the configured range, when no target is reported, when its target status is rejected, or when the resulting confidence is zero.

The selected observation records distance, confidence, raw source-zone ID, sensor quality fields, velocity, velocity validity, velocity state, and persistence counters.

## Confidence Engine

The confidence score remains an interpretable engineering quality heuristic. It combines:

| Input | Weight |
|---|---:|
| Target status | 30% |
| Signal per SPAD | 30% |
| Range sigma | 20% |
| Ambient per SPAD | 5% |
| Reflectance | 5% |
| Detected targets | 5% |
| Enabled SPADs | 5% |

Target status 5 receives full status credit; statuses 6 and 9 receive partial credit; other statuses are rejected by the current model. The confidence value is not a statistical probability and requires future calibration using representative 4×4 data.

## Temporal observation and velocity

Velocity is estimated from consecutive selected sector distances:

```text
velocity_mmps = (current_distance_mm - previous_distance_mm) / elapsed_seconds
```

A minimum time delta of 20 ms protects the calculation from very small intervals. Only valid velocities enter the five-sample moving average.

Classification uses the smoothed value:

```text
velocity < −50 mm/s  → Approaching
−50 to +50 mm/s      → Stationary
velocity > +50 mm/s  → Receding
invalid velocity     → Unknown
```

Negative velocity means that the measured range is decreasing relative to the sensor. This may result from target motion, user motion, sensor motion, or a combination of them.

## Motion Persistence Engine

Each of the 18 sectors maintains independent bounded counters for `Approaching`, `Stationary`, and `Receding`.

For a recognized state, its counter increments by one and the other two counters decrement by one. For `Unknown`, all counters decrement by one. Values are clamped to 0–200.

The public `motion_persistence` field contains the counter for the current recognized state. It is an observation-based temporal evidence score. It is not:

- a percentage;
- a probability;
- measurement confidence;
- Time to Collision;
- an object ID; or
- evidence that the same object was observed in every frame.

At approximately 14 processed observations per second, a threshold of 10 represents roughly 0.71 seconds of uninterrupted supporting observations. The actual duration varies with the effective processing rate and with counter history.

## Attention Engine

The v3.0.0 Attention Engine is deterministic and intentionally simple. A sector becomes an active attention source only when:

```python
sector.velocity_state == "Approaching"
and sector.motion_persistence >= 10
```

The current Attention Engine does not add confidence as a separate final condition. Confidence has already filtered the raw measurement and controls whether valid sector distances and velocities can be formed. The two signals therefore serve different stages:

```text
confidence          → Can this measurement be trusted enough to observe?
velocity/persistence → Has approaching motion remained consistent long enough to alert?
```

Every qualifying source contributes its predefined motor mask. Masks are combined using bitwise OR, preserving simultaneous directional cues.

## Direction-to-motor mapping

| Sensor | Sector | Approximate direction | Motors | Mask |
|---|:---:|---|---|---:|
| T1 Front-right | S0 | Right | M4 | `0x08` |
| T1 Front-right | S1 | Front-right | M1 + M4 | `0x09` |
| T1 Front-right | S2 | Front-right | M1 + M4 | `0x09` |
| T2 Front | S0 | Front-right | M1 + M4 | `0x09` |
| T2 Front | S1 | Front | M1 | `0x01` |
| T2 Front | S2 | Front-left | M1 + M2 | `0x03` |
| T3 Front-left | S0 | Front-left | M1 + M2 | `0x03` |
| T3 Front-left | S1 | Front-left | M1 + M2 | `0x03` |
| T3 Front-left | S2 | Left | M2 | `0x02` |
| T4 Rear-left | S0 | Left | M2 | `0x02` |
| T4 Rear-left | S1 | Rear-left | M2 + M3 | `0x06` |
| T4 Rear-left | S2 | Rear-left | M2 + M3 | `0x06` |
| T5 Rear | S0 | Rear-left | M2 + M3 | `0x06` |
| T5 Rear | S1 | Rear | M3 | `0x04` |
| T5 Rear | S2 | Rear-right | M3 + M4 | `0x0C` |
| T6 Rear-right | S0 | Rear-right | M3 + M4 | `0x0C` |
| T6 Rear-right | S1 | Rear-right | M3 + M4 | `0x0C` |
| T6 Rear-right | S2 | Right | M4 | `0x08` |

## MCU-friendly motor mask

| Bit | Motor | Direction | Hex |
|---:|---|---|---:|
| 0 | M1 | Front | `0x01` |
| 1 | M2 | Left | `0x02` |
| 2 | M3 | Rear | `0x04` |
| 3 | M4 | Right | `0x08` |

Examples:

```text
No motors        = 0000 = 0x00
M1               = 0001 = 0x01
M1 + M4          = 1001 = 0x09
M2 + M3          = 0110 = 0x06
M3 + M4          = 1100 = 0x0C
All motors       = 1111 = 0x0F
```

The sketch maps M1–M4 to PWM pins D5, D6, D9, and D10. These pins must drive motor-driver inputs, never motors directly.

## Feedback Engine

The Python Feedback Engine:

1. masks the requested value to four valid bits;
2. sends it through RouterBridge when the mask changes;
3. refreshes an unchanged mask every 500 ms;
4. records the mask returned by the MCU;
5. reports requested and applied masks to the dashboard; and
6. retries at the keep-alive interval after a Bridge error instead of flooding the connection.

The MCU applies PWM duty 255 to enabled motor outputs. If an active motor mask is not refreshed within 1000 ms, the watchdog applies `0x00` and turns all motors off.

## Dashboard and data contract

The browser payload now includes:

```text
configuration
sensors[6]
attention
feedback
```

Each sensor carries its 4×4 distance and confidence images plus a structured observation containing S0, S1, and S2. The attention object exposes the activation rule, combined motor mask, motor names, and every active sensor-sector source. The feedback object exposes command status and both requested and MCU-applied masks.

The dashboard adds:

- six sensor overview cards;
- T1–T6 detailed selection;
- selected-sensor distance and confidence heatmaps;
- complete temporal sector observations;
- a top-view M1–M4 motor display;
- requested versus applied masks;
- active attention sources; and
- complete six-sensor JSON output.

## Validation performed

The current prototype configuration records an approximate retrieved rate of 14 Hz. A motor activation threshold of 10 has been exercised successfully and remains a tuning parameter rather than a universal human-factors result.

Static validation of the submitted source confirms:

- Python syntax compiles successfully;
- JavaScript syntax passes `node --check`;
- the HTML contains the six-sensor and four-motor UI elements;
- the 18-entry motor mapping is present in Python;
- motion-persistence saturation is configured at 200;
- feedback refresh and MCU watchdog constants are present; and
- the attached JavaScript, HTML, sketch, and CSS match the `develop` branch after line-ending normalization.

Arduino compilation and complete electrical validation require the Arduino UNO Q toolchain, sensor library, driver hardware, and physical prototype and are outside static documentation validation.

## Known limitations

- The Confidence Engine is heuristic and not calibrated against a ground-truth dataset.
- No object identification, object tracking, or cross-sensor spatial fusion is performed.
- Motion persistence is sector-state memory, not same-object persistence.
- Persistence is observation-count based rather than time-normalized.
- Head, rig, or user motion can appear as relative target motion.
- The attention rule does not rank multiple hazards by distance, urgency, or Time to Collision.
- Motor intensity is currently on/off at a fixed PWM duty rather than distance- or urgency-modulated.
- No trained ML model is used in the decision path.
- The device is a research prototype, not a certified assistive or safety system.

## Release statement

SixthSense v3.0.0 demonstrates an end-to-end Physical AI loop:

```text
Sense → qualify → observe → interpret motion → accumulate evidence
      → select attention → encode direction → deliver haptic feedback
```

Its principal contribution is not a trained AI model but a modular, transparent, testable perception-to-action architecture that turns multi-directional spatial observations into intuitive directional cues.
