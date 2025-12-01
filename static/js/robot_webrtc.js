let pc = null;
let ws = null;
let localRobotId = null;

function connectWebRTC(robotId) {
    localRobotId = robotId;

    ws = new WebSocket(`ws://${location.host}/ws/screen/`);

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
                await pc.addIceCandidate(msg.ice);
                break;
        }
    };

    createPeerConnection();
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
        if (event.candidate) {
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

window.addEventListener("DOMContentLoaded", () => {
    const robotId = window.ROBOT_ID;
    connectWebRTC(robotId);
});
