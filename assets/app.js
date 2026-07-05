/******************************************************************************
 *
 * SixthSense
 *
 * Version : 2.0.0.2
 *
 * Dashboard JavaScript
 *
 * Platform : Arduino UNO Q
 *
 ******************************************************************************/

/******************************************************************************
 * Configuration
 ******************************************************************************/

const APP_NAME = "SixthSense";

const APP_VERSION = "2.0.0.2";

const HEATMAP_ROWS = 8;

const HEATMAP_COLS = 8;

const INVALID_DISTANCE = 4000;

const MAX_DISTANCE = 3000;

/******************************************************************************
 * Global State
 ******************************************************************************/

let socket = null;

let observation = null;

let messageCount = 0;

let connected = false;

/******************************************************************************
 * Heatmap
 ******************************************************************************/

const canvas = document.getElementById("tof-canvas");

const ctx = canvas.getContext("2d");

/******************************************************************************
 * Cached DOM Elements
 ******************************************************************************/

/*----------------------------------------------------------
Sensor Information
----------------------------------------------------------*/

const sensorIdElement =
    document.getElementById("sensor-id");

const sensorNameElement =
    document.getElementById("sensor-name");

const sensorStatusElement =
    document.getElementById("sensor-status");

const sensorFrameElement =
    document.getElementById("sensor-frame");

const sensorTimestampElement =
    document.getElementById("sensor-timestamp");

const sensorFpsElement =
    document.getElementById("sensor-fps");

/*----------------------------------------------------------
Sector Cards
----------------------------------------------------------*/

const sector0DistanceElement =
    document.getElementById("sector0-distance");

const sector1DistanceElement =
    document.getElementById("sector1-distance");

const sector2DistanceElement =
    document.getElementById("sector2-distance");

/*----------------------------------------------------------
System Status
----------------------------------------------------------*/

const bridgeStatusElement =
    document.getElementById("bridge-status");

const browserStatusElement =
    document.getElementById("browser-status");

const tofStatusElement =
    document.getElementById("tof-status");

const historySizeElement =
    document.getElementById("history-size");

const historyCapacityElement =
    document.getElementById("history-capacity");

/*----------------------------------------------------------
Debug
----------------------------------------------------------*/

const observationJsonElement =
    document.getElementById("observation-json");

const dashboardVersionElement =
    document.getElementById("dashboard-version");

const lastUpdateElement =
    document.getElementById("last-update");

const messageCountElement =
    document.getElementById("message-count");

/******************************************************************************
 * Socket.IO
 ******************************************************************************/

socket = io();

/******************************************************************************
 * Connection Events
 ******************************************************************************/

socket.on("connect", () =>
{
    connected = true;

    console.log("Connected to backend.");

    browserStatusElement.textContent = "CONNECTED";
    browserStatusElement.className = "status-online";

    socket.emit("get_initial_state");
});

socket.on("disconnect", () =>
{
    connected = false;

    console.log("Disconnected.");

    browserStatusElement.textContent = "DISCONNECTED";
    browserStatusElement.className = "status-offline";
});

/******************************************************************************
 * Dashboard Message
 ******************************************************************************/

socket.on("tof_frame", (message) =>
{
    messageCount++;

    messageCountElement.textContent = messageCount;

    lastUpdateElement.textContent =
        new Date().toLocaleTimeString();

    observation = message.observation;

    updateDashboard(message);
    
    updateHeatmap(message);
});

/******************************************************************************
 * Startup
 ******************************************************************************/

window.addEventListener("load", () =>
{
    dashboardVersionElement.textContent = APP_VERSION;

    historyCapacityElement.textContent = 20;

    console.log(APP_NAME + " Dashboard Started");
});
/******************************************************************************
 * Dashboard Update
 ******************************************************************************/

function updateDashboard(message)
{
    if (!message)
        return;

    if (!message.observation)
        return;

    observation = message.observation;

    updateSensorInformation(observation);

    updateSectorCards(observation);

    updateObservationJSON(observation);

    updateSystemStatus(observation);
}

/******************************************************************************
 * Sensor Information
 ******************************************************************************/

function updateSensorInformation(observation)
{
    sensorIdElement.textContent =
        observation.sensor_id;

    sensorNameElement.textContent =
        observation.sensor_name;

    sensorStatusElement.textContent =
        observation.status;

    sensorFrameElement.textContent =
        observation.frame_number;

    sensorTimestampElement.textContent =
        observation.timestamp;

    sensorFpsElement.textContent =
        observation.fps;

    //
    // Status colour
    //

    sensorStatusElement.className = "";

    if (observation.status === "ONLINE")
    {
        sensorStatusElement.classList.add(
            "status-online"
        );
    }
    else
    {
        sensorStatusElement.classList.add(
            "status-offline"
        );
    }
}

/******************************************************************************
 * Sector Cards
 ******************************************************************************/

function updateSectorCards(observation)
{
    if (!observation.sectors)
        return;

    if (observation.sectors.length < 3)
        return;

    sector0DistanceElement.textContent =
        observation.sectors[0].distance;

    sector1DistanceElement.textContent =
        observation.sectors[1].distance;

    sector2DistanceElement.textContent =
        observation.sectors[2].distance;
}

/******************************************************************************
 * Observation JSON
 ******************************************************************************/

function updateObservationJSON(observation)
{
    observationJsonElement.textContent =
        JSON.stringify(
            observation,
            null,
            4
        );
}

/******************************************************************************
 * System Status
 ******************************************************************************/

function updateSystemStatus(observation)
{
    //
    // Browser
    //

    if (connected)
    {
        browserStatusElement.textContent =
            "CONNECTED";

        browserStatusElement.className =
            "status-online";
    }
    else
    {
        browserStatusElement.textContent =
            "DISCONNECTED";

        browserStatusElement.className =
            "status-offline";
    }

    //
    // Bridge
    //

    bridgeStatusElement.textContent =
        "CONNECTED";

    bridgeStatusElement.className =
        "status-online";

    //
    // ToF
    //

    tofStatusElement.textContent =
        observation.status;

    tofStatusElement.className = "";

    if (observation.status === "ONLINE")
    {
        tofStatusElement.classList.add(
            "status-online"
        );
    }
    else
    {
        tofStatusElement.classList.add(
            "status-offline"
        );
    }

    //
    // History Buffer
    //
    // (Will become dynamic in v2.1.0)
    //

    historySizeElement.textContent = "--";
}
/******************************************************************************
 * Heatmap Renderer
 ******************************************************************************/

function drawHeatmap(image)
{
    if (!image)
        return;

    const rows = image.length;

    const cols = image[0].length;

    const cellWidth =
        canvas.width / cols;

    const cellHeight =
        canvas.height / rows;

    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    for (let row = 0; row < rows; row++)
    {
        for (let col = 0; col < cols; col++)
        {
            const distance =
                image[row][col];

            ctx.fillStyle =
                distanceToColor(distance);

            ctx.fillRect(
                col * cellWidth,
                row * cellHeight,
                cellWidth,
                cellHeight
            );

            ctx.strokeStyle = "#444";

            ctx.strokeRect(
                col * cellWidth,
                row * cellHeight,
                cellWidth,
                cellHeight
            );

            ctx.fillStyle = "#000";

            ctx.font = "12px Arial";

            ctx.textAlign = "center";

            ctx.textBaseline = "middle";

            if (distance !== 0)
            {
                ctx.fillText(
                    distance,
                    col * cellWidth + cellWidth / 2,
                    row * cellHeight + cellHeight / 2
                );
            }
        }
    }

    drawSectorBoundaries(
        cellWidth,
        cellHeight
    );
}

/******************************************************************************
 * Sector Overlay
 ******************************************************************************/

function drawSectorBoundaries(
    cellWidth,
    cellHeight
)
{
    ctx.strokeStyle = "#ff0000";

    ctx.lineWidth = 3;

    //
    // Sector 0 | Sector 1
    //

    ctx.beginPath();

    ctx.moveTo(
        cellWidth * 3,
        0
    );

    ctx.lineTo(
        cellWidth * 3,
        canvas.height
    );

    ctx.stroke();

    //
    // Sector 1 | Sector 2
    //

    ctx.beginPath();

    ctx.moveTo(
        cellWidth * 5,
        0
    );

    ctx.lineTo(
        cellWidth * 5,
        canvas.height
    );

    ctx.stroke();

    ctx.lineWidth = 1;
}

/******************************************************************************
 * Distance Colour Map
 ******************************************************************************/

function distanceToColor(distance)
{
    if (distance === 0)
        return "#ffffff";

    if (distance >= INVALID_DISTANCE)
        return "#ffffff";

    const normalized =
        Math.min(
            distance,
            MAX_DISTANCE
        ) / MAX_DISTANCE;

    //
    // Hue:
    //
    // 0 mm      -> Red
    // 3000 mm   -> Green
    //

    const hue =
        normalized * 120;

    return `hsl(${hue},100%,50%)`;
}

/******************************************************************************
 * Heatmap Update
 ******************************************************************************/

function updateHeatmap(message)
{
    if (!message)
        return;

    if (!message.image)
        return;

    drawHeatmap(
        message.image
    );
}

/******************************************************************************
 * Utility Functions
 ******************************************************************************/

function setText(
    element,
    value
)
{
    if (!element)
        return;

    element.textContent = value;
}

function setStatus(
    element,
    value
)
{
    if (!element)
        return;

    element.textContent = value;

    element.className = "";

    switch(value)
    {
        case "ONLINE":

            element.classList.add(
                "status-online"
            );

            break;

        case "OFFLINE":

            element.classList.add(
                "status-offline"
            );

            break;

        default:

            element.classList.add(
                "status-warning"
            );
    }
}
/******************************************************************************
 * Initialization
 ******************************************************************************/

function initializeDashboard()
{
    console.log("==========================================");

    console.log(APP_NAME);

    console.log("Version :", APP_VERSION);

    console.log("==========================================");

    dashboardVersionElement.textContent =
        APP_VERSION;

    browserStatusElement.textContent =
        "DISCONNECTED";

    browserStatusElement.className =
        "status-offline";

    bridgeStatusElement.textContent =
        "WAITING";

    bridgeStatusElement.className =
        "status-warning";

    tofStatusElement.textContent =
        "OFFLINE";

    tofStatusElement.className =
        "status-offline";

    historyCapacityElement.textContent =
        "20";

    historySizeElement.textContent =
        "--";

    observationJsonElement.textContent =
        "Waiting for ToF observations...";
}

/******************************************************************************
 * Browser Ready
 ******************************************************************************/

window.addEventListener(
    "DOMContentLoaded",
    () =>
    {
        initializeDashboard();
    }
);

/******************************************************************************
 * Window Resize
 ******************************************************************************/

window.addEventListener(
    "resize",
    () =>
    {
        if(observation == null)
            return;

        //
        // Redraw heatmap
        //

        drawHeatmap(
            observation.image ??
            []
        );
    }
);

/******************************************************************************
 * Future Hooks
 ******************************************************************************/

/*
Version 2.1.0

    Velocity Engine

        computeVelocity()

        updateVelocity()

------------------------------------------------------------

Version 2.2.0

    Persistence Engine

        computePersistence()

------------------------------------------------------------

Version 3.0.0

    Camera Observation

------------------------------------------------------------

Version 4.0.0

    Context Engine

------------------------------------------------------------

Version 5.0.0

    Attention Engine

------------------------------------------------------------

Version 6.0.0

    Audio Engine

------------------------------------------------------------

Version 7.0.0

    Vibration Engine

*/

/******************************************************************************
 * End of File
 ******************************************************************************/