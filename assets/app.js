/******************************************************************************
 *
 * SixthSense
 *
 * Version : 2.1.0
 *
 * Dashboard JavaScript
 *
 ******************************************************************************/

/******************************************************************************
 * Configuration
 ******************************************************************************/

const APP_NAME = "SixthSense";

const APP_VERSION = "2.1.0";

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

const canvas =
    document.getElementById("tof-canvas");

const ctx =
    canvas.getContext("2d");

/******************************************************************************
 * Cached DOM Elements
 ******************************************************************************/

/*---------------------------------------------------------------------------
Sensor Information
---------------------------------------------------------------------------*/

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

/*---------------------------------------------------------------------------
Sector Cards
---------------------------------------------------------------------------*/

const sector0DistanceElement =
    document.getElementById("sector0-distance");

const sector1DistanceElement =
    document.getElementById("sector1-distance");

const sector2DistanceElement =
    document.getElementById("sector2-distance");

/*
 * New in v2.1.0
 */

const sector0VelocityElement =
    document.getElementById("sector0-velocity");

const sector1VelocityElement =
    document.getElementById("sector1-velocity");

const sector2VelocityElement =
    document.getElementById("sector2-velocity");

const sector0StateElement =
    document.getElementById("sector0-state");

const sector1StateElement =
    document.getElementById("sector1-state");

const sector2StateElement =
    document.getElementById("sector2-state");

/*---------------------------------------------------------------------------
System Status
---------------------------------------------------------------------------*/

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

/*---------------------------------------------------------------------------
Debug
---------------------------------------------------------------------------*/

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

    browserStatusElement.textContent =
        "CONNECTED";

    browserStatusElement.className =
        "status-online";

    /*
     * Arduino App Lab expects a payload.
     */

    socket.emit(
        "get_initial_state",
        {}
    );
});

socket.on("disconnect", () =>
{
    connected = false;

    console.log("Disconnected.");

    browserStatusElement.textContent =
        "DISCONNECTED";

    browserStatusElement.className =
        "status-offline";
});

/******************************************************************************
 * Dashboard Messages
 ******************************************************************************/

socket.on("tof_frame", (message) =>
{
    messageCount++;

    messageCountElement.textContent =
        messageCount;

    lastUpdateElement.textContent =
        new Date().toLocaleTimeString();

    observation =
        message.observation;

    updateDashboard(message);

    updateHeatmap(message);
});

/******************************************************************************
 * Startup
 ******************************************************************************/

window.addEventListener("load", () =>
{
    dashboardVersionElement.textContent =
        APP_VERSION;

    historyCapacityElement.textContent =
        20;

    console.log(
        APP_NAME +
        " Dashboard Started"
    );
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

    updateSensorInformation(
        observation
    );

    updateSectorCards(
        observation
    );

    updateSystemStatus(
        observation
    );

    updateObservationJSON(
        observation
    );
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

    if (observation.sectors.length !== 3)
        return;

    updateSector(
        observation.sectors[0],
        sector0DistanceElement,
        sector0VelocityElement,
        sector0StateElement
    );

    updateSector(
        observation.sectors[1],
        sector1DistanceElement,
        sector1VelocityElement,
        sector1StateElement
    );

    updateSector(
        observation.sectors[2],
        sector2DistanceElement,
        sector2VelocityElement,
        sector2StateElement
    );
}

/******************************************************************************
 * Sector Update
 ******************************************************************************/

function updateSector(
    sector,
    distanceElement,
    velocityElement,
    stateElement
)
{
    distanceElement.textContent =
        sector.distance_mm;

    velocityElement.textContent =
        sector.velocity_mmps.toFixed(1);

    stateElement.textContent =
        sector.velocity_state;

    stateElement.className = "";

    switch (sector.velocity_state)
    {
        case "Approaching":

            stateElement.classList.add(
                "status-danger"
            );

            break;

        case "Receding":

            stateElement.classList.add(
                "status-online"
            );

            break;

        default:

            stateElement.classList.add(
                "status-warning"
            );
    }
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

    bridgeStatusElement.textContent =
        "CONNECTED";

    bridgeStatusElement.className =
        "status-online";

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

    historySizeElement.textContent =
        observation.history_size;

    historyCapacityElement.textContent =
        "20";
}

/******************************************************************************
 * Heatmap Renderer
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

function drawHeatmap(image)
{
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

            if (distance !== 0)
            {
                ctx.fillStyle = "#000";

                ctx.font = "12px Arial";

                ctx.textAlign = "center";

                ctx.textBaseline = "middle";

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

    /*
     * Sector 0 | Sector 1
     */

    ctx.beginPath();

    ctx.moveTo(
        cellWidth * 2,
        0
    );

    ctx.lineTo(
        cellWidth * 2,
        canvas.height
    );

    ctx.stroke();

    /*
     * Sector 1 | Sector 2
     */

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

    /*
     * Hue
     *
     * 0 mm      -> Red
     * 3000 mm   -> Green
     */

    const hue =
        normalized * 120;

    return `hsl(${hue},100%,50%)`;
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

    switch (value)
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

        case "Approaching":

            element.classList.add(
                "status-danger"
            );

            break;

        case "Receding":

            element.classList.add(
                "status-online"
            );

            break;

        case "Stationary":

            element.classList.add(
                "status-warning"
            );

            break;

        default:

            element.classList.add(
                "status-warning"
            );
    }
}

/******************************************************************************
 * Dashboard Initialization
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

    historySizeElement.textContent =
        "0";

    historyCapacityElement.textContent =
        "20";

    observationJsonElement.textContent =
        "Waiting for observations...";
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
        if (!observation)
            return;

        drawHeatmap(
            observation.image ?? []
        );
    }
);

/******************************************************************************
 * Dashboard Refresh
 *
 * Reserved for future versions.
 ******************************************************************************/

function refreshDashboard()
{
    if (!observation)
        return;

    updateDashboard(
        {
            observation: observation
        }
    );
}

/******************************************************************************
 * Future Roadmap
 *
 * v2.2.0
 * --------
 *  - Observation Persistence
 *  - Persistence Visualization
 *
 * v3.0.0
 * --------
 *  - Multi-ToF Observation
 *  - Six Independent Observation Engines
 *
 * v4.0.0
 * --------
 *  - Context Engine
 *
 * v5.0.0
 * --------
 *  - Attention Engine
 *
 * v6.0.0
 * --------
 *  - Feedback Engine
 *
 ******************************************************************************/

/******************************************************************************
 * Dashboard Validation
 ******************************************************************************/

function validateObservation(observation)
{
    if (!observation)
        return false;

    if (!observation.sectors)
        return false;

    if (observation.sectors.length !== 3)
        return false;

    return true;
}

/******************************************************************************
 * Browser Diagnostics
 ******************************************************************************/

function printDashboardInfo()
{
    console.log("==========================================");

    console.log(APP_NAME);

    console.log("Dashboard Version :", APP_VERSION);

    console.log("Temporal ToF Observation Engine");

    console.log("==========================================");
}

/******************************************************************************
 * Application Startup
 ******************************************************************************/

window.addEventListener(
    "DOMContentLoaded",
    () =>
    {
        printDashboardInfo();

        initializeDashboard();
    }
);

/******************************************************************************
 * End of File
 *
 * SixthSense
 *
 * Version : 2.1.0
 *
 ******************************************************************************/