// robot_control.js

let controlSocket = null;
let controlReady = false;

export async function startRobotControlChannel(robotId) {
    return new Promise((resolve, reject) => {
        const wsUrl = `ws://${window.location.host}/ws/control/${robotId}/`;

        console.log("[RobotControl] Connecting to:", wsUrl);

        controlSocket = new WebSocket(wsUrl);

        controlSocket.onopen = () => {
            console.log("[RobotControl] Control channel connected");
            controlReady = true;
            resolve();
        };

        controlSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("[RobotControl] Received:", data);

            if (data.type === "control_ack") {
                console.log("[RobotControl] ACK:", data.message);
            }

            if (data.type === "error") {
                console.error("[RobotControl] Error:", data.message);
            }
        };

        controlSocket.onerror = (err) => {
            console.error("[RobotControl] WebSocket error:", err);
            controlReady = false;
            reject(err);
        };

        controlSocket.onclose = () => {
            console.warn("[RobotControl] Control WebSocket closed");
            controlReady = false;
        };
    });
}


// ==============================
//  Command Functions (Exports)
// ==============================

export function sendControlCommand(type, payload = {}) {
    if (!controlReady || !controlSocket || controlSocket.readyState !== WebSocket.OPEN) {
        console.warn("[RobotControl] Control channel not ready");
        return;
    }

    const msg = {
        type: type,
        payload: payload
    };

    console.log("[RobotControl] Sending:", msg);
    controlSocket.send(JSON.stringify(msg));
}


// 이동 (예: 방향: forward / backward / left / right)
export function move(direction, speed = 1.0) {
    sendControlCommand("move", {
        direction: direction,
        speed: speed
    });
}


// 정지
export function stop() {
    sendControlCommand("stop");
}


// 비상 정지
export function emergencyStop() {
    sendControlCommand("e_stop");
}


// 속도 설정
export function setSpeed(speed) {
    sendControlCommand("set_speed", { speed });
}


// 도킹 명령
export function dock() {
    sendControlCommand("dock");
}


// 경로 따라가기
export function pathFollow(pathId) {
    sendControlCommand("path_follow", { path_id: pathId });
}


// 연결 종료
export function closeControlChannel() {
    if (controlSocket) {
        controlSocket.close();
        controlSocket = null;
        controlReady = false;
        console.log("[RobotControl] Control channel closed");
    }
}
