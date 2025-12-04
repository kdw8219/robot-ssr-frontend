let pc = null;
let ws = null;
let localRobotId = null;

let wsReconnectTimer = null;
let rtcReconnectTimer = null;

const RECONNECT_INTERVAL = 1500; // 1.5 sec

export function startWebRTCConnection(robotId) {
    localRobotId = robotId;

    console.log("[WebRTC] Starting connection...");
    connectWebSocket(robotId);
}

function connectWebSocket(robotId) {
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${location.host}/ws/screen/${robotId}/`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("[WebSocket] Connected");

        // Clear reconnection timer if exists
        if (wsReconnectTimer) {
            clearTimeout(wsReconnectTimer);
            wsReconnectTimer = null;
        }

        // Request WebRTC offer
        ws.send(JSON.stringify({
            type: "request_screen",
            robot_id: robotId
        }));
    };

    ws.onmessage = async (e) => {
        const msg = JSON.parse(e.data);

        switch (msg.type) {
            case "robot_offer":
                await handleOffer(msg.offer);
                break;

            case "robot_ice":
                if (pc) {
                    try {
                        await pc.addIceCandidate(msg.ice);
                    } catch (err) {
                        console.warn("[WebRTC] ICE add failed:", err);
                    }
                }
                break;

            case "webrtc_error":
                console.error("[WebRTC] Error from server:", msg.error);
                restartWebRTC();
                break;
        }
    };

    ws.onerror = (err) => {
        console.error("[WebSocket] Error:", err);
    };

    ws.onclose = () => {
        console.warn("[WebSocket] Closed. Retrying...");
        scheduleWsReconnect();
    };

    // Create PeerConnection each time WS connects
    createPeerConnection();
}


function scheduleWsReconnect() {
    if (wsReconnectTimer) return; // prevent multiple loops

    wsReconnectTimer = setTimeout(() => {
        console.log("[WebSocket] Reconnecting...");
        connectWebSocket(localRobotId);
    }, RECONNECT_INTERVAL);
}


export function disconnectWebRTC() {
    console.log("[WebRTC] Disconnecting…");

    if (pc) {
        pc.getSenders().forEach(sender => {
            try { sender.track?.stop(); } catch (_) { }
        });
        pc.close();
    }

    if (ws) ws.close();

    pc = null;
    ws = null;

    localRobotId = null;

    const videoElem = document.getElementById("robot-video");
    if (videoElem) videoElem.srcObject = null;
}

function restartWebRTC() {
    if (rtcReconnectTimer) return;

    console.warn("[WebRTC] Restarting connection...");

    disconnectWebRTC();

    rtcReconnectTimer = setTimeout(() => {
        rtcReconnectTimer = null;
        startWebRTCConnection(localRobotId);
    }, RECONNECT_INTERVAL);
}

function createPeerConnection() {
    pc = new RTCPeerConnection({
        iceServers: [
            { urls: ["stun:stun.l.google.com:19302"] }
        ]
    });

    pc.ontrack = (event) => {
        document.getElementById("robot-video").srcObject = event.streams[0];
    };

    pc.onicecandidate = (event) => {
        if (event.candidate && ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "client_ice",
                robot_id: localRobotId,
                ice: event.candidate
            }));
        }
    };

    pc.oniceconnectionstatechange = () => {
        console.log("[WebRTC] ICE state:", pc.iceConnectionState);

        if (["disconnected", "failed"].includes(pc.iceConnectionState)) {
            restartWebRTC();
        }
    };
}


async function handleOffer(offer) {
    try {
        await pc.setRemoteDescription(offer);

        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        ws.send(JSON.stringify({
            type: "client_answer",
            robot_id: localRobotId,
            answer: answer
        }));
    } catch (err) {
        console.error("[WebRTC] Offer handling error:", err);
        restartWebRTC();
    }
}
