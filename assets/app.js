// SPDX-License-Identifier: MPL-2.0

///////////////////////////////////////////////////////////////////////////////
// SixthSense Dashboard
// Part 1
//
// Socket.IO
// State Management
// UI Updates
// Helper Functions
///////////////////////////////////////////////////////////////////////////////

"use strict";

///////////////////////////////////////////////////////////////////////////////
// Socket.IO
///////////////////////////////////////////////////////////////////////////////

const socket = io(
    window.location.origin,
    {
        transports: ["websocket", "polling"]
    }
);

console.log("Socket.IO client created");

///////////////////////////////////////////////////////////////////////////////
// HTML Elements
///////////////////////////////////////////////////////////////////////////////

const connectionStatus =
    document.getElementById("connectionStatus");

const frameNumber =
    document.getElementById("frameNumber");

const fpsValue =
    document.getElementById("fpsValue");

const nearestValue =
    document.getElementById("nearestValue");

const leftDistance =
    document.getElementById("leftDistance");

const centerDistance =
    document.getElementById("centerDistance");

const rightDistance =
    document.getElementById("rightDistance");

const canvas =
    document.getElementById("heatmapCanvas");

const ctx =
    canvas.getContext("2d");

///////////////////////////////////////////////////////////////////////////////
// Constants
///////////////////////////////////////////////////////////////////////////////

const GRID_SIZE = 8;

const CELL_SIZE = canvas.width / GRID_SIZE;

const MAX_DISTANCE = 3000;

///////////////////////////////////////////////////////////////////////////////
// Global State
///////////////////////////////////////////////////////////////////////////////

let currentFrame = 0;

let currentImage = [];

let currentFPS = 0;

let connected = false;

///////////////////////////////////////////////////////////////////////////////
// Initialise Empty Image
///////////////////////////////////////////////////////////////////////////////

for(let r=0;r<GRID_SIZE;r++)
{
    currentImage.push([]);

    for(let c=0;c<GRID_SIZE;c++)
    {
        currentImage[r].push(0);
    }
}

///////////////////////////////////////////////////////////////////////////////
// Distance -> Colour
///////////////////////////////////////////////////////////////////////////////

function distanceToColor(distance)
{
    if(distance === 0)
        return "#000000";

    const t = Math.min(distance,3000)/3000;

    const r = Math.round(255*(1-t));

    const g = Math.round(255*(1-Math.abs(t-0.5)*2));

    const b = Math.round(255*t);

    return `rgb(${r},${g},${b})`;
}

///////////////////////////////////////////////////////////////////////////////
// Connection Status
///////////////////////////////////////////////////////////////////////////////

function setConnected(state)
{
    connected = state;

    if(state)
    {
        connectionStatus.innerHTML = "Connected";

        connectionStatus.className = "connected";
    }
    else
    {
        connectionStatus.innerHTML = "Disconnected";

        connectionStatus.className = "disconnected";
    }
}

///////////////////////////////////////////////////////////////////////////////
// Update Statistics
///////////////////////////////////////////////////////////////////////////////

function updateStatistics(message)
{
    frameNumber.innerHTML =
        message.frame ?? "--";

    fpsValue.innerHTML =
        (message.fps ?? 0).toString();

    nearestValue.innerHTML =
        message.nearest !== undefined
            ? message.nearest + " mm"
            : "--";

    leftDistance.innerHTML =
        message.left !== undefined
            ? message.left + " mm"
            : "--";

    centerDistance.innerHTML =
        message.center !== undefined
            ? message.center + " mm"
            : "--";

    rightDistance.innerHTML =
        message.right !== undefined
            ? message.right + " mm"
            : "--";
}

///////////////////////////////////////////////////////////////////////////////
// Receive Frame
///////////////////////////////////////////////////////////////////////////////

function processFrame(message)
{
    console.log("FRAME RECEIVED");

    console.log(message);

    console.log("Rows =", message.image.length);
    console.log("Cols =", message.image[0].length);
    console.log("Pixel(0,0) =", message.image[0][0]);
    console.log("First Row =", message.image[0]);

    currentFrame = message.frame;
    currentImage = message.image;

  updateStatistics(message);

    drawHeatmap();
}

///////////////////////////////////////////////////////////////////////////////
// Socket Initialisation
///////////////////////////////////////////////////////////////////////////////

function initialiseSocket()
{
    console.log("Initialising Socket.IO...");

    socket.on("connect", () =>
    {
        console.log("Socket connected");
        console.log("Socket ID:", socket.id);

        setConnected(true);

        socket.emit("get_initial_state", {});
    });

    socket.on("disconnect", () =>
    {
        console.log("Socket disconnected");

        setConnected(false);
    });

    socket.on("connect_error", (err) =>
    {
        console.error("Socket connect error");

        console.error(err);
    });

    socket.on("tof_frame", (message) =>
    {
        console.log("Received tof_frame");

        console.log(message);

        processFrame(message);
    });
}

///////////////////////////////////////////////////////////////////////////////
// Page Loaded
///////////////////////////////////////////////////////////////////////////////

document.addEventListener(
    "DOMContentLoaded",
    () =>
    {
        initialiseSocket();
    }
);

///////////////////////////////////////////////////////////////////////////////
// SixthSense Dashboard
// Part 2
//
// Canvas Rendering
///////////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////////
// Draw Grid
///////////////////////////////////////////////////////////////////////////////

function drawGrid()
{
    ctx.strokeStyle = "#404040";
    ctx.lineWidth = 1;

    for(let r = 0; r <= GRID_SIZE; r++)
    {
        ctx.beginPath();

        ctx.moveTo(
            0,
            r * CELL_SIZE
        );

        ctx.lineTo(
            canvas.width,
            r * CELL_SIZE
        );

        ctx.stroke();
    }

    for(let c = 0; c <= GRID_SIZE; c++)
    {
        ctx.beginPath();

        ctx.moveTo(
            c * CELL_SIZE,
            0
        );

        ctx.lineTo(
            c * CELL_SIZE,
            canvas.height
        );

        ctx.stroke();
    }
}

///////////////////////////////////////////////////////////////////////////////
// Draw One Cell
///////////////////////////////////////////////////////////////////////////////

function drawCell(row, col, distance)
{
    const x = col * CELL_SIZE;

    const y = row * CELL_SIZE;

    ctx.fillStyle = distanceToColor(distance);

    ctx.fillRect(
        x,
        y,
        CELL_SIZE,
        CELL_SIZE
    );

    ctx.strokeStyle = "#303030";

    ctx.strokeRect(
        x,
        y,
        CELL_SIZE,
        CELL_SIZE
    );

    ////////////////////////////////////////////////////////////
    // Distance Text
    ////////////////////////////////////////////////////////////

    ctx.fillStyle = "white";

    ctx.font = "16px Arial";

    ctx.textAlign = "center";

    ctx.textBaseline = "middle";

    if(distance == 0)
    {
        ctx.fillText(
            "--",
            x + CELL_SIZE / 2,
            y + CELL_SIZE / 2
        );
    }
    else
    {
        ctx.fillText(
            distance.toString(),
            x + CELL_SIZE / 2,
            y + CELL_SIZE / 2
        );
    }
}

///////////////////////////////////////////////////////////////////////////////
// Draw Entire Heatmap
///////////////////////////////////////////////////////////////////////////////

function drawHeatmap()
{
 
    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    ctx.fillStyle = "black";

    ctx.fillRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

  if(currentImage.length !== 8)
{
    console.log("Image size incorrect");

    return;
}

    for(let r=0;r<8;r++)
    {
      console.log(currentImage);
console.log(typeof currentImage[0][0]);
        for(let c=0;c<8;c++)
        {
            drawCell(
                r,
                c,
                currentImage[r][c]
            );
        }
    }

    drawGrid();
}

///////////////////////////////////////////////////////////////////////////////
// Resize
///////////////////////////////////////////////////////////////////////////////

window.addEventListener(
    "resize",
    () =>
    {
        drawHeatmap();
    }
);

///////////////////////////////////////////////////////////////////////////////
// Initial Draw
///////////////////////////////////////////////////////////////////////////////

drawHeatmap();