/*****************************************************************************/
/* SixthSense Dashboard - v2.2.1                                            */
/*****************************************************************************/

const APP_NAME = "SixthSense";
const APP_VERSION = "2.2.1";

const HISTORY_CAPACITY = 20;

const INVALID_DISTANCE = 4000;
const MAX_DISTANCE = 3000;

const CONFIDENCE_HIGH = 80;
const CONFIDENCE_MEDIUM = 50;


/*****************************************************************************/
/* Global State                                                              */
/*****************************************************************************/

let socket = null;

let connected = false;

let observation = null;

let lastMessage = null;

let messageCount = 0;


/*****************************************************************************/
/* Canvas                                                                    */
/*****************************************************************************/

const distanceCanvas =
    document.getElementById("tof-canvas");

const distanceCtx =
    distanceCanvas.getContext("2d");


const confidenceCanvas =
    document.getElementById("confidence-canvas");

const confidenceCtx =
    confidenceCanvas.getContext("2d");


/*****************************************************************************/
/* DOM References                                                            */
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


/* Sector Elements */

const sectorElements =
[
    0,
    1,
    2

].map(
    (id) =>
    ({
        distance:
            document.getElementById(
                `sector${id}-distance`
            ),

        confidence:
            document.getElementById(
                `sector${id}-confidence`
            ),

        confidenceLevel:
            document.getElementById(
                `sector${id}-confidence-level`
            ),

        zone:
            document.getElementById(
                `sector${id}-zone`
            ),

        velocity:
            document.getElementById(
                `sector${id}-velocity`
            ),

        state:
            document.getElementById(
                `sector${id}-state`
            )
    })
);


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


socket.on(
    "connect",
    () =>
    {
        connected = true;

        console.log(
            "Connected to backend."
        );

        setStatus(
            browserStatusElement,
            "CONNECTED",
            "status-online"
        );

        /*
         * Arduino Apps Lab expects a payload.
         */

        socket.emit(
            "get_initial_state",
            {}
        );
    }
);


socket.on(
    "disconnect",
    () =>
    {
        connected = false;

        console.log(
            "Disconnected from backend."
        );

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
    }
);


/*****************************************************************************/
/* ToF Messages                                                              */
/*****************************************************************************/

socket.on(
    "tof_frame",
    (message) =>
    {
        if (
            !message
            ||
            !message.observation
        )
        {
            return;
        }

        lastMessage =
            message;

        observation =
            message.observation;

        messageCount += 1;

        messageCountElement.textContent =
            messageCount;

        lastUpdateElement.textContent =
            new Date().toLocaleTimeString();

        if (
            message.app_version
        )
        {
            backendVersionElement.textContent =
                message.app_version;
        }

        updateDashboard(
            message
        );

        updateHeatmaps(
            message
        );
    }
);


/*****************************************************************************/
/* Dashboard Update                                                          */
/*****************************************************************************/

function updateDashboard(
    message
)
{
    if (
        !message
        ||
        !message.observation
    )
    {
        return;
    }

    const obs =
        message.observation;

    updateSensorInformation(
        obs
    );

    updateSectorCards(
        obs
    );

    updateSystemStatus(
        obs
    );

    updateObservationJSON(
        obs
    );
}


/*****************************************************************************/
/* Sensor Information                                                        */
/*****************************************************************************/

function updateSensorInformation(
    obs
)
{
    setText(
        sensorIdElement,
        obs.sensor_id ?? "--"
    );

    setText(
        sensorNameElement,
        obs.sensor_name ?? "--"
    );

    setText(
        sensorFrameElement,
        obs.frame_number ?? 0
    );

    setText(
        sensorTimestampElement,
        obs.timestamp ?? 0
    );

    setText(
        sensorFpsElement,
        Number(
            obs.fps ?? 0
        ).toFixed(1)
    );

    const online =
        obs.status === "ONLINE";

    setStatus(
        sensorStatusElement,
        obs.status ?? "OFFLINE",
        online
            ? "status-online"
            : "status-offline"
    );
}


/*****************************************************************************/
/* Sector Cards                                                              */
/*****************************************************************************/

function updateSectorCards(
    obs
)
{
    if (
        !Array.isArray(
            obs.sectors
        )
    )
    {
        return;
    }

    if (
        obs.sectors.length !== 3
    )
    {
        return;
    }

    obs.sectors.forEach(
        (
            sector,
            index
        ) =>
        {
            updateSector(
                sector,
                sectorElements[index]
            );
        }
    );
}


/*****************************************************************************/
/* Single Sector                                                             */
/*****************************************************************************/

function updateSector(
    sector,
    elements
)
{
    const distance =
        Number(
            sector.distance_mm ?? 0
        );

    const confidence =
        Number(
            sector.confidence ?? 0
        );

    const velocity =
        Number(
            sector.velocity_mmps ?? 0
        );

    const zoneId =
        Number.isInteger(
            sector.zone_id
        )
            ? sector.zone_id
            : -1;

    const velocityState =
        sector.velocity_state
        ??
        "Stationary";


    /*
     * Distance
     */

    elements.distance.textContent =
        distance > 0
            ? distance
            : "--";


    /*
     * Confidence
     */

    elements.confidence.textContent =
        confidence.toFixed(1);

    updateConfidenceBadge(
        elements.confidenceLevel,
        confidence
    );


    /*
     * Sensor Zone
     */

    elements.zone.textContent =
        zoneId >= 0
            ? zoneId
            : "--";


    /*
     * Velocity
     */

    elements.velocity.textContent =
        velocity.toFixed(1);


    /*
     * Motion State
     */

    elements.state.textContent =
        velocityState;

    updateVelocityState(
        elements.state,
        velocityState
    );
}


/*****************************************************************************/
/* Confidence Badge                                                          */
/*****************************************************************************/

function updateConfidenceBadge(
    element,
    confidence
)
{
    element.className =
        "confidence-level";

    if (
        confidence >=
        CONFIDENCE_HIGH
    )
    {
        element.textContent =
            "HIGH";

        element.classList.add(
            "confidence-high"
        );
    }

    else if (
        confidence >=
        CONFIDENCE_MEDIUM
    )
    {
        element.textContent =
            "MEDIUM";

        element.classList.add(
            "confidence-medium"
        );
    }

    else if (
        confidence > 0
    )
    {
        element.textContent =
            "LOW";

        element.classList.add(
            "confidence-low"
        );
    }

    else
    {
        element.textContent =
            "INVALID";

        element.classList.add(
            "confidence-invalid"
        );
    }
}


/*****************************************************************************/
/* Velocity State                                                            */
/*****************************************************************************/

function updateVelocityState(
    element,
    state
)
{
    element.className =
        "state-value";

    switch (
        state
    )
    {
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


        default:

            element.classList.add(
                "status-warning"
            );

            break;
    }
}


/*****************************************************************************/
/* System Status                                                             */
/*****************************************************************************/

function updateSystemStatus(
    obs
)
{
    /*
     * Browser
     */

    setStatus(
        browserStatusElement,

        connected
            ? "CONNECTED"
            : "DISCONNECTED",

        connected
            ? "status-online"
            : "status-offline"
    );


    /*
     * Arduino Bridge
     *
     * A valid tof_frame means the complete Bridge path is working.
     */

    setStatus(
        bridgeStatusElement,
        "CONNECTED",
        "status-online"
    );


    /*
     * ToF Sensor
     */

    const online =
        obs.status === "ONLINE";

    setStatus(
        tofStatusElement,
        obs.status ?? "OFFLINE",

        online
            ? "status-online"
            : "status-offline"
    );


    /*
     * History
     */

    historySizeElement.textContent =
        obs.history_size ?? 0;

    historyCapacityElement.textContent =
        HISTORY_CAPACITY;
}


/*****************************************************************************/
/* Observation JSON                                                          */
/*****************************************************************************/

function updateObservationJSON(
    obs
)
{
    observationJsonElement.textContent =
        JSON.stringify(
            obs,
            null,
            4
        );
}


/*****************************************************************************/
/* Heatmaps                                                                  */
/*****************************************************************************/

function updateHeatmaps(
    message
)
{
    if (
        Array.isArray(
            message.image
        )
    )
    {
        drawDistanceHeatmap(
            message.image
        );
    }

    if (
        Array.isArray(
            message.confidence_image
        )
    )
    {
        drawConfidenceHeatmap(
            message.confidence_image
        );
    }
}


/*****************************************************************************/
/* Distance Heatmap                                                          */
/*****************************************************************************/

function drawDistanceHeatmap(
    image
)
{
    drawGrid(

        distanceCanvas,

        distanceCtx,

        image,

        distanceToColor,

        (value) =>
        {
            if (
                value > 0
                &&
                value < INVALID_DISTANCE
            )
            {
                return `${Math.round(value)}`;
            }

            return "";
        }
    );
}


/*****************************************************************************/
/* Confidence Heatmap                                                        */
/*****************************************************************************/

function drawConfidenceHeatmap(
    image
)
{
    drawGrid(

        confidenceCanvas,

        confidenceCtx,

        image,

        confidenceToColor,

        (value) =>
            `${Number(value).toFixed(0)}%`
    );
}


/*****************************************************************************/
/* Generic 8x8 Grid Renderer                                                 */
/*****************************************************************************/

function drawGrid(
    canvas,
    ctx,
    image,
    colorFunction,
    textFunction
)
{
    if (
        !Array.isArray(
            image
        )
        ||
        image.length === 0
        ||
        !Array.isArray(
            image[0]
        )
    )
    {
        return;
    }

    const rows =
        image.length;

    const cols =
        image[0].length;

    const cellWidth =
        canvas.width
        /
        cols;

    const cellHeight =
        canvas.height
        /
        rows;


    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );


    for (
        let row = 0;
        row < rows;
        row++
    )
    {
        for (
            let col = 0;
            col < cols;
            col++
        )
        {
            const value =
                Number(
                    image[row][col]
                    ??
                    0
                );

            const x =
                col
                *
                cellWidth;

            const y =
                row
                *
                cellHeight;


            /*
             * Cell Background
             */

            const cellColor =
                colorFunction(
                    value
                );

            ctx.fillStyle =
                cellColor;

            ctx.fillRect(
                x,
                y,
                cellWidth,
                cellHeight
            );


            /*
             * Cell Border
             */

            ctx.strokeStyle =
                "#475569";

            ctx.lineWidth =
                1;

            ctx.strokeRect(
                x,
                y,
                cellWidth,
                cellHeight
            );


            /*
             * Cell Text
             */

            const text =
                textFunction(
                    value
                );

            if (
                text
            )
            {
                ctx.fillStyle =
                    getReadableTextColor(
                        cellColor
                    );

                ctx.font =
                    "600 13px Arial";

                ctx.textAlign =
                    "center";

                ctx.textBaseline =
                    "middle";

                ctx.fillText(

                    text,

                    x
                    +
                    cellWidth / 2,

                    y
                    +
                    cellHeight / 2
                );
            }
        }
    }


    /*
     * Logical sector boundaries
     */

    drawSectorBoundaries(
        canvas,
        ctx,
        cellWidth
    );
}


/*****************************************************************************/
/* Sector Boundaries                                                         */
/*****************************************************************************/

function drawSectorBoundaries(
    canvas,
    ctx,
    cellWidth
)
{
    ctx.save();

    ctx.strokeStyle =
        "#ef4444";

    ctx.lineWidth =
        4;

    /*
     * Sectors:
     *
     * 0 1 | 2 3 4 | 5 6 7
     */

    [
        2,
        5

    ].forEach(
        (column) =>
        {
            ctx.beginPath();

            ctx.moveTo(
                cellWidth
                *
                column,
                0
            );

            ctx.lineTo(
                cellWidth
                *
                column,
                canvas.height
            );

            ctx.stroke();
        }
    );

    ctx.restore();
}


/*****************************************************************************/
/* Distance Colour Mapping                                                   */
/*****************************************************************************/

function distanceToColor(
    distance
)
{
    if (
        distance <= 0
        ||
        distance >= INVALID_DISTANCE
    )
    {
        return "#ffffff";
    }

    const normalized =
        Math.min(
            distance,
            MAX_DISTANCE
        )
        /
        MAX_DISTANCE;

    /*
     * 0 mm    -> Red
     * 3000 mm -> Green
     */

    const hue =
        normalized
        *
        120;

    return `hsl(${hue}, 100%, 50%)`;
}


/*****************************************************************************/
/* Confidence Colour Mapping                                                 */
/*****************************************************************************/

function confidenceToColor(
    confidence
)
{
    const clamped =
        Math.max(
            0,
            Math.min(
                100,
                confidence
            )
        );

    if (
        clamped <= 0
    )
    {
        return "#e5e7eb";
    }

    /*
     * 0%   -> Red
     * 50%  -> Yellow
     * 100% -> Green
     */

    const hue =
        (
            clamped
            /
            100
        )
        *
        120;

    return `hsl(${hue}, 90%, 48%)`;
}


/*****************************************************************************/
/* Heatmap Text Colour                                                       */
/*****************************************************************************/

function getReadableTextColor(
    color
)
{
    if (
        color === "#ffffff"
        ||
        color === "#e5e7eb"
    )
    {
        return "#111827";
    }

    /*
     * Current heatmap colours are bright enough for dark text.
     */

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
    if (
        element
    )
    {
        element.textContent =
            value;
    }
}


function setStatus(
    element,
    value,
    className
)
{
    if (
        !element
    )
    {
        return;
    }

    element.textContent =
        value;

    element.className =
        className;
}


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

    lastUpdateElement.textContent =
        "--";


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

    setStatus(
        tofStatusElement,
        "OFFLINE",
        "status-offline"
    );

    setStatus(
        sensorStatusElement,
        "OFFLINE",
        "status-offline"
    );


    observationJsonElement.textContent =
        "Waiting for observations...";


    console.log(
        "=========================================="
    );

    console.log(
        APP_NAME
    );

    console.log(
        "Dashboard Version:",
        APP_VERSION
    );

    console.log(
        "Temporal ToF + Confidence Engine"
    );

    console.log(
        "=========================================="
    );
}


/*****************************************************************************/
/* Browser Ready                                                             */
/*****************************************************************************/

window.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);


/*****************************************************************************/
/* Window Resize                                                             */
/*****************************************************************************/

window.addEventListener(
    "resize",
    () =>
    {
        /*
         * Redraw using the complete last backend message.
         *
         * The old v2.1.0 implementation attempted to access
         * observation.image, but image belongs to the top-level message.
         */

        if (
            lastMessage
        )
        {
            updateHeatmaps(
                lastMessage
            );
        }
    }
);


/*****************************************************************************/
/* End of File                                                               */
/*****************************************************************************/