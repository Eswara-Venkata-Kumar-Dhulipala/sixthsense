// ============================================================================
// SixthSense
// Arduino UNO Q
// VL53L5CX 8x8 ToF Sensor
//
// Production Version
// ============================================================================

#include <Wire.h>
#include <array>

#include <Arduino_RouterBridge.h>
#include <SparkFun_VL53L5CX_Library.h>

// ============================================================================
// Constants
// ============================================================================

constexpr uint8_t IMAGE_SIZE = 64;
constexpr uint32_t I2C_SPEED = 400000;
constexpr uint8_t SENSOR_ADDRESS = 0x29;

// ============================================================================
// Sensor
// ============================================================================

SparkFun_VL53L5CX tof;
VL53L5CX_ResultsData measurementData;

// ============================================================================
// Frame Buffer
// ============================================================================

std::array<uint16_t, IMAGE_SIZE> distanceFrame;

uint32_t frameCounter = 0;
uint32_t lastFrameTime = 0;

bool sensorRunning = false;

// ============================================================================
// Bridge RPC Functions
// ============================================================================

std::array<uint16_t, IMAGE_SIZE> get_frame()
{
    return distanceFrame;
}

uint32_t get_frame_counter()
{
    return frameCounter;
}

uint32_t get_timestamp()
{
    return lastFrameTime;
}

bool sensor_ready()
{
    return sensorRunning;
}

// ============================================================================
// Initialize Sensor
// ============================================================================

bool initSensor()
{
    Serial.println();
    Serial.println("======================================");
    Serial.println("Initializing VL53L5CX");
    Serial.println("======================================");

    // UNO Q Qwiic connector
    Wire1.begin();
    Wire1.setClock(I2C_SPEED);

    if (!tof.begin(SENSOR_ADDRESS, Wire1))
    {
        Serial.println("ERROR : Sensor not detected");
        return false;
    }

    Serial.println("Sensor detected");

    // -------------------------------------------------------
    // 8x8 Resolution
    // -------------------------------------------------------

    if (!tof.setResolution(8 * 8))
    {
        Serial.println("Failed to set 8x8 resolution");
        return false;
    }

    Serial.println("Resolution : 8 x 8");

    // -------------------------------------------------------
    // 15 FPS
    // -------------------------------------------------------

    if (!tof.setRangingFrequency(15))
    {
        Serial.println("Failed to set ranging frequency");
        return false;
    }

    Serial.println("Frequency : 15 Hz");

    // -------------------------------------------------------
    // Better stability
    // -------------------------------------------------------

    if (!tof.setIntegrationTime(20))
    {
        Serial.println("Failed to set integration time");
        return false;
    }

    Serial.println("Integration Time : 20 ms");

    // -------------------------------------------------------
    // Closest target
    // -------------------------------------------------------

    tof.setTargetOrder(SF_VL53L5CX_TARGET_ORDER::CLOSEST);

    // -------------------------------------------------------
    // Start ranging
    // -------------------------------------------------------

    if (!tof.startRanging())
    {
        Serial.println("Failed to start ranging");
        return false;
    }

    Serial.println("Ranging Started");

    return true;
}

// ============================================================================
// Read One Frame
// ============================================================================

bool updateFrame()
{
    if (!tof.isDataReady())
    {
        return false;
    }

    if (!tof.getRangingData(&measurementData))
    {
        return false;
    }

    for (uint8_t i = 0; i < IMAGE_SIZE; i++)
    {
        uint16_t d = measurementData.distance_mm[i];

        // Replace invalid readings with zero
        if (d == 0 || d == 65535)
        {
            d = 0;
        }

        distanceFrame[i] = d;
    }

    frameCounter++;

    lastFrameTime = millis();

    return true;
}

// ============================================================================
// Setup
// ============================================================================

void setup()
{
    Serial.begin(9600);

    delay(2000);

    Serial.println();
    Serial.println("======================================");
    Serial.println("SixthSense");
    Serial.println("Arduino UNO Q");
    Serial.println("VL53L5CX");
    Serial.println("======================================");

    distanceFrame.fill(0);

    sensorRunning = initSensor();

    Bridge.begin();

    Bridge.provide("get_frame", get_frame);
    Bridge.provide("get_frame_counter", get_frame_counter);
    Bridge.provide("get_timestamp", get_timestamp);
    Bridge.provide("sensor_ready", sensor_ready);

    if(sensorRunning)
    {
        Serial.println();
        Serial.println("System Ready");
    }
    else
    {
        Serial.println();
        Serial.println("Sensor Initialization FAILED");
    }

    Serial.println();
}

// ============================================================================
// Loop
// ============================================================================

void loop()
{
    if(!sensorRunning)
    {
        delay(100);
        return;
    }

    if(updateFrame())
    {
        // Print one message every second
        if(frameCounter % 15 == 0)
        {
            Serial.print("Frame : ");
            Serial.print(frameCounter);

            Serial.print("   Center : ");
            Serial.print(distanceFrame[27]);

            Serial.println(" mm");
        }
    }

    delay(2);
}