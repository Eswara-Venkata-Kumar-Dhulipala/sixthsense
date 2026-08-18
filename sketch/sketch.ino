// ============================================================================
// SixthSense
// Version 3.0.0
// Arduino UNO Q
// 6 x VL53L5CX Multi-ToF Observation Bridge
//
// Fixed acquisition configuration:
//   Sensors                : 6 x VL53L5CX
//   Resolution             : 4 x 4
//   Zones / sensor         : 16
//   Total zones            : 96
//   Requested ranging rate : 30 Hz
//   Integration time       : 20 ms
//   I2C                    : 400 kHz
//   SparkFun packet size   : 128 bytes
//
// Mux mapping:
//   T1 -> CH0 -> Front-right
//   T2 -> CH1 -> Front
//   T3 -> CH2 -> Front-left
//   T4 -> CH5 -> Rear-left
//   T5 -> CH6 -> Rear
//   T6 -> CH7 -> Rear-right
//
// Bridge architecture:
//   - Sensors acquire continuously on the MCU.
//   - A six-sensor observation is published only when all six sensors have
//     produced at least one fresh frame since the previous publication.
//   - Published data remains immutable until Python calls consume_observation().
//   - All 96 zones are flattened per signal for efficient Bridge transfer.
// ============================================================================

#include <Wire.h>
#include <array>
#include <algorithm>

#include <zephyr/sys/atomic.h>

#include <Arduino_RouterBridge.h>
#include <SparkFun_VL53L5CX_Library.h>

// ============================================================================
// Constants
// ============================================================================

constexpr uint8_t NUM_SENSORS = 6;

constexpr uint8_t IMAGE_ROWS = 4;
constexpr uint8_t IMAGE_COLS = 4;
constexpr uint8_t ZONES_PER_SENSOR = 16;
constexpr uint16_t TOTAL_ZONES = NUM_SENSORS * ZONES_PER_SENSOR;

constexpr uint8_t TARGET_INDEX = 0;

constexpr uint32_t SERIAL_BAUD_RATE = 115200;

constexpr uint32_t I2C_SPEED = 400000;
constexpr uint8_t SENSOR_ADDRESS = 0x29;
constexpr uint8_t MUX_ADDRESS = 0x70;
constexpr uint8_t TOF_PACKET_SIZE = 128;

constexpr uint8_t RANGING_FREQUENCY_HZ = 30;
constexpr uint32_t INTEGRATION_TIME_MS = 20;

constexpr uint8_t SENSOR_INIT_RETRIES = 5;
constexpr uint32_t SENSOR_RETRY_DELAY_MS = 250;

constexpr std::array<uint8_t, NUM_SENSORS> SENSOR_MUX_CHANNELS =
{
    0,  // T1 -> Front-right
    1,  // T2 -> Front
    2,  // T3 -> Front-left
    5,  // T4 -> Rear-left
    6,  // T5 -> Rear
    7   // T6 -> Rear-right
};

// ============================================================================
// Sensor Objects
// ============================================================================

SparkFun_VL53L5CX tof1;
SparkFun_VL53L5CX tof2;
SparkFun_VL53L5CX tof3;
SparkFun_VL53L5CX tof4;
SparkFun_VL53L5CX tof5;
SparkFun_VL53L5CX tof6;

std::array<SparkFun_VL53L5CX *, NUM_SENSORS> tofSensors =
{
    &tof1,
    &tof2,
    &tof3,
    &tof4,
    &tof5,
    &tof6
};

std::array<VL53L5CX_ResultsData, NUM_SENSORS> measurementData;

// ============================================================================
// Sensor Frame
// ============================================================================

struct SensorFrame
{
    // Per-target outputs
    std::array<int16_t, ZONES_PER_SENSOR> distance {};
    std::array<uint32_t, ZONES_PER_SENSOR> signal {};
    std::array<uint16_t, ZONES_PER_SENSOR> sigma {};
    std::array<uint8_t, ZONES_PER_SENSOR> status {};
    std::array<uint8_t, ZONES_PER_SENSOR> reflectance {};

    // Per-zone outputs
    std::array<uint32_t, ZONES_PER_SENSOR> ambient {};
    std::array<uint8_t, ZONES_PER_SENSOR> targets {};
    std::array<uint32_t, ZONES_PER_SENSOR> spads {};

    uint32_t frameCounter = 0;
    uint32_t timestamp = 0;

    // True once this sensor has produced a new frame since the last
    // six-sensor publication.
    bool fresh = false;
};

std::array<SensorFrame, NUM_SENSORS> liveFrames;
std::array<SensorFrame, NUM_SENSORS> publishedFrames;

// ============================================================================
// Initialization State
// ============================================================================
//
// Sensor init codes:
//
//   0   -> initialization not completed
//   1   -> initialized successfully
//
//  -1   -> mux channel selection failed
//  -2   -> sensor probe / begin failed
//  -3   -> 128-byte packet-size configuration failed
//  -4   -> 4x4 resolution configuration failed
//  -5   -> 30 Hz ranging-frequency configuration failed
//  -6   -> 20 ms integration-time configuration failed
//  -7   -> startRanging() failed
// -10   -> I2C mux initialization failed
//
// ============================================================================

std::array<int32_t, NUM_SENSORS> sensorInitCodes {};
std::array<uint8_t, NUM_SENSORS> sensorReadyFlags {};

bool muxReady = false;
bool sensorsRunning = false;

// ============================================================================
// Publication State
// ============================================================================

atomic_t observationReady = ATOMIC_INIT(0);
atomic_t observationCounter = ATOMIC_INIT(0);
atomic_t muxSelectErrors = ATOMIC_INIT(0);

atomic_t sensorReadErrors[NUM_SENSORS] =
{
    ATOMIC_INIT(0),
    ATOMIC_INIT(0),
    ATOMIC_INIT(0),
    ATOMIC_INIT(0),
    ATOMIC_INIT(0),
    ATOMIC_INIT(0)
};

uint32_t publishedObservationTimestamp = 0;

// ============================================================================
// Mux Helpers
// ============================================================================

bool writeMuxControl(
    uint8_t controlByte
)
{
    Wire1.beginTransmission(
        MUX_ADDRESS
    );

    Wire1.write(
        controlByte
    );

    return Wire1.endTransmission() == 0;
}

bool selectMuxChannel(
    uint8_t channel
)
{
    if (channel > 7)
    {
        return false;
    }

    return writeMuxControl(
        static_cast<uint8_t>(
            1U << channel
        )
    );
}

bool disableAllMuxChannels()
{
    return writeMuxControl(
        0x00
    );
}

bool initMux()
{
    Wire1.beginTransmission(
        MUX_ADDRESS
    );

    if (
        Wire1.endTransmission()
        !=
        0
    )
    {
        return false;
    }

    return disableAllMuxChannels();
}

bool probeSensorAddress()
{
    Wire1.beginTransmission(
        SENSOR_ADDRESS
    );

    return Wire1.endTransmission() == 0;
}

// ============================================================================
// Sensor Initialization
// ============================================================================

bool configureSensor(
    uint8_t sensorIndex
)
{
    SparkFun_VL53L5CX &sensor =
        *tofSensors[
            sensorIndex
        ];

    const uint8_t muxChannel =
        SENSOR_MUX_CHANNELS[
            sensorIndex
        ];

    sensorInitCodes[
        sensorIndex
    ] = 0;

    sensorReadyFlags[
        sensorIndex
    ] = 0;

    if (!selectMuxChannel(muxChannel))
    {
        sensorInitCodes[
            sensorIndex
        ] = -1;

        return false;
    }

    delay(
        10
    );

    bool initialized = false;

    for (
        uint8_t attempt = 0;
        attempt < SENSOR_INIT_RETRIES;
        attempt++
    )
    {
        if (
            probeSensorAddress()
            &&
            sensor.begin(
                SENSOR_ADDRESS,
                Wire1
            )
        )
        {
            initialized = true;
            break;
        }

        delay(
            SENSOR_RETRY_DELAY_MS
        );
    }

    if (!initialized)
    {
        sensorInitCodes[
            sensorIndex
        ] = -2;

        return false;
    }

    // SparkFun VL53L5CX library default is 32 bytes.
    // 128 bytes was validated on UNO Q and reduces transfer overhead.
    sensor.setWireMaxPacketSize(
        TOF_PACKET_SIZE
    );

    if (
        sensor.getWireMaxPacketSize()
        !=
        TOF_PACKET_SIZE
    )
    {
        sensorInitCodes[
            sensorIndex
        ] = -3;

        return false;
    }

    if (!sensor.setResolution(
        IMAGE_ROWS * IMAGE_COLS
    ))
    {
        sensorInitCodes[
            sensorIndex
        ] = -4;

        return false;
    }

    if (!sensor.setRangingFrequency(
        RANGING_FREQUENCY_HZ
    ))
    {
        sensorInitCodes[
            sensorIndex
        ] = -5;

        return false;
    }

    if (!sensor.setIntegrationTime(
        INTEGRATION_TIME_MS
    ))
    {
        sensorInitCodes[
            sensorIndex
        ] = -6;

        return false;
    }

    sensor.setTargetOrder(
        SF_VL53L5CX_TARGET_ORDER::CLOSEST
    );

    if (!sensor.startRanging())
    {
        sensorInitCodes[
            sensorIndex
        ] = -7;

        return false;
    }

    sensorInitCodes[
        sensorIndex
    ] = 1;

    sensorReadyFlags[
        sensorIndex
    ] = 1;

    return true;
}

bool initSensors()
{
    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        if (!configureSensor(
            sensorIndex
        ))
        {
            return false;
        }

        delay(
            20
        );
    }

    return disableAllMuxChannels();
}

// ============================================================================
// Acquire One Sensor Frame
// ============================================================================

bool updateSensor(
    uint8_t sensorIndex
)
{
    SparkFun_VL53L5CX &sensor =
        *tofSensors[
            sensorIndex
        ];

    SensorFrame &frame =
        liveFrames[
            sensorIndex
        ];

    if (!selectMuxChannel(
        SENSOR_MUX_CHANNELS[
            sensorIndex
        ]
    ))
    {
        atomic_inc(
            &muxSelectErrors
        );

        return false;
    }

    // SparkFun isDataReady() returns false both when no frame is ready and
    // when the readiness transaction cannot establish readiness. Therefore,
    // "false" is not counted as a communication error here.
    if (!sensor.isDataReady())
    {
        return false;
    }

    if (!sensor.getRangingData(
        &measurementData[
            sensorIndex
        ]
    ))
    {
        atomic_inc(
            &sensorReadErrors[
                sensorIndex
            ]
        );

        return false;
    }

    for (
        uint8_t zone = 0;
        zone < ZONES_PER_SENSOR;
        zone++
    )
    {
        const uint16_t targetIndex =

            zone
            *
            VL53L5CX_NB_TARGET_PER_ZONE

            +

            TARGET_INDEX;

        frame.distance[
            zone
        ] =
            measurementData[
                sensorIndex
            ].distance_mm[
                targetIndex
            ];

        frame.signal[
            zone
        ] =
            measurementData[
                sensorIndex
            ].signal_per_spad[
                targetIndex
            ];

        frame.sigma[
            zone
        ] =
            measurementData[
                sensorIndex
            ].range_sigma_mm[
                targetIndex
            ];

        frame.status[
            zone
        ] =
            measurementData[
                sensorIndex
            ].target_status[
                targetIndex
            ];

        frame.reflectance[
            zone
        ] =
            measurementData[
                sensorIndex
            ].reflectance[
                targetIndex
            ];

        frame.ambient[
            zone
        ] =
            measurementData[
                sensorIndex
            ].ambient_per_spad[
                zone
            ];

        frame.targets[
            zone
        ] =
            measurementData[
                sensorIndex
            ].nb_target_detected[
                zone
            ];

        frame.spads[
            zone
        ] =
            measurementData[
                sensorIndex
            ].nb_spads_enabled[
                zone
            ];
    }

    frame.frameCounter++;

    // Timestamp is the successful MCU read-completion time.
    // It is not a hardware optical-exposure timestamp.
    frame.timestamp =
        millis();

    frame.fresh =
        true;

    return true;
}

// ============================================================================
// Publish Immutable Six-Sensor Observation
// ============================================================================

bool allSensorsFresh()
{
    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        if (!liveFrames[
            sensorIndex
        ].fresh)
        {
            return false;
        }
    }

    return true;
}

void tryPublishObservation()
{
    // One-slot publication buffer.
    // Do not overwrite data while Python is reading it.
    if (
        atomic_get(
            &observationReady
        )
        !=
        0
    )
    {
        return;
    }

    if (!allSensorsFresh())
    {
        return;
    }

    uint32_t newestTimestamp = 0;

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        publishedFrames[
            sensorIndex
        ] =
            liveFrames[
                sensorIndex
            ];

        publishedFrames[
            sensorIndex
        ].fresh =
            false;

        newestTimestamp =
            std::max(
                newestTimestamp,
                publishedFrames[
                    sensorIndex
                ].timestamp
            );

        liveFrames[
            sensorIndex
        ].fresh =
            false;
    }

    publishedObservationTimestamp =
        newestTimestamp;

    const atomic_val_t nextCounter =
        atomic_get(
            &observationCounter
        )
        +
        1;

    atomic_set(
        &observationCounter,
        nextCounter
    );

    // Publish only after every immutable field above has been written.
    atomic_set(
        &observationReady,
        1
    );
}

// ============================================================================
// Flatten Published Six-Sensor Arrays
// ============================================================================

std::array<int16_t, TOTAL_ZONES> get_distance()
{
    std::array<int16_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].distance[
                    zone
                ];
        }
    }

    return out;
}

std::array<uint32_t, TOTAL_ZONES> get_signal()
{
    std::array<uint32_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].signal[
                    zone
                ];
        }
    }

    return out;
}

std::array<uint16_t, TOTAL_ZONES> get_sigma()
{
    std::array<uint16_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].sigma[
                    zone
                ];
        }
    }

    return out;
}

std::array<uint8_t, TOTAL_ZONES> get_status()
{
    std::array<uint8_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].status[
                    zone
                ];
        }
    }

    return out;
}

std::array<uint8_t, TOTAL_ZONES> get_reflectance()
{
    std::array<uint8_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].reflectance[
                    zone
                ];
        }
    }

    return out;
}

std::array<uint32_t, TOTAL_ZONES> get_ambient()
{
    std::array<uint32_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].ambient[
                    zone
                ];
        }
    }

    return out;
}

std::array<uint8_t, TOTAL_ZONES> get_targets()
{
    std::array<uint8_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].targets[
                    zone
                ];
        }
    }

    return out;
}

std::array<uint32_t, TOTAL_ZONES> get_spads()
{
    std::array<uint32_t, TOTAL_ZONES> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        for (
            uint8_t zone = 0;
            zone < ZONES_PER_SENSOR;
            zone++
        )
        {
            out[
                sensorIndex
                *
                ZONES_PER_SENSOR
                +
                zone
            ] =
                publishedFrames[
                    sensorIndex
                ].spads[
                    zone
                ];
        }
    }

    return out;
}

// ============================================================================
// Published Metadata RPCs
// ============================================================================

uint32_t get_bridge_heartbeat()
{
    return millis();
}

bool system_ready()
{
    return sensorsRunning;
}

uint32_t get_pending_observation()
{
    if (
        atomic_get(
            &observationReady
        )
        ==
        0
    )
    {
        return 0;
    }

    return static_cast<uint32_t>(
        atomic_get(
            &observationCounter
        )
    );
}

uint32_t get_observation_timestamp()
{
    return publishedObservationTimestamp;
}

std::array<uint32_t, NUM_SENSORS> get_sensor_frame_counters()
{
    std::array<uint32_t, NUM_SENSORS> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        out[
            sensorIndex
        ] =
            publishedFrames[
                sensorIndex
            ].frameCounter;
    }

    return out;
}

std::array<uint32_t, NUM_SENSORS> get_sensor_timestamps()
{
    std::array<uint32_t, NUM_SENSORS> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        out[
            sensorIndex
        ] =
            publishedFrames[
                sensorIndex
            ].timestamp;
    }

    return out;
}

std::array<int32_t, NUM_SENSORS> get_sensor_init_codes()
{
    return sensorInitCodes;
}

std::array<uint8_t, NUM_SENSORS> get_sensor_ready_flags()
{
    return sensorReadyFlags;
}

std::array<uint32_t, NUM_SENSORS> get_sensor_read_errors()
{
    std::array<uint32_t, NUM_SENSORS> out {};

    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        out[
            sensorIndex
        ] =
            static_cast<uint32_t>(
                atomic_get(
                    &sensorReadErrors[
                        sensorIndex
                    ]
                )
            );
    }

    return out;
}

uint32_t get_mux_select_errors()
{
    return static_cast<uint32_t>(
        atomic_get(
            &muxSelectErrors
        )
    );
}

bool consume_observation(
    uint32_t expectedObservation
)
{
    if (
        atomic_get(
            &observationReady
        )
        ==
        0
    )
    {
        return false;
    }

    if (
        static_cast<uint32_t>(
            atomic_get(
                &observationCounter
            )
        )
        !=
        expectedObservation
    )
    {
        return false;
    }

    atomic_set(
        &observationReady,
        0
    );

    return true;
}

// ============================================================================
// Register RouterBridge RPCs
// ============================================================================

void registerBridgeFunctions()
{
    Bridge.provide(
        "get_bridge_heartbeat",
        get_bridge_heartbeat
    );

    Bridge.provide(
        "system_ready",
        system_ready
    );

    Bridge.provide(
        "get_pending_observation",
        get_pending_observation
    );

    Bridge.provide(
        "get_observation_timestamp",
        get_observation_timestamp
    );

    Bridge.provide(
        "get_sensor_frame_counters",
        get_sensor_frame_counters
    );

    Bridge.provide(
        "get_sensor_timestamps",
        get_sensor_timestamps
    );

    Bridge.provide(
        "get_sensor_init_codes",
        get_sensor_init_codes
    );

    Bridge.provide(
        "get_sensor_ready_flags",
        get_sensor_ready_flags
    );

    Bridge.provide(
        "get_sensor_read_errors",
        get_sensor_read_errors
    );

    Bridge.provide(
        "get_mux_select_errors",
        get_mux_select_errors
    );

    Bridge.provide(
        "get_distance",
        get_distance
    );

    Bridge.provide(
        "get_signal",
        get_signal
    );

    Bridge.provide(
        "get_sigma",
        get_sigma
    );

    Bridge.provide(
        "get_status",
        get_status
    );

    Bridge.provide(
        "get_reflectance",
        get_reflectance
    );

    Bridge.provide(
        "get_ambient",
        get_ambient
    );

    Bridge.provide(
        "get_targets",
        get_targets
    );

    Bridge.provide(
        "get_spads",
        get_spads
    );

    Bridge.provide(
        "consume_observation",
        consume_observation
    );
}

// ============================================================================
// Setup
// ============================================================================

void setup()
{
    Serial.begin(
        SERIAL_BAUD_RATE
    );

    delay(
        2000
    );

    Serial.println();
    Serial.println("========================================");
    Serial.println("SixthSense v3.0.0");
    Serial.println("6 x VL53L5CX Multi-ToF Bridge");
    Serial.println("========================================");

    Wire1.begin();

    Wire1.setClock(
        I2C_SPEED
    );

    muxReady =
        initMux();

    if (!muxReady)
    {
        sensorInitCodes.fill(
            -10
        );

        sensorReadyFlags.fill(
            0
        );

        sensorsRunning =
            false;
    }
    else
    {
        sensorsRunning =
            initSensors();
    }

    Bridge.begin();

    registerBridgeFunctions();

    Serial.println();
    Serial.println("Configuration:");
    Serial.println("  Sensors       : 6");
    Serial.println("  Resolution    : 4 x 4");
    Serial.println("  Zones         : 96 total");
    Serial.println("  Ranging       : 30 Hz requested");
    Serial.println("  Integration   : 20 ms");
    Serial.println("  I2C           : 400 kHz");
    Serial.println("  Packet size   : 128 bytes");

    if (sensorsRunning)
    {
        Serial.println("  Status        : ALL SENSORS READY");
    }
    else
    {
        Serial.println("  Status        : SENSOR INITIALIZATION FAILED");

        for (
            uint8_t sensorIndex = 0;
            sensorIndex < NUM_SENSORS;
            sensorIndex++
        )
        {
            Serial.print("  T");
            Serial.print(sensorIndex + 1);
            Serial.print(" init code : ");
            Serial.println(
                sensorInitCodes[
                    sensorIndex
                ]
            );
        }
    }

    Serial.println("========================================");
    Serial.println();
}

// ============================================================================
// Main Loop
// ============================================================================

void loop()
{
    if (!sensorsRunning)
    {
        delay(
            100
        );

        return;
    }

    // Sequentially poll all six sensors.
    //
    // The timestamp stored for each frame is the MCU read-completion time.
    // It must not be interpreted as the exact optical acquisition time.
    for (
        uint8_t sensorIndex = 0;
        sensorIndex < NUM_SENSORS;
        sensorIndex++
    )
    {
        updateSensor(
            sensorIndex
        );
    }

    tryPublishObservation();

    delay(
        2
    );
}
