/****************************************************************************
 * SixthSense
 * Version : 3.0.0
 * Dashboard JavaScript
 * 6 x VL53L5CX / 4x4
 ****************************************************************************/

const APP_NAME = "SixthSense";
const APP_VERSION = "3.0.0";

const SENSOR_COUNT = 6;

const SENSOR_ORDER = [
    "T1",
    "T2",
    "T3",
    "T4",
    "T5",
    "T6"
];

const SENSOR_LABELS = {
    T1: "Front-right",
    T2: "Front",
    T3: "Front-left",
    T4: "Rear-left",
    T5: "Rear",
    T6: "Rear-right"
};

const HEATMAP_ROWS = 4;
const HEATMAP_COLS = 4;

const INVALID_DISTANCE = 4000;
const MAX_DISTANCE = 3000;

const HISTORY_CAPACITY = 20;
const MOTION_PERSISTENCE_MAX = 200;

const CONFIDENCE_HIGH = 80;
const CONFIDENCE_MEDIUM = 50;

const MOTOR_MASK_ALL = 0x0F;

const MOTOR_CONFIG = [
    {
        id: "M1",
        direction: "Front",
        bit: 0x01
    },
    {
        id: "M2",
        direction: "Left",
        bit: 0x02
    },
    {
        id: "M3",
        direction: "Rear",
        bit: 0x04
    },
    {
        id: "M4",
        direction: "Right",
        bit: 0x08
    }
];


/*****************************************************************************/
/* Global State                                                              */
/*****************************************************************************/

let socket = null;
let lastMessage = null;
let messageCount = 0;
let connected = false;

/*
 * T2 / Front is the default detail view.
 */
let selectedSensorId = "T2";


/*****************************************************************************/
/* DOM Helpers                                                               */
/*****************************************************************************/

const byId = (id) =>
    document.getElementById(id);


/*****************************************************************************/
/* Cached DOM Elements                                                       */
/*****************************************************************************/

const applicationVersionElement =
    byId("application-version");

const sensorOverviewGridElement =
    byId("sensor-overview-grid");

const sensorSelectorElement =
    byId("sensor-selector");


/* Haptic Motor Feedback */

const motorFeedbackStateElement =
    byId("motor-feedback-state");

const motorMapElement =
    byId("motor-map");

const activeMotorCountElement =
    byId("active-motor-count");

const attentionStatusElement =
    byId("attention-status");

const requestedMotorMaskElement =
    byId("requested-motor-mask");

const appliedMotorMaskElement =
    byId("applied-motor-mask");

const feedbackCommandStatusElement =
    byId("feedback-command-status");

const activeMotorNamesElement =
    byId("active-motor-names");

const attentionSourcesElement =
    byId("attention-sources");

const motorElements = MOTOR_CONFIG.map(
    (motor) => ({
        ...motor,

        node:
            byId(
                `motor-${motor.id.toLowerCase()}`
            ),

        state:
            byId(
                `motor-${motor.id.toLowerCase()}-state`
            )
    })
);


/* Selected Sensor Information */

const sensorIdElement =
    byId("sensor-id");

const sensorNameElement =
    byId("sensor-name");

const sensorMuxChannelElement =
    byId("sensor-mux-channel");

const sensorStatusElement =
    byId("sensor-status");

const sensorFrameElement =
    byId("sensor-frame");

const sensorTimestampElement =
    byId("sensor-timestamp");

const sensorFpsElement =
    byId("sensor-fps");

const historySizeElement =
    byId("history-size");

const historyCapacityElement =
    byId("history-capacity");


/* System Status */

const bridgeStatusElement =
    byId("bridge-status");

const browserStatusElement =
    byId("browser-status");

const tofStatusElement =
    byId("tof-status");

const onlineSensorCountElement =
    byId("online-sensor-count");

const observationNumberElement =
    byId("observation-number");


/* Debug */

const observationJsonElement =
    byId("observation-json");

const dashboardVersionElement =
    byId("dashboard-version");

const backendVersionElement =
    byId("backend-version");

const lastUpdateElement =
    byId("last-update");

const messageCountElement =
    byId("message-count");


/*****************************************************************************/
/* Canvas                                                                    */
/*****************************************************************************/

const distanceCanvas =
    byId("tof-canvas");

const confidenceCanvas =
    byId("confidence-canvas");

const distanceCtx =
    distanceCanvas
        ? distanceCanvas.getContext("2d")
        : null;

const confidenceCtx =
    confidenceCanvas
        ? confidenceCanvas.getContext("2d")
        : null;


/*****************************************************************************/
/* Sector DOM Elements                                                       */
/*****************************************************************************/

const sectorElements = [0, 1, 2].map(
    (index) => ({
        distance:
            byId(
                `sector${index}-distance`
            ),

        confidence:
            byId(
                `sector${index}-confidence`
            ),

        confidenceLevel:
            byId(
                `sector${index}-confidence-level`
            ),

        zone:
            byId(
                `sector${index}-zone`
            ),

        velocity:
            byId(
                `sector${index}-velocity`
            ),

        velocityState:
            byId(
                `sector${index}-velocity-state`
            ),

        persistence:
            byId(
                `sector${index}-persistence`
            )
    })
);


/*****************************************************************************/
/* Generic Utilities                                                         */
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

    element.textContent =
        value;

    element.className =
        className;
}


function formatNumber(
    value,
    digits = 1
)
{
    const number =
        Number(value);

    if (!Number.isFinite(number))
        return "--";

    return number.toFixed(
        digits
    );
}


function escapeHtml(
    value
)
{
    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


function validateObservation(
    observation
)
{
    return Boolean(
        observation
        &&
        Array.isArray(
            observation.sectors
        )
        &&
        observation.sectors.length === 3
    );
}


function normalizeMotorMask(
    value
)
{
    if (
        value === null
        ||
        value === undefined
        ||
        value === ""
    )
    {
        return null;
    }

    const mask =
        Number(value);

    if (!Number.isFinite(mask))
        return null;

    return (
        Math.trunc(mask)
        &
        MOTOR_MASK_ALL
    );
}


function formatMotorMask(
    motorMask
)
{
    const normalized =
        normalizeMotorMask(
            motorMask
        );

    if (normalized === null)
        return "--";

    return `0x${normalized
        .toString(16)
        .toUpperCase()
        .padStart(2, "0")}`;
}


function motorNamesFromMask(
    motorMask
)
{
    const normalized =
        normalizeMotorMask(
            motorMask
        );

    if (normalized === null)
        return [];

    return MOTOR_CONFIG
        .filter(
            (motor) =>
                Boolean(
                    normalized
                    &
                    motor.bit
                )
        )
        .map(
            (motor) =>
                motor.id
        );
}


function formatMotorNames(
    motorNames
)
{
    return motorNames.length > 0
        ? motorNames.join(" + ")
        : "None";
}


/*****************************************************************************/
/* Multi-ToF Helpers                                                         */
/*****************************************************************************/

function orderedSensors(
    message
)
{
    const sensors =
        Array.isArray(
            message?.sensors
        )
            ? message.sensors
            : [];

    return SENSOR_ORDER
        .map(
            (sensorId) =>
                sensors.find(
                    (sensor) =>
                        sensor.sensor_id
                        ===
                        sensorId
                )
        )
        .filter(
            Boolean
        );
}


function findSensor(
    message,
    sensorId
)
{
    if (
        !Array.isArray(
            message?.sensors
        )
    )
    {
        return null;
    }

    return (
        message.sensors.find(
            (sensor) =>
                sensor.sensor_id
                ===
                sensorId
        )
        ??
        null
    );
}


/*****************************************************************************/
/* Confidence Presentation                                                   */
/*****************************************************************************/

function confidenceClassification(
    confidence
)
{
    if (
        !Number.isFinite(
            confidence
        )
        ||
        confidence <= 0
    )
    {
        return {
            label:
                "INVALID",

            className:
                "confidence-invalid"
        };
    }

    if (
        confidence
        >=
        CONFIDENCE_HIGH
    )
    {
        return {
            label:
                "HIGH",

            className:
                "confidence-high"
        };
    }

    if (
        confidence
        >=
        CONFIDENCE_MEDIUM
    )
    {
        return {
            label:
                "MEDIUM",

            className:
                "confidence-medium"
        };
    }

    return {
        label:
            "LOW",

        className:
            "confidence-low"
    };
}


/*****************************************************************************/
/* Sensor Selector                                                           */
/*****************************************************************************/

function setupSensorSelector()
{
    if (!sensorSelectorElement)
        return;

    sensorSelectorElement
        .querySelectorAll(
            ".sensor-select-button"
        )
        .forEach(
            (button) =>
            {
                button.addEventListener(
                    "click",
                    () =>
                    {
                        const requestedSensorId =
                            button.dataset.sensorId;

                        if (!requestedSensorId)
                            return;

                        selectedSensorId =
                            requestedSensorId;

                        updateSensorSelectorState();

                        if (lastMessage)
                        {
                            updateSensorOverview(
                                lastMessage
                            );

                            updateSelectedSensor(
                                lastMessage
                            );
                        }
                    }
                );
            }
        );

    updateSensorSelectorState();
}


function updateSensorSelectorState()
{
    if (!sensorSelectorElement)
        return;

    sensorSelectorElement
        .querySelectorAll(
            ".sensor-select-button"
        )
        .forEach(
            (button) =>
            {
                button.classList.toggle(
                    "active",
                    button.dataset.sensorId
                    ===
                    selectedSensorId
                );
            }
        );
}


/*****************************************************************************/
/* Dashboard Initialization                                                  */
/*****************************************************************************/

function initializeDashboard()
{
    setText(
        applicationVersionElement,
        `v${APP_VERSION}`
    );

    setText(
        dashboardVersionElement,
        APP_VERSION
    );

    setText(
        backendVersionElement,
        "--"
    );

    setText(
        historySizeElement,
        "0"
    );

    setText(
        historyCapacityElement,
        HISTORY_CAPACITY
    );

    setText(
        messageCountElement,
        "0"
    );

    setText(
        onlineSensorCountElement,
        "0"
    );

    setText(
        observationNumberElement,
        "0"
    );

    setText(
        observationJsonElement,
        "Waiting for observations..."
    );

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

    setMotorFeedbackUnavailable(
        "WAITING FOR FEEDBACK",
        "motor-state-waiting"
    );

    setupSensorSelector();

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
        "6 x VL53L5CX | 4x4 | Multi-ToF Observation Engine"
    );

    console.log(
        "=========================================="
    );
}


/*****************************************************************************/
/* Main Dashboard Update                                                     */
/*****************************************************************************/

function updateDashboard(
    message
)
{
    updateSensorOverview(
        message
    );

    updateSelectedSensor(
        message
    );

    updateMotorFeedback(
        message
    );

    updateSystemStatus(
        message
    );

    updateObservationJSON(
        message
    );
}


/*****************************************************************************/
/* Haptic Motor Feedback                                                     */
/*****************************************************************************/

function setMotorFeedbackHeadline(
    value,
    className
)
{
    setStatus(
        motorFeedbackStateElement,
        value,
        `motor-feedback-state ${className}`
    );
}


function setMotorFeedbackUnavailable(
    headline,
    headlineClass
)
{
    setMotorFeedbackHeadline(
        headline,
        headlineClass
    );

    if (motorMapElement)
    {
        motorMapElement.classList.remove(
            "has-active"
        );

        motorMapElement.classList.toggle(
            "feedback-fault",
            headlineClass === "motor-state-fault"
        );
    }

    motorElements.forEach(
        (motor) =>
        {
            if (motor.node)
            {
                motor.node.classList.remove(
                    "active"
                );

                motor.node.classList.add(
                    "unavailable"
                );

                motor.node.setAttribute(
                    "aria-label",
                    `${motor.id} ${motor.direction}: feedback unavailable`
                );
            }

            setText(
                motor.state,
                "--"
            );
        }
    );

    setText(
        activeMotorCountElement,
        "-- / 4"
    );

    setText(
        attentionStatusElement,
        "WAITING"
    );

    if (attentionStatusElement)
    {
        attentionStatusElement.className =
            "status-unknown";
    }

    setText(
        requestedMotorMaskElement,
        "--"
    );

    setText(
        appliedMotorMaskElement,
        "--"
    );

    setText(
        feedbackCommandStatusElement,
        "UNAVAILABLE"
    );

    if (feedbackCommandStatusElement)
    {
        feedbackCommandStatusElement.className =
            "status-unknown";
    }

    setText(
        activeMotorNamesElement,
        "Unknown"
    );

    renderAttentionSources(
        []
    );
}


function renderAttentionSources(
    sources
)
{
    if (!attentionSourcesElement)
        return;

    attentionSourcesElement.innerHTML =
        "";

    if (
        !Array.isArray(sources)
        ||
        sources.length === 0
    )
    {
        attentionSourcesElement.className =
            "attention-sources attention-sources-empty";

        attentionSourcesElement.textContent =
            "No sector currently meets the activation rule.";

        return;
    }

    attentionSourcesElement.className =
        "attention-sources";

    sources.forEach(
        (source) =>
        {
            const sourceMask =
                normalizeMotorMask(
                    source?.motor_mask
                );

            const sourceMotors =
                motorNamesFromMask(
                    sourceMask
                );

            const chip =
                document.createElement(
                    "div"
                );

            chip.className =
                "attention-source-chip";

            const title =
                document.createElement(
                    "strong"
                );

            title.textContent =
                `${source?.sensor_id ?? "--"} / ${source?.sector_name ?? "--"}`;

            const detail =
                document.createElement(
                    "span"
                );

            detail.textContent =
                `${source?.sensor_position ?? "--"} · P${source?.motion_persistence ?? 0}`;

            const motors =
                document.createElement(
                    "span"
                );

            motors.className =
                "attention-source-motors";

            motors.textContent =
                `→ ${formatMotorNames(sourceMotors)}`;

            chip.append(
                title,
                detail,
                motors
            );

            attentionSourcesElement.appendChild(
                chip
            );
        }
    );
}


function updateMotorFeedback(
    message
)
{
    const attention =
        message?.attention
        ??
        null;

    const feedback =
        message?.feedback
        ??
        null;

    const requestedMask =
        normalizeMotorMask(
            attention?.motor_mask
            ??
            feedback?.requested_motor_mask
        );

    const appliedMask =
        normalizeMotorMask(
            feedback?.applied_motor_mask
        );

    const feedbackAvailable =
        Boolean(feedback)
        &&
        appliedMask !== null;

    const commandOk =
        feedbackAvailable
        &&
        feedback.command_ok === true;

    if (!attention && !feedbackAvailable)
    {
        setMotorFeedbackUnavailable(
            "MCU FEEDBACK UNAVAILABLE",
            "motor-state-waiting"
        );

        return;
    }

    setText(
        requestedMotorMaskElement,
        formatMotorMask(
            requestedMask
        )
    );

    setText(
        appliedMotorMaskElement,
        feedbackAvailable
            ? (
                commandOk
                    ? formatMotorMask(appliedMask)
                    : `${formatMotorMask(appliedMask)} (last confirmed)`
            )
            : "--"
    );

    const requestedMotors =
        motorNamesFromMask(
            requestedMask
        );

    if (attentionStatusElement)
    {
        if (!attention)
        {
            setStatus(
                attentionStatusElement,
                "UNAVAILABLE",
                "status-unknown"
            );
        }
        else if (requestedMotors.length > 0)
        {
            setStatus(
                attentionStatusElement,
                "ATTENTION ACTIVE",
                "status-danger"
            );
        }
        else
        {
            setStatus(
                attentionStatusElement,
                "IDLE",
                "status-online"
            );
        }
    }

    if (!feedbackAvailable)
    {
        setMotorFeedbackUnavailable(
            "MCU FEEDBACK UNAVAILABLE",
            "motor-state-waiting"
        );

        setText(
            requestedMotorMaskElement,
            formatMotorMask(
                requestedMask
            )
        );

        if (attentionStatusElement && attention)
        {
            setStatus(
                attentionStatusElement,
                requestedMotors.length > 0
                    ? "ATTENTION ACTIVE"
                    : "IDLE",
                requestedMotors.length > 0
                    ? "status-danger"
                    : "status-online"
            );
        }

        renderAttentionSources(
            attention?.active_sources
            ??
            []
        );

        return;
    }

    if (!commandOk)
    {
        setStatus(
            feedbackCommandStatusElement,
            "COMMAND ERROR",
            "status-danger"
        );

        setMotorFeedbackHeadline(
            "FEEDBACK COMMAND ERROR",
            "motor-state-fault"
        );
    }
    else
    {
        setStatus(
            feedbackCommandStatusElement,
            "ACKNOWLEDGED",
            "status-online"
        );
    }

    /*
     * Only a successful MCU acknowledgement is treated as confirmation
     * that the applied mask represents the current motor state.
     */
    const confirmedMask =
        commandOk
            ? appliedMask
            : 0;

    const activeMotors =
        motorNamesFromMask(
            confirmedMask
        );

    motorElements.forEach(
        (motor) =>
        {
            const active =
                Boolean(
                    confirmedMask
                    &
                    motor.bit
                );

            if (motor.node)
            {
                motor.node.classList.toggle(
                    "active",
                    active
                );

                motor.node.classList.toggle(
                    "unavailable",
                    !commandOk
                );

                motor.node.setAttribute(
                    "aria-label",
                    `${motor.id} ${motor.direction}: ${
                        active
                            ? "vibrating"
                            : commandOk
                                ? "off"
                                : "feedback unavailable"
                    }`
                );
            }

            setText(
                motor.state,
                active
                    ? "VIBRATING"
                    : commandOk
                        ? "OFF"
                        : "--"
            );
        }
    );

    if (motorMapElement)
    {
        motorMapElement.classList.toggle(
            "has-active",
            activeMotors.length > 0
        );

        motorMapElement.classList.toggle(
            "feedback-fault",
            !commandOk
        );

        motorMapElement.setAttribute(
            "aria-label",
            commandOk
                ? `Top-view motor arrangement. Vibrating motors: ${formatMotorNames(activeMotors)}.`
                : "Top-view motor arrangement. Current MCU motor state is unavailable."
        );
    }

    setText(
        activeMotorCountElement,
        commandOk
            ? `${activeMotors.length} / 4`
            : "-- / 4"
    );

    setText(
        activeMotorNamesElement,
        commandOk
            ? formatMotorNames(activeMotors)
            : "Unknown"
    );

    if (commandOk)
    {
        if (activeMotors.length > 0)
        {
            setMotorFeedbackHeadline(
                `VIBRATING: ${formatMotorNames(activeMotors)}`,
                "motor-state-active"
            );
        }
        else
        {
            setMotorFeedbackHeadline(
                "ALL MOTORS OFF",
                "motor-state-idle"
            );
        }
    }

    renderAttentionSources(
        attention?.active_sources
        ??
        []
    );
}


/*****************************************************************************/
/* Six-ToF Overview                                                          */
/*****************************************************************************/

function updateSensorOverview(
    message
)
{
    if (!sensorOverviewGridElement)
        return;

    const sensors =
        orderedSensors(
            message
        );

    sensorOverviewGridElement.innerHTML =
        "";

    if (sensors.length === 0)
    {
        sensorOverviewGridElement.innerHTML =
            '<div class="empty-state">'
            +
            'Waiting for six-sensor observations...'
            +
            '</div>';

        return;
    }

    sensors.forEach(
        (sensor) =>
        {
            const observation =
                sensor.observation
                ??
                {};

            const sectors =
                Array.isArray(
                    observation.sectors
                )
                    ? observation.sectors
                    : [];

            const online =
                observation.status
                ===
                "ONLINE";

            const card =
                document.createElement(
                    "button"
                );

            card.type =
                "button";

            card.className =
                "sensor-overview-item";

            if (
                sensor.sensor_id
                ===
                selectedSensorId
            )
            {
                card.classList.add(
                    "selected"
                );
            }

            const sectorHtml =
                [0, 1, 2]
                    .map(
                        (sectorIndex) =>
                        {
                            const sector =
                                sectors[
                                    sectorIndex
                                ]
                                ??
                                {};

                            const distance =
                                Number(
                                    sector.distance_mm
                                    ??
                                    0
                                );

                            const value =
                                distance > 0
                                    ?
                                    `${Math.round(distance)} mm`
                                    :
                                    "--";

                            return `
                                <div class="overview-sector">
                                    <span>S${sectorIndex}</span>
                                    <strong>${value}</strong>
                                </div>
                            `;
                        }
                    )
                    .join(
                        ""
                    );

            card.innerHTML = `
                <div class="overview-header">

                    <div>
                        <strong>
                            ${escapeHtml(
                                sensor.sensor_id
                                ??
                                "--"
                            )}
                        </strong>

                        <span>
                            ${escapeHtml(
                                sensor.position
                                ??
                                SENSOR_LABELS[
                                    sensor.sensor_id
                                ]
                                ??
                                "--"
                            )}
                        </span>
                    </div>

                    <span
                        class="${
                            online
                                ?
                                "status-online"
                                :
                                "status-offline"
                        }">

                        ${
                            online
                                ?
                                "ONLINE"
                                :
                                "OFFLINE"
                        }

                    </span>

                </div>

                <div class="overview-meta">

                    <span>
                        CH${escapeHtml(
                            sensor.mux_channel
                            ??
                            "--"
                        )}
                    </span>

                    <span>
                        ${formatNumber(
                            sensor.fps,
                            1
                        )} Hz
                    </span>

                    <span>
                        F${escapeHtml(
                            sensor.frame_number
                            ??
                            "--"
                        )}
                    </span>

                </div>

                <div class="overview-sector-grid">
                    ${sectorHtml}
                </div>
            `;

            card.addEventListener(
                "click",
                () =>
                {
                    selectedSensorId =
                        sensor.sensor_id;

                    updateSensorSelectorState();

                    updateSensorOverview(
                        message
                    );

                    updateSelectedSensor(
                        message
                    );
                }
            );

            sensorOverviewGridElement.appendChild(
                card
            );
        }
    );
}


/*****************************************************************************/
/* Selected Sensor                                                           */
/*****************************************************************************/

function updateSelectedSensor(
    message
)
{
    let sensor =
        findSensor(
            message,
            selectedSensorId
        );

    /*
     * If selected sensor is unavailable,
     * use the first available sensor.
     */
    if (!sensor)
    {
        sensor =
            orderedSensors(
                message
            )[0]
            ??
            null;

        if (!sensor)
            return;

        selectedSensorId =
            sensor.sensor_id;

        updateSensorSelectorState();
    }

    const observation =
        sensor.observation
        ??
        null;

    if (
        !validateObservation(
            observation
        )
    )
    {
        return;
    }

    updateSensorInformation(
        sensor,
        observation
    );

    updateSectorCards(
        observation
    );

    updateHeatmaps(
        sensor
    );
}


/*****************************************************************************/
/* Selected Sensor Information                                               */
/*****************************************************************************/

function updateSensorInformation(
    sensor,
    observation
)
{
    setText(
        sensorIdElement,
        sensor.sensor_id
    );

    setText(
        sensorNameElement,
        sensor.position
        ??
        sensor.sensor_name
    );

    setText(
        sensorMuxChannelElement,
        sensor.mux_channel
    );

    setText(
        sensorFrameElement,
        sensor.frame_number
        ??
        observation.frame_number
    );

    setText(
        sensorTimestampElement,
        sensor.timestamp
        ??
        observation.timestamp
    );

    setText(
        sensorFpsElement,
        formatNumber(
            sensor.fps
            ??
            observation.fps,
            2
        )
    );

    setText(
        historySizeElement,
        observation.history_size
        ??
        0
    );

    if (
        observation.status
        ===
        "ONLINE"
    )
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
            observation.status
            ??
            "OFFLINE",
            "status-offline"
        );
    }
}


/*****************************************************************************/
/* Sector Cards                                                              */
/*****************************************************************************/

function updateSectorCards(
    observation
)
{
    if (
        !validateObservation(
            observation
        )
    )
    {
        return;
    }

    observation.sectors.forEach(
        (sector, index) =>
        {
            updateSector(
                sector,
                sectorElements[
                    index
                ]
            );
        }
    );
}


function updateSector(
    sector,
    elements
)
{
    if (!elements)
        return;

    const distance =
        Number(
            sector.distance_mm
            ??
            0
        );

    const confidence =
        Number(
            sector.confidence
            ??
            0
        );

    const velocity =
        Number(
            sector.velocity_mmps
            ??
            0
        );

    const velocityValid =
        Boolean(
            sector.velocity_valid
            ??
            false
        );

    const persistence =
        Number(
            sector.motion_persistence
            ??
            0
        );

    setText(
        elements.distance,
        distance > 0
            ?
            Math.round(
                distance
            )
            :
            "--"
    );

    setText(
        elements.confidence,
        Number.isFinite(
            confidence
        )
            ?
            confidence.toFixed(
                1
            )
            :
            "0.0"
    );

    setText(
        elements.zone,
        Number(
            sector.zone_id
        )
        >=
        0
            ?
            sector.zone_id
            :
            "--"
    );

    setText(
        elements.velocity,
        velocityValid
        &&
        Number.isFinite(
            velocity
        )
            ?
            velocity.toFixed(
                1
            )
            :
            "--"
    );

    setText(
        elements.persistence,
        Number.isFinite(
            persistence
        )
            ?
            Math.max(
                0,
                Math.min(
                    MOTION_PERSISTENCE_MAX,
                    Math.round(
                        persistence
                    )
                )
            )
            :
            "0"
    );

    const confidenceInfo =
        confidenceClassification(
            confidence
        );

    if (
        elements.confidenceLevel
    )
    {
        elements.confidenceLevel.textContent =
            confidenceInfo.label;

        elements.confidenceLevel.className =
            `confidence-badge ${confidenceInfo.className}`;
    }

    const velocityState =
        sector.velocity_state
        ??
        "Unknown";

    if (
        elements.velocityState
    )
    {
        elements.velocityState.textContent =
            velocityState;

        elements.velocityState.className =
            "state-value";

        switch (
            velocityState
        )
        {
            case "Approaching":

                elements.velocityState.classList.add(
                    "status-danger"
                );

                break;

            case "Receding":

                elements.velocityState.classList.add(
                    "status-online"
                );

                break;

            case "Stationary":

                elements.velocityState.classList.add(
                    "status-warning"
                );

                break;

            default:

                elements.velocityState.classList.add(
                    "status-unknown"
                );

                break;
        }
    }
}


/*****************************************************************************/
/* System Status                                                             */
/*****************************************************************************/

function updateSystemStatus(
    message
)
{
    setStatus(
        browserStatusElement,
        connected
            ?
            "CONNECTED"
            :
            "DISCONNECTED",
        connected
            ?
            "status-online"
            :
            "status-offline"
    );

    /*
     * Receiving a valid tof_frame means the
     * Browser -> Python -> RouterBridge path is operational.
     */
    setStatus(
        bridgeStatusElement,
        "CONNECTED",
        "status-online"
    );

    const sensors =
        orderedSensors(
            message
        );

    const onlineCount =
        sensors.filter(
            (sensor) =>
                sensor.observation
                &&
                sensor.observation.status
                ===
                "ONLINE"
        ).length;

    setText(
        onlineSensorCountElement,
        onlineCount
    );

    setText(
        observationNumberElement,
        message.observation_number
        ??
        0
    );

    if (
        onlineCount
        ===
        SENSOR_COUNT
    )
    {
        setStatus(
            tofStatusElement,
            "ALL ONLINE",
            "status-online"
        );
    }
    else if (
        onlineCount > 0
    )
    {
        setStatus(
            tofStatusElement,
            `${onlineCount}/${SENSOR_COUNT} ONLINE`,
            "status-warning"
        );
    }
    else
    {
        setStatus(
            tofStatusElement,
            "OFFLINE",
            "status-offline"
        );
    }
}


/*****************************************************************************/
/* Heatmaps                                                                  */
/*****************************************************************************/

function updateHeatmaps(
    sensor
)
{
    if (
        sensor.image
    )
    {
        drawDistanceHeatmap(
            sensor.image
        );
    }

    if (
        sensor.confidence_image
    )
    {
        drawConfidenceHeatmap(
            sensor.confidence_image
        );
    }
}


function drawDistanceHeatmap(
    image
)
{
    drawHeatmap(
        distanceCtx,
        distanceCanvas,
        image,
        distanceToColor,
        (value) =>
            value > 0
                ?
                `${Math.round(value)}`
                :
                ""
    );
}


function drawConfidenceHeatmap(
    image
)
{
    drawHeatmap(
        confidenceCtx,
        confidenceCanvas,
        image,
        confidenceToColor,
        (value) =>
            Number.isFinite(
                Number(value)
            )
                ?
                `${Math.round(
                    Number(value)
                )}`
                :
                ""
    );
}


/*****************************************************************************/
/* Generic 4x4 Heatmap                                                       */
/*****************************************************************************/

function drawHeatmap(
    context,
    canvas,
    image,
    colorFunction,
    labelFunction
)
{
    if (
        !context
        ||
        !canvas
        ||
        !Array.isArray(
            image
        )
        ||
        image.length === 0
    )
    {
        return;
    }

    const rows =
        image.length;

    const cols =
        Array.isArray(
            image[0]
        )
            ?
            image[0].length
            :
            0;

    if (
        rows !== HEATMAP_ROWS
        ||
        cols !== HEATMAP_COLS
    )
    {
        console.warn(
            "Unexpected heatmap size:",
            rows,
            "x",
            cols,
            "| expected 4 x 4"
        );
    }

    if (
        rows === 0
        ||
        cols === 0
    )
    {
        return;
    }

    const cellWidth =
        canvas.width
        /
        cols;

    const cellHeight =
        canvas.height
        /
        rows;

    context.clearRect(
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
                    image[
                        row
                    ][
                        col
                    ]
                );

            const background =
                colorFunction(
                    value
                );

            context.fillStyle =
                background;

            context.fillRect(
                col
                *
                cellWidth,

                row
                *
                cellHeight,

                cellWidth,

                cellHeight
            );

            context.strokeStyle =
                "#475569";

            context.lineWidth =
                1;

            context.strokeRect(
                col
                *
                cellWidth,

                row
                *
                cellHeight,

                cellWidth,

                cellHeight
            );

            const label =
                labelFunction(
                    value
                );

            if (label)
            {
                context.fillStyle =
                    "#111827";

                context.font =
                    "bold 20px Arial";

                context.textAlign =
                    "center";

                context.textBaseline =
                    "middle";

                context.fillText(
                    label,

                    col
                    *
                    cellWidth
                    +
                    cellWidth / 2,

                    row
                    *
                    cellHeight
                    +
                    cellHeight / 2
                );
            }
        }
    }

    drawSectorBoundaries(
        context,
        canvas,
        cellWidth
    );
}


/*****************************************************************************/
/* Sector Boundaries                                                         */
/*****************************************************************************/

/*
 * Final 4x4 local-sector definition:
 *
 *     col 0 | col 1   col 2 | col 3
 *       S0  |       S1      |   S2
 *
 * S0 = left-most column
 * S1 = middle two columns
 * S2 = right-most column
 *
 * The red boundaries occur after columns 0 and 2.
 */

function drawSectorBoundaries(
    context,
    canvas,
    cellWidth
)
{
    context.save();

    context.strokeStyle =
        "#dc2626";

    context.lineWidth =
        4;

    /*
     * S0 | S1 boundary
     */
    context.beginPath();

    context.moveTo(
        cellWidth,
        0
    );

    context.lineTo(
        cellWidth,
        canvas.height
    );

    context.stroke();

    /*
     * S1 | S2 boundary
     */
    context.beginPath();

    context.moveTo(
        cellWidth
        *
        3,
        0
    );

    context.lineTo(
        cellWidth
        *
        3,
        canvas.height
    );

    context.stroke();

    context.restore();
}


/*****************************************************************************/
/* Distance Heatmap Colour                                                   */
/*****************************************************************************/

function distanceToColor(
    distance
)
{
    if (
        !Number.isFinite(
            distance
        )
        ||
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
     * 0 mm -> red
     * 3000 mm -> green
     */
    const hue =
        normalized
        *
        120;

    return `hsl(${hue}, 100%, 50%)`;
}


/*****************************************************************************/
/* Confidence Heatmap Colour                                                 */
/*****************************************************************************/

function confidenceToColor(
    confidence
)
{
    if (
        !Number.isFinite(
            confidence
        )
        ||
        confidence <= 0
    )
    {
        return "#f8fafc";
    }

    const normalized =
        Math.max(
            0,
            Math.min(
                100,
                confidence
            )
        );

    const hue =
        normalized
        *
        1.2;

    return `hsl(${hue}, 85%, 48%)`;
}


/*****************************************************************************/
/* JSON Viewer                                                               */
/*****************************************************************************/

function updateObservationJSON(
    message
)
{
    if (!observationJsonElement)
        return;

    observationJsonElement.textContent =
        JSON.stringify(
            {
                observation_number:
                    message.observation_number,

                timestamp:
                    message.timestamp,

                configuration:
                    message.configuration,

                sensors:
                    message.sensors,

                attention:
                    message.attention,

                feedback:
                    message.feedback
            },
            null,
            4
        );
}


/*****************************************************************************/
/* Socket.IO                                                                 */
/*****************************************************************************/

socket =
    io();


socket.on(
    "connect",
    () =>
    {
        connected =
            true;

        console.log(
            "Connected to backend."
        );

        setStatus(
            browserStatusElement,
            "CONNECTED",
            "status-online"
        );

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
        connected =
            false;

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

        setStatus(
            tofStatusElement,
            "OFFLINE",
            "status-offline"
        );

        setMotorFeedbackUnavailable(
            "CONNECTION LOST",
            "motor-state-fault"
        );
    }
);


/*****************************************************************************/
/* ToF Frame Message                                                         */
/*****************************************************************************/

socket.on(
    "tof_frame",
    (message) =>
    {
        if (!message)
            return;

        /*
         * SixthSense v3.0 primary payload:
         *
         * message.sensors[0] = T1 / Front-right
         * message.sensors[1] = T2 / Front
         * message.sensors[2] = T3 / Front-left
         * message.sensors[3] = T4 / Rear-left
         * message.sensors[4] = T5 / Rear
         * message.sensors[5] = T6 / Rear-right
         */
        if (
            !Array.isArray(
                message.sensors
            )
            ||
            message.sensors.length === 0
        )
        {
            console.warn(
                "tof_frame does not contain "
                +
                "a multi-ToF sensors array."
            );

            return;
        }

        lastMessage =
            message;

        messageCount++;

        setText(
            messageCountElement,
            messageCount
        );

        setText(
            lastUpdateElement,
            new Date().toLocaleTimeString()
        );

        if (
            message.app_version
        )
        {
            setText(
                backendVersionElement,
                message.app_version
            );
        }

        updateDashboard(
            message
        );
    }
);


/*****************************************************************************/
/* Window Resize                                                             */
/*****************************************************************************/

window.addEventListener(
    "resize",
    () =>
    {
        if (
            lastMessage
        )
        {
            updateSelectedSensor(
                lastMessage
            );
        }
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
/* SixthSense Dashboard v3.0.0                                               */
/*****************************************************************************/