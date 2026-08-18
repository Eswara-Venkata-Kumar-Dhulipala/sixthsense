// ============================================================================
// SixthSense
// Arduino UNO Q
// VL53L5CX 8x8 ToF Sensor
//
// Production Bridge + Snapshot + Initialization Diagnostics
// ============================================================================

#include <Wire.h>
#include <array>

#include <Arduino_RouterBridge.h>
#include <SparkFun_VL53L5CX_Library.h>

// ============================================================================
// Constants
// ============================================================================

constexpr uint8_t IMAGE_SIZE = 64;
constexpr uint8_t TARGET_INDEX = 0;

constexpr uint32_t SERIAL_BAUD_RATE = 115200;
constexpr uint32_t I2C_SPEED = 400000;
constexpr uint8_t SENSOR_ADDRESS = 0x29;

constexpr uint8_t SENSOR_INIT_RETRIES = 10;
constexpr uint32_t SENSOR_RETRY_DELAY_MS = 500;

// ============================================================================
// Sensor
// ============================================================================

SparkFun_VL53L5CX tof;
VL53L5CX_ResultsData measurementData;

// ============================================================================
// Live Sensor Buffers
// ============================================================================

// Per-target outputs

std::array<int16_t, IMAGE_SIZE> liveDistance;
std::array<uint32_t, IMAGE_SIZE> liveSignal;
std::array<uint16_t, IMAGE_SIZE> liveSigma;
std::array<uint8_t, IMAGE_SIZE> liveStatus;
std::array<uint8_t, IMAGE_SIZE> liveReflectance;

// Per-zone outputs

std::array<uint32_t, IMAGE_SIZE> liveAmbient;
std::array<uint8_t, IMAGE_SIZE> liveTargets;
std::array<uint32_t, IMAGE_SIZE> liveSpads;

// ============================================================================
// Snapshot Buffers
// ============================================================================

// Per-target outputs

std::array<int16_t, IMAGE_SIZE> snapshotDistance;
std::array<uint32_t, IMAGE_SIZE> snapshotSignal;
std::array<uint16_t, IMAGE_SIZE> snapshotSigma;
std::array<uint8_t, IMAGE_SIZE> snapshotStatus;
std::array<uint8_t, IMAGE_SIZE> snapshotReflectance;

// Per-zone outputs

std::array<uint32_t, IMAGE_SIZE> snapshotAmbient;
std::array<uint8_t, IMAGE_SIZE> snapshotTargets;
std::array<uint32_t, IMAGE_SIZE> snapshotSpads;

// ============================================================================
// Metadata
// ============================================================================

uint32_t liveFrameCounter = 0;
uint32_t liveTimestamp = 0;

uint32_t snapshotFrameCounter = 0;
uint32_t snapshotTimestamp = 0;

bool sensorRunning = false;

// ============================================================================
// Sensor Initialization Diagnostic Code
// ============================================================================
//
//  0  -> initialization not completed
//  1  -> sensor initialized successfully
//
// -1  -> tof.begin() / sensor detection failed
// -2  -> setResolution() failed
// -3  -> setRangingFrequency() failed
// -4  -> setIntegrationTime() failed
// -5  -> startRanging() failed
//
// ============================================================================

int32_t sensorInitCode = 0;

// ============================================================================
// I2C Probe
// ============================================================================

bool probeSensorAddress()
{
    Wire1.beginTransmission(
        SENSOR_ADDRESS
    );

    const uint8_t result =
        Wire1.endTransmission();

    return result == 0;
}

// ============================================================================
// Diagnostic RPC Functions
// ============================================================================

bool sensor_ready()
{
    return sensorRunning;
}

int32_t get_sensor_init_code()
{
    return sensorInitCode;
}

uint32_t get_live_frame_counter()
{
    return liveFrameCounter;
}

uint32_t get_snapshot_frame_counter()
{
    return snapshotFrameCounter;
}

// ============================================================================
// Snapshot Data Getters
// ============================================================================

std::array<int16_t, IMAGE_SIZE> get_distance()
{
    return snapshotDistance;
}

std::array<uint32_t, IMAGE_SIZE> get_signal()
{
    return snapshotSignal;
}

std::array<uint16_t, IMAGE_SIZE> get_sigma()
{
    return snapshotSigma;
}

std::array<uint8_t, IMAGE_SIZE> get_status()
{
    return snapshotStatus;
}

std::array<uint8_t, IMAGE_SIZE> get_reflectance()
{
    return snapshotReflectance;
}

std::array<uint32_t, IMAGE_SIZE> get_ambient()
{
    return snapshotAmbient;
}

std::array<uint8_t, IMAGE_SIZE> get_targets()
{
    return snapshotTargets;
}

std::array<uint32_t, IMAGE_SIZE> get_spads()
{
    return snapshotSpads;
}

uint32_t get_timestamp()
{
    return snapshotTimestamp;
}

// ============================================================================
// Capture Snapshot
// ============================================================================

uint32_t capture_snapshot()
{
    // No valid sensor frame yet.

    if (liveFrameCounter == 0)
    {
        return 0;
    }

    // ------------------------------------------------------------------------
    // Copy complete live sensor state
    // ------------------------------------------------------------------------

    snapshotDistance = liveDistance;
    snapshotSignal = liveSignal;
    snapshotSigma = liveSigma;
    snapshotStatus = liveStatus;
    snapshotReflectance = liveReflectance;

    snapshotAmbient = liveAmbient;
    snapshotTargets = liveTargets;
    snapshotSpads = liveSpads;

    // ------------------------------------------------------------------------
    // Snapshot metadata
    // ------------------------------------------------------------------------

    snapshotFrameCounter = liveFrameCounter;
    snapshotTimestamp = liveTimestamp;

    return snapshotFrameCounter;
}

// ============================================================================
// Initialize VL53L5CX
// ============================================================================

bool initSensor()
{
    Serial.println();
    Serial.println("========================================");
    Serial.println("Initializing VL53L5CX");
    Serial.println("========================================");

    sensorInitCode = 0;

    // ------------------------------------------------------------------------
    // Start I2C
    // ------------------------------------------------------------------------

    Serial.println(
        "Starting Wire1..."
    );

    Wire1.begin();

    Wire1.setClock(
        I2C_SPEED
    );

    Serial.println(
        "I2C Ready"
    );

    // Give the sensor and Qwiic bus time to settle.

    delay(
        500
    );

    // ------------------------------------------------------------------------
    // Sensor detection / driver initialization
    // ------------------------------------------------------------------------

    bool sensorDetected = false;

    for (
        uint8_t attempt = 1;
        attempt <= SENSOR_INIT_RETRIES;
        attempt++
    )
    {
        Serial.print(
            "Sensor probe attempt "
        );

        Serial.print(
            attempt
        );

        Serial.print(
            "/"
        );

        Serial.println(
            SENSOR_INIT_RETRIES
        );

        // --------------------------------------------------------------------
        // Check whether anything responds at 0x29
        // --------------------------------------------------------------------

        if (!probeSensorAddress())
        {
            Serial.println(
                "No I2C response at address 0x29"
            );

            delay(
                SENSOR_RETRY_DELAY_MS
            );

            continue;
        }

        Serial.println(
            "I2C device detected at 0x29"
        );

        // --------------------------------------------------------------------
        // Initialize SparkFun driver
        // --------------------------------------------------------------------

        if (tof.begin(
            SENSOR_ADDRESS,
            Wire1
        ))
        {
            sensorDetected = true;

            Serial.println(
                "VL53L5CX driver initialized"
            );

            break;
        }

        Serial.println(
            "tof.begin() failed - retrying"
        );

        delay(
            SENSOR_RETRY_DELAY_MS
        );
    }

    // ------------------------------------------------------------------------
    // Sensor could not be initialized
    // ------------------------------------------------------------------------

    if (!sensorDetected)
    {
        sensorInitCode = -1;

        Serial.println(
            "ERROR: VL53L5CX could not be initialized"
        );

        return false;
    }

    // ------------------------------------------------------------------------
    // 8x8 resolution
    // ------------------------------------------------------------------------

    if (!tof.setResolution(
        8 * 8
    ))
    {
        sensorInitCode = -2;

        Serial.println(
            "ERROR: setResolution() failed"
        );

        return false;
    }

    Serial.println(
        "Resolution : 8 x 8"
    );

    // ------------------------------------------------------------------------
    // 15 Hz ranging
    // ------------------------------------------------------------------------

    if (!tof.setRangingFrequency(
        15
    ))
    {
        sensorInitCode = -3;

        Serial.println(
            "ERROR: setRangingFrequency() failed"
        );

        return false;
    }

    Serial.println(
        "Frequency : 15 Hz"
    );

    // ------------------------------------------------------------------------
    // Integration time
    // ------------------------------------------------------------------------

    if (!tof.setIntegrationTime(
        20
    ))
    {
        sensorInitCode = -4;

        Serial.println(
            "ERROR: setIntegrationTime() failed"
        );

        return false;
    }

    Serial.println(
        "Integration Time : 20 ms"
    );

    // ------------------------------------------------------------------------
    // Closest target
    // ------------------------------------------------------------------------

    tof.setTargetOrder(
        SF_VL53L5CX_TARGET_ORDER::CLOSEST
    );

    Serial.println(
        "Target Order : Closest"
    );

    // ------------------------------------------------------------------------
    // Start ranging
    // ------------------------------------------------------------------------

    if (!tof.startRanging())
    {
        sensorInitCode = -5;

        Serial.println(
            "ERROR: startRanging() failed"
        );

        return false;
    }

    Serial.println(
        "Ranging Started"
    );

    sensorInitCode = 1;

    return true;
}

// ============================================================================
// Read One Sensor Frame
// ============================================================================

bool updateFrame()
{
    // ------------------------------------------------------------------------
    // New measurement available?
    // ------------------------------------------------------------------------

    if (!tof.isDataReady())
    {
        return false;
    }

    // ------------------------------------------------------------------------
    // Retrieve VL53L5CX result structure
    // ------------------------------------------------------------------------

    if (!tof.getRangingData(
        &measurementData
    ))
    {
        return false;
    }

    // ------------------------------------------------------------------------
    // Copy every required sensor output
    // ------------------------------------------------------------------------

    for (
        uint8_t zone = 0;
        zone < IMAGE_SIZE;
        zone++
    )
    {
        const uint16_t targetIndex =

            zone
            * VL53L5CX_NB_TARGET_PER_ZONE

            +

            TARGET_INDEX;

        // --------------------------------------------------------------------
        // Per-target outputs
        // --------------------------------------------------------------------

        liveDistance[zone] =
            measurementData.distance_mm[
                targetIndex
            ];

        liveSignal[zone] =
            measurementData.signal_per_spad[
                targetIndex
            ];

        liveSigma[zone] =
            measurementData.range_sigma_mm[
                targetIndex
            ];

        liveStatus[zone] =
            measurementData.target_status[
                targetIndex
            ];

        liveReflectance[zone] =
            measurementData.reflectance[
                targetIndex
            ];

        // --------------------------------------------------------------------
        // Per-zone outputs
        // --------------------------------------------------------------------

        liveAmbient[zone] =
            measurementData.ambient_per_spad[
                zone
            ];

        liveTargets[zone] =
            measurementData.nb_target_detected[
                zone
            ];

        liveSpads[zone] =
            measurementData.nb_spads_enabled[
                zone
            ];
    }

    // ------------------------------------------------------------------------
    // Metadata
    // ------------------------------------------------------------------------

    liveFrameCounter++;

    liveTimestamp =
        millis();

    return true;
}

// ============================================================================
// Initialize Buffers
// ============================================================================

void initializeBuffers()
{
    // ------------------------------------------------------------------------
    // Live
    // ------------------------------------------------------------------------

    liveDistance.fill(
        0
    );

    liveSignal.fill(
        0
    );

    liveSigma.fill(
        0
    );

    liveStatus.fill(
        255
    );

    liveReflectance.fill(
        0
    );

    liveAmbient.fill(
        0
    );

    liveTargets.fill(
        0
    );

    liveSpads.fill(
        0
    );

    // ------------------------------------------------------------------------
    // Snapshot
    // ------------------------------------------------------------------------

    snapshotDistance.fill(
        0
    );

    snapshotSignal.fill(
        0
    );

    snapshotSigma.fill(
        0
    );

    snapshotStatus.fill(
        255
    );

    snapshotReflectance.fill(
        0
    );

    snapshotAmbient.fill(
        0
    );

    snapshotTargets.fill(
        0
    );

    snapshotSpads.fill(
        0
    );
}

// ============================================================================
// Register RouterBridge RPCs
// ============================================================================

void registerBridgeFunctions()
{
    // ------------------------------------------------------------------------
    // Diagnostics
    // ------------------------------------------------------------------------

    Bridge.provide(
        "sensor_ready",
        sensor_ready
    );

    Bridge.provide(
        "get_sensor_init_code",
        get_sensor_init_code
    );

    Bridge.provide(
        "get_live_frame_counter",
        get_live_frame_counter
    );

    Bridge.provide(
        "get_snapshot_frame_counter",
        get_snapshot_frame_counter
    );

    // ------------------------------------------------------------------------
    // Snapshot control
    // ------------------------------------------------------------------------

    Bridge.provide(
        "capture_snapshot",
        capture_snapshot
    );

    // ------------------------------------------------------------------------
    // Metadata
    // ------------------------------------------------------------------------

    Bridge.provide(
        "get_timestamp",
        get_timestamp
    );

    // ------------------------------------------------------------------------
    // Sensor outputs
    // ------------------------------------------------------------------------

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
    Serial.println("SixthSense");
    Serial.println("Arduino UNO Q");
    Serial.println("VL53L5CX Production Bridge");
    Serial.println("========================================");

    // ------------------------------------------------------------------------
    // Initialize buffers
    // ------------------------------------------------------------------------

    initializeBuffers();

    // ------------------------------------------------------------------------
    // Initialize sensor
    // ------------------------------------------------------------------------

    sensorRunning =
        initSensor();

    // ------------------------------------------------------------------------
    // Start RouterBridge
    // ------------------------------------------------------------------------

    Bridge.begin();

    registerBridgeFunctions();

    // ------------------------------------------------------------------------
    // Startup summary
    // ------------------------------------------------------------------------

    Serial.println();
    Serial.println("========================================");

    if (sensorRunning)
    {
        Serial.println(
            "Sensor Ready"
        );

        Serial.println(
            "Bridge Ready"
        );

        Serial.println(
            "Snapshot Interface Ready"
        );

        Serial.println(
            "SixthSense System Ready"
        );
    }
    else
    {
        Serial.println(
            "Sensor Initialization FAILED"
        );

        Serial.print(
            "Initialization Code : "
        );

        Serial.println(
            sensorInitCode
        );

        Serial.println(
            "Bridge diagnostic interface remains available"
        );
    }

    Serial.println(
        "========================================"
    );

    Serial.println();
}

// ============================================================================
// Main Loop
// ============================================================================

void loop()
{
    // ------------------------------------------------------------------------
    // Initialization failed
    //
    // Bridge remains alive so Python can retrieve sensorInitCode.
    // ------------------------------------------------------------------------

    if (!sensorRunning)
    {
        delay(
            100
        );

        return;
    }

    // ------------------------------------------------------------------------
    // Continuous ranging
    // ------------------------------------------------------------------------

    if (updateFrame())
    {
        // --------------------------------------------------------------------
        // Low-rate Serial diagnostic.
        //
        // Sensor runs at 15 Hz, therefore this executes
        // approximately once per second.
        // --------------------------------------------------------------------

        if (
            liveFrameCounter % 15
            ==
            0
        )
        {
            Serial.print(
                "Live Frame : "
            );

            Serial.print(
                liveFrameCounter
            );

            Serial.print(
                " | Timestamp : "
            );

            Serial.print(
                liveTimestamp
            );

            Serial.print(
                " ms | Center : "
            );

            Serial.print(
                liveDistance[
                    27
                ]
            );

            Serial.print(
                " mm | Status : "
            );

            Serial.print(
                liveStatus[
                    27
                ]
            );

            Serial.print(
                " | Targets : "
            );

            Serial.println(
                liveTargets[
                    27
                ]
            );
        }
    }

    delay(
        2
    );
}