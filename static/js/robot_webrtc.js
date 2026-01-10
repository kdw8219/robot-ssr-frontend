let pc = null;
let ws = null;
let localRobotId = null;

let wsReconnectTimer = null;
let rtcReconnectTimer = null;

const RECONNECT_INTERVAL = 1500; // 1.5 sec

export function startWebRTCConnection(robotId) {
    localRobotId = robotId;

    console.log("[WebRTC] Starting connection for robot:", robotId);
    connectWebSocket(robotId);
}

export function disconnectWebRTC() {
    console.log("[WebRTC] Disconnecting…");

    if (pc) {
        pc.getSenders().forEach(sender => {
            try { sender.track?.stop(); } catch (_) {}
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

// ==============================
// WebSocket
// ==============================

function connectWebSocket(robotId) {
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${location.host}/ws/screen/${robotId}/`;

    console.log("[WebRTC] Connecting WebSocket:", wsUrl);
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("[WebRTC] WebSocket connected");

        if (wsReconnectTimer) {
            clearTimeout(wsReconnectTimer);
            wsReconnectTimer = null;
        }

        // signaling 시작 요청
        ws.send(JSON.stringify({
            type: "screen_request",
            robot_id: robotId
        }));
    };

    ws.onmessage = async (e) => {
        const msg = JSON.parse(e.data);

        switch (msg.type) {
            case "heartbeat_check":
                // Keepalive; no client action required.
                break;
            case "robot_offer":
                await handleOffer(msg.offer);
                break;

            case "robot_ice":
                if (pc && msg.ice) {
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

            default:
                console.warn("[WebRTC] Unknown signaling message:", msg);
        }
    };

    ws.onerror = (err) => {
        console.error("[WebRTC] WebSocket error:", err);
    };

    ws.onclose = () => {
        console.warn("[WebRTC] WebSocket closed, retrying…");
        scheduleWsReconnect();
    };

    createPeerConnection();
}

function scheduleWsReconnect() {
    if (wsReconnectTimer) return;

    wsReconnectTimer = setTimeout(() => {
        console.log("[WebRTC] Reconnecting WebSocket…");
        connectWebSocket(localRobotId);
    }, RECONNECT_INTERVAL);
}

// ==============================
// WebRTC
// ==============================

function createPeerConnection() {
    pc = new RTCPeerConnection({
        iceServers: [
            {
                urls: ["turn:172.30.32.224:3480?transport=tcp"],
                username: "temp", // delete later
                credential: "temp123" // delete later
            }
        ],
        iceTransportPolicy: "relay"
    });

    pc.ontrack = (event) => {
        const videoElem = document.getElementById("robot-video");
        if (videoElem) {
            videoElem.srcObject = event.streams[0];
        }
    };

    pc.onicecandidate = (event) => {
        if (event.candidate && ws && ws.readyState === WebSocket.OPEN) {
            const c = event.candidate;
            console.log("[WebRTC] ICE candidate:", {
                candidate: c.candidate,
                sdpMid: c.sdpMid,
                sdpMLineIndex: c.sdpMLineIndex,
            });
            ws.send(JSON.stringify({
                type: "client_ice",
                robot_id: localRobotId,
                ice: event.candidate
            }));
        }
    };

    pc.onicecandidateerror = (event) => {
        console.warn(
            "[WebRTC] ICE candidate error:",
            {
                errorCode: event.errorCode,
                errorText: event.errorText,
                url: event.url,
                hostCandidate: event.hostCandidate,
            }
        );
    };

    pc.onicegatheringstatechange = () => {
        console.log("[WebRTC] ICE gathering state:", pc.iceGatheringState);
    };

    pc.oniceconnectionstatechange = () => {
        console.log("[WebRTC] ICE state:", pc.iceConnectionState);

        if (["disconnected", "failed"].includes(pc.iceConnectionState)) {
            restartWebRTC();
        }
    };

    pc.onconnectionstatechange = () => {
        console.log("[WebRTC] Peer connection state:", pc.connectionState);
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

function restartWebRTC() {
    if (rtcReconnectTimer) return;

    console.warn("[WebRTC] Restarting connection…");

    const robotId = localRobotId;
    disconnectWebRTC();

    rtcReconnectTimer = setTimeout(() => {
        rtcReconnectTimer = null;
        if (robotId) {
            startWebRTCConnection(robotId);
        } else {
            console.warn("[WebRTC] Restart skipped: robot_id is null");
        }
    }, RECONNECT_INTERVAL);
}
