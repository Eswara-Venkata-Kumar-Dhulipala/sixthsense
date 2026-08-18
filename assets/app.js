/******************************************************************************
 * SixthSense
 * Version : 2.3.0
 * Dashboard JavaScript
 ******************************************************************************/

/*****************************************************************************/
/* Configuration                                                             */
/*****************************************************************************/

const APP_NAME = "SixthSense";
const APP_VERSION = "2.3.0";

const HEATMAP_ROWS = 8;
const HEATMAP_COLS = 8;

const INVALID_DISTANCE = 4000;
const MAX_DISTANCE = 3000;

const HISTORY_CAPACITY = 20;

const CONFIDENCE_HIGH = 80;
const CONFIDENCE_MEDIUM = 50;

/*****************************************************************************/
/* Global State                                                              */
/*****************************************************************************/

let socket = null;
let observation = null;
let lastMessage = null;
let messageCount = 0;
let connected = false;

/*****************************************************************************/
/* Canvas                                                                    */
/*****************************************************************************/

const distanceCanvas = document.getElementById("tof-canvas");
const distanceCtx = distanceCanvas.getContext("2d");

const confidenceCanvas = document.getElementById("confidence-canvas");
const confidenceCtx = confidenceCanvas.getContext("2d");

/*****************************************************************************/
/* Cached DOM Elements                                                       */
/*****************************************************************************/

const applicationVersionElement =
    document.getElementById("application-version");

/* Sensor Information */

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

/* Sector 0 */

const sector0DistanceElement =
    document.getElementById("sector0-distance");

const sector0ConfidenceElement =
    document.getElementById("sector0-confidence");

const sector0ConfidenceLevelElement =
    document.getElementById("sector0-confidence-level");

const sector0ZoneElement =
    document.getElementById("sector0-zone");

const sector0VelocityElement =
    document.getElementById("sector0-velocity");

const sector0VelocityStateElement =
    document.getElementById("sector0-velocity-state");

const sector0PersistenceElement =
    document.getElementById("sector0-persistence");

/* Sector 1 */

const sector1DistanceElement =
    document.getElementById("sector1-distance");

const sector1ConfidenceElement =
    document.getElementById("sector1-confidence");

const sector1ConfidenceLevelElement =
    document.getElementById("sector1-confidence-level");

const sector1ZoneElement =
    document.getElementById("sector1-zone");

const sector1VelocityElement =
    document.getElementById("sector1-velocity");

const sector1VelocityStateElement =
    document.getElementById("sector1-velocity-state");

const sector1PersistenceElement =
    document.getElementById("sector1-persistence");

/* Sector 2 */

const sector2DistanceElement =
    document.getElementById("sector2-distance");

const sector2ConfidenceElement =
    document.getElementById("sector2-confidence");

const sector2ConfidenceLevelElement =
    document.getElementById("sector2-confidence-level");

const sector2ZoneElement =
    document.getElementById("sector2-zone");

const sector2VelocityElement =
    document.getElementById("sector2-velocity");

const sector2VelocityStateElement =
    document.getElementById("sector2-velocity-state");

const sector2PersistenceElement =
    document.getElementById("sector2-persistence");

/* System Status */

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

/* Debug */

const observationJsonElement =
    document.getElementById("observation-json");

const dashboardVersionElement =
    document.getElementById("dashboard-version");

const backendVersionElement =
    document.getElementById("backend-version");

const lastUpdateElement =
    document.getElementById("last-update");

const messageCountElement =
    document.getElementById("message-count");

/*****************************************************************************/
/* Socket.IO                                                                 */
/*****************************************************************************/

socket = io();

socket.on("connect", () =>
{
    connected = true;

    console.log("Connected to backend.");

    setStatus(
        browserStatusElement,
        "CONNECTED",
        "status-online"
    );

    socket.emit(
        "get_initial_state",
        {}
    );
});

socket.on("disconnect", () =>
{
    connected = false;

    console.log("Disconnected from backend.");

    setStatus(
        browserStatusElement,
        "DISCONNECTED",
        "status-offline"
    );

    setStatus(
        bridgeStatusElement,
        "WAITING",
        "status-warning"
    );
});

/*****************************************************************************/
/* Dashboard Messages                                                        */
/*****************************************************************************/

socket.on("tof_frame", (message) =>
{
    if (!message || !message.observation)
        return;

    lastMessage = message;
    observation = message.observation;

    messageCount++;

    messageCountElement.textContent =
        messageCount;

    lastUpdateElement.textContent =
        new Date().toLocaleTimeString();

    if (message.app_version)
    {
        backendVersionElement.textContent =
            message.app_version;
    }

    updateDashboard(message);
    updateHeatmaps(message);
});

/*****************************************************************************/
/* Dashboard Initialization                                                  */
/*****************************************************************************/

function initializeDashboard()
{
    applicationVersionElement.textContent =
        `v${APP_VERSION}`;

    dashboardVersionElement.textContent =
        APP_VERSION;

    backendVersionElement.textContent =
        "--";

    historySizeElement.textContent =
        "0";

    historyCapacityElement.textContent =
        HISTORY_CAPACITY;

    messageCountElement.textContent =
        "0";

    observationJsonElement.textContent =
        "Waiting for observations...";

    setStatus(
        bridgeStatusElement,
        "WAITING",
        "status-warning"
    );

    setStatus(
        browserStatusElement,
        "DISCONNECTED",
        "status-offline"
    );

    setStatus(
        tofStatusElement,
        "OFFLINE",
        "status-offline"
    );

    console.log("==========================================");
    console.log(APP_NAME);
    console.log("Dashboard Version :", APP_VERSION);
    console.log("Temporal ToF + Confidence + Motion Persistence Engine");
    console.log("==========================================");
}

/*****************************************************************************/
/* Dashboard Update                                                          */
/*****************************************************************************/

function updateDashboard(message)
{
    if (!message || !message.observation)
        return;

    const currentObservation =
        message.observation;

    updateSensorInformation(
        currentObservation
    );

    updateSectorCards(
        currentObservation
    );

    updateSystemStatus(
        currentObservation
    );

    updateObservationJSON(
        currentObservation
    );
}

/*****************************************************************************/
/* Sensor Information                                                        */
/*****************************************************************************/

function updateSensorInformation(currentObservation)
{
    setText(
        sensorIdElement,
        currentObservation.sensor_id
    );

    setText(
        sensorNameElement,
        currentObservation.sensor_name
    );

    setText(
        sensorFrameElement,
        currentObservation.frame_number
    );

    setText(
        sensorTimestampElement,
        currentObservation.timestamp
    );

    setText(
        sensorFpsElement,
        formatNumber(currentObservation.fps, 1)
    );

    if (currentObservation.status === "ONLINE")
    {
        setStatus(
            sensorStatusElement,
            "ONLINE",
            "status-online"
        );
    }
    else
    {
        setStatus(
            sensorStatusElement,
            currentObservation.status ?? "OFFLINE",
            "status-offline"
        );
    }
}

/*****************************************************************************/
/* Sector Cards                                                              */
/*****************************************************************************/

function updateSectorCards(currentObservation)
{
    if (!validateObservation(currentObservation))
        return;

    updateSector(
        currentObservation.sectors[0],
        sector0DistanceElement,
        sector0ConfidenceElement,
        sector0ConfidenceLevelElement,
        sector0ZoneElement,
        sector0VelocityElement,
        sector0VelocityStateElement,
        sector0PersistenceElement
    );

    updateSector(
        currentObservation.sectors[1],
        sector1DistanceElement,
        sector1ConfidenceElement,
        sector1ConfidenceLevelElement,
        sector1ZoneElement,
        sector1VelocityElement,
        sector1VelocityStateElement,
        sector1PersistenceElement
    );

    updateSector(
        currentObservation.sectors[2],
        sector2DistanceElement,
        sector2ConfidenceElement,
        sector2ConfidenceLevelElement,
        sector2ZoneElement,
        sector2VelocityElement,
        sector2VelocityStateElement,
        sector2PersistenceElement
    );
}

function updateSector(
    sector,
    distanceElement,
    confidenceElement,
    confidenceLevelElement,
    zoneElement,
    velocityElement,
    velocityStateElement,
    persistenceElement
)
{
    const distance =
        Number(sector.distance_mm ?? 0);

    const confidence =
        Number(sector.confidence ?? 0);

    const velocity =
        Number(sector.velocity_mmps ?? 0);

    const velocityValid =
        Boolean(sector.velocity_valid ?? false);

    const motionPersistence =
        Number(sector.motion_persistence ?? 0);

    distanceElement.textContent =
        distance > 0 ? distance : "--";

    confidenceElement.textContent =
        Number.isFinite(confidence)
            ? confidence.toFixed(1)
            : "0.0";

    zoneElement.textContent =
        Number(sector.zone_id) >= 0
            ? sector.zone_id
            : "--";

    velocityElement.textContent =
        velocityValid && Number.isFinite(velocity)
            ? velocity.toFixed(1)
            : "--";

    persistenceElement.textContent =
        Number.isFinite(motionPersistence)
            ? Math.max(0, Math.min(100, Math.round(motionPersistence)))
            : "0";

    const confidenceInfo =
        confidenceClassification(confidence);

    confidenceLevelElement.textContent =
        confidenceInfo.label;

    confidenceLevelElement.className =
        `confidence-badge ${confidenceInfo.className}`;

    const velocityState =
        sector.velocity_state ?? "Unknown";

    velocityStateElement.textContent = velocityState;
    velocityStateElement.className = "state-value";

    switch (velocityState)
    {
        case "Approaching":
            velocityStateElement.classList.add(
                "status-danger"
            );
            break;

        case "Receding":
            velocityStateElement.classList.add(
                "status-online"
            );
            break;

        case "Stationary":
            velocityStateElement.classList.add(
                "status-warning"
            );
            break;

        default:
            velocityStateElement.classList.add(
                "status-unknown"
            );
            break;
    }
}

/*****************************************************************************/
/* Confidence Presentation                                                   */
/*****************************************************************************/

function confidenceClassification(confidence)
{
    if (!Number.isFinite(confidence) || confidence <= 0)
    {
        return {
            label: "INVALID",
            className: "confidence-invalid"
        };
    }

    if (confidence >= CONFIDENCE_HIGH)
    {
        return {
            label: "HIGH",
            className: "confidence-high"
        };
    }

    if (confidence >= CONFIDENCE_MEDIUM)
    {
        return {
            label: "MEDIUM",
            className: "confidence-medium"
        };
    }

    return {
        label: "LOW",
        className: "confidence-low"
    };
}

/*****************************************************************************/
/* JSON Viewer                                                               */
/*****************************************************************************/

function updateObservationJSON(currentObservation)
{
    observationJsonElement.textContent =
        JSON.stringify(
            currentObservation,
            null,
            4
        );
}

/*****************************************************************************/
/* System Status                                                             */
/*****************************************************************************/

function updateSystemStatus(currentObservation)
{
    if (connected)
    {
        setStatus(
            browserStatusElement,
            "CONNECTED",
            "status-online"
        );
    }
    else
    {
        setStatus(
            browserStatusElement,
            "DISCONNECTED",
            "status-offline"
        );
    }

    /* A valid tof_frame proves that RouterBridge is operational. */

    setStatus(
        bridgeStatusElement,
        "CONNECTED",
        "status-online"
    );

    if (currentObservation.status === "ONLINE")
    {
        setStatus(
            tofStatusElement,
            "ONLINE",
            "status-online"
        );
    }
    else
    {
        setStatus(
            tofStatusElement,
            currentObservation.status ?? "OFFLINE",
            "status-offline"
        );
    }

    setText(
        historySizeElement,
        currentObservation.history_size ?? 0
    );

    setText(
        historyCapacityElement,
        HISTORY_CAPACITY
    );
}

/*****************************************************************************/
/* Heatmaps                                                                  */
/*****************************************************************************/

function updateHeatmaps(message)
{
    if (message.image)
    {
        drawDistanceHeatmap(
            message.image
        );
    }

    if (message.confidence_image)
    {
        drawConfidenceHeatmap(
            message.confidence_image
        );
    }
}

function drawDistanceHeatmap(image)
{
    drawHeatmap(
        distanceCtx,
        distanceCanvas,
        image,
        distanceToColor,
        (value) => value > 0 ? `${Math.round(value)}` : ""
    );
}

function drawConfidenceHeatmap(image)
{
    drawHeatmap(
        confidenceCtx,
        confidenceCanvas,
        image,
        confidenceToColor,
        (value) => Number.isFinite(Number(value))
            ? `${Math.round(Number(value))}%`
            : ""
    );
}

function drawHeatmap(
    context,
    targetCanvas,
    image,
    colorFunction,
    labelFunction
)
{
    if (!Array.isArray(image) || image.length === 0)
        return;

    const rows = image.length;
    const cols = image[0].length;

    if (rows !== HEATMAP_ROWS || cols !== HEATMAP_COLS)
    {
        console.warn(
            "Unexpected heatmap size:",
            rows,
            "x",
            cols
        );
    }

    const cellWidth =
        targetCanvas.width / cols;

    const cellHeight =
        targetCanvas.height / rows;

    context.clearRect(
        0,
        0,
        targetCanvas.width,
        targetCanvas.height
    );

    for (let row = 0; row < rows; row++)
    {
        for (let col = 0; col < cols; col++)
        {
            const value =
                Number(image[row][col]);

            context.fillStyle =
                colorFunction(value);

            context.fillRect(
                col * cellWidth,
                row * cellHeight,
                cellWidth,
                cellHeight
            );

            context.strokeStyle = "#475569";
            context.lineWidth = 1;

            context.strokeRect(
                col * cellWidth,
                row * cellHeight,
                cellWidth,
                cellHeight
            );

            const label =
                labelFunction(value);

            if (label)
            {
                context.fillStyle =
                    readableTextColor(
                        colorFunction(value)
                    );

                context.font =
                    "bold 12px Arial";

                context.textAlign =
                    "center";

                context.textBaseline =
                    "middle";

                context.fillText(
                    label,
                    col * cellWidth + cellWidth / 2,
                    row * cellHeight + cellHeight / 2
                );
            }
        }
    }

    drawSectorBoundaries(
        context,
        targetCanvas,
        cellWidth
    );
}

function drawSectorBoundaries(
    context,
    targetCanvas,
    cellWidth
)
{
    context.save();

    context.strokeStyle = "#dc2626";
    context.lineWidth = 3;

    context.beginPath();
    context.moveTo(cellWidth * 2, 0);
    context.lineTo(cellWidth * 2, targetCanvas.height);
    context.stroke();

    context.beginPath();
    context.moveTo(cellWidth * 5, 0);
    context.lineTo(cellWidth * 5, targetCanvas.height);
    context.stroke();

    context.restore();
}

/*****************************************************************************/
/* Heatmap Colour Maps                                                       */
/*****************************************************************************/

function distanceToColor(distance)
{
    if (!Number.isFinite(distance) || distance <= 0)
        return "#ffffff";

    if (distance >= INVALID_DISTANCE)
        return "#ffffff";

    const normalized =
        Math.min(distance, MAX_DISTANCE) / MAX_DISTANCE;

    /* 0 mm -> red, 3000 mm -> green */

    const hue =
        normalized * 120;

    return `hsl(${hue}, 100%, 50%)`;
}

function confidenceToColor(confidence)
{
    if (!Number.isFinite(confidence) || confidence <= 0)
        return "#f8fafc";

    const normalized =
        Math.max(0, Math.min(100, confidence));

    /* 0% -> red, 100% -> green */

    const hue =
        normalized * 1.2;

    return `hsl(${hue}, 85%, 48%)`;
}

/*
 * The generated heatmap colors are mostly bright. Black text provides the
 * clearest contrast for this palette. Kept as a helper to make the renderer
 * easy to extend later.
 */
function readableTextColor(_background)
{
    return "#111827";
}

/*****************************************************************************/
/* Utilities                                                                 */
/*****************************************************************************/

function setText(
    element,
    value
)
{
    if (!element)
        return;

    element.textContent =
        value ?? "--";
}

function setStatus(
    element,
    value,
    className
)
{
    if (!element)
        return;

    element.textContent = value;
    element.className = className;
}

function formatNumber(
    value,
    digits
)
{
    const number = Number(value);

    if (!Number.isFinite(number))
        return "--";

    return number.toFixed(digits);
}

function validateObservation(currentObservation)
{
    if (!currentObservation)
        return false;

    if (!Array.isArray(currentObservation.sectors))
        return false;

    return currentObservation.sectors.length === 3;
}

/*****************************************************************************/
/* Resize                                                                    */
/*****************************************************************************/

window.addEventListener(
    "resize",
    () =>
    {
        if (!lastMessage)
            return;

        updateHeatmaps(
            lastMessage
        );
    }
);

/*****************************************************************************/
/* Startup                                                                   */
/*****************************************************************************/

window.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);

/*****************************************************************************/
/* End of File                                                               */
/* SixthSense Dashboard v2.3.0                                               */
/*****************************************************************************/
