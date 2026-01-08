// robot_control.js

let controlSocket = null;
let controlReady = false;
let currentRobotId = null;

let reconnectTimer = null;
const RECONNECT_INTERVAL = 1500; // 1.5 sec


export async function startRobotControlChannel(robotId) {
    return new Promise((resolve, reject) => {
        currentRobotId = robotId;

        const protocol = location.protocol === "https:" ? "wss" : "ws";
        const wsUrl = `${protocol}://${window.location.host}/ws/control/${robotId}/`;

        console.log("[RobotControl] Connecting:", wsUrl);
        controlSocket = new WebSocket(wsUrl);

        controlSocket.onopen = () => {
            console.log("[RobotControl] Connected");
            controlReady = true;

            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }

            resolve();
        };

        controlSocket.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            handleControlMessage(msg);
        };

        controlSocket.onerror = (err) => {
            console.error("[RobotControl] WebSocket error:", err);
            controlReady = false;
            reject(err);
        };

        controlSocket.onclose = () => {
            console.warn("[RobotControl] WebSocket closed");
            controlReady = false;
            scheduleReconnect();
        };
    });
}

export function closeControlChannel() {
    console.log("[RobotControl] Closing control channel");

    if (controlSocket) {
        controlSocket.close();
        controlSocket = null;
    }

    controlReady = false;
    currentRobotId = null;
}

function send(type, payload = {}) {
    if (!controlReady || !controlSocket || controlSocket.readyState !== WebSocket.OPEN) {
        console.warn("[RobotControl] Channel not ready");
        return;
    }

    if (!currentRobotId) {
        console.error("[RobotControl] robot_id not set");
        return;
    }

    const msg = {
        type: type,
        robot_id: currentRobotId,
        payload: payload
    };

    console.log("[RobotControl] Sending:", msg);
    controlSocket.send(JSON.stringify(msg));
}

export function move(direction, speed = 1.0) {
    send("move", { direction, speed });
}

export function stop() {
    send("stop");
}

export function emergencyStop() {
    send("e_stop");
}

export function setSpeed(speed) {
    send("set_speed", { speed });
}

export function dock() {
    send("dock");
}

export function pathFollow(pathId) {
    send("path_follow", { path_id: pathId });
}

function handleControlMessage(msg) {
    switch (msg.type) {
        case "heartbeat_check":
            // Keepalive; no client action required.
            break;
        case "control_ack":
            console.log("[RobotControl] ACK:", msg.message);
            break;

        case "control_error":
            console.error("[RobotControl] Error:", msg.message);
            break;

        case "robot_status":
            console.log("[RobotControl] Status:", msg.status);
            break;

        default:
            console.warn("[RobotControl] Unknown message:", msg);
    }
}

function scheduleReconnect() {
    if (reconnectTimer) return;

    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;

        if (currentRobotId) {
            console.log("[RobotControl] Reconnecting…");
            startRobotControlChannel(currentRobotId).catch(() => {});
        }
    }, RECONNECT_INTERVAL);
}
