let pc = null;
let ws = null;
let localRobotId = null;

// -----------------------------------------
// Public function: Start WebRTC connection
// -----------------------------------------
export function startWebRTCConnection(robotId) {
    localRobotId = robotId;
    
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${protocol}://${location.host}/ws/screen/${robotId}/`);

    ws.onopen = () => {
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
                    await pc.addIceCandidate(msg.ice);
                }
                break;
        }
    };

    createPeerConnection();
}


// -----------------------------------------
// Public function: Disconnect WebRTC
// -----------------------------------------
export function disconnectWebRTC() {
    console.log("Disconnecting WebRTC…");

    // Close PeerConnection
    if (pc) {
        pc.getSenders().forEach(sender => {
            try { sender.track?.stop(); } catch (_) { }
        });

        pc.close();
        pc = null;
    }

    // Close WebSocket
    if (ws) {
        ws.close();
        ws = null;
    }

    // Clear video screen (optional)
    const videoElem = document.getElementById("robot-video");
    if (videoElem) {
        videoElem.srcObject = null;
    }

    localRobotId = null;
}


// -----------------------------------------
// Internal helper functions (not exported)
// -----------------------------------------

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
        if (event.candidate && ws) {
            ws.send(JSON.stringify({
                type: "client_ice",
                robot_id: localRobotId,
                ice: event.candidate
            }));
        }
    };
}

async function handleOffer(offer) {
    await pc.setRemoteDescription(offer);

    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    ws.send(JSON.stringify({
        type: "client_answer",
        robot_id: localRobotId,
        answer: answer
    }));
}
