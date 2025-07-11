const peerConnection = new RTCPeerConnection();
const videoContainer = document.getElementById("student-video");
let localStream = null;

const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/stream/${examId}/`);

// Step 1: getUserMedia
navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(stream => {
        localStream = stream;

        if (videoContainer) {
            const video = document.createElement("video");
            video.srcObject = stream;
            video.autoplay = true;
            video.muted = true;
            video.playsInline = true;
            videoContainer.appendChild(video);
        }

        stream.getTracks().forEach(track => peerConnection.addTrack(track, stream));

        if (socket.readyState === WebSocket.OPEN) {
            createAndSendOffer();
        } else {
            socket.addEventListener('open', createAndSendOffer);
        }
    })
    .catch(error => {
        console.error("Camera access error:", error);
    });

// Step 2: Send ICE candidates
peerConnection.onicecandidate = event => {
    if (event.candidate && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "candidate",
            candidate: event.candidate,
            from: studentUsername
        }));
    }
};

// Step 3: Handle messages from proctor
socket.onmessage = async event => {
    const data = JSON.parse(event.data);

    if (data.type === "answer") {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
    } else if (data.type === "candidate") {
        try {
            if (peerConnection.remoteDescription) {
                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            }
        } catch (err) {
            console.log("Some error");
            }
    } else if (data.type === "proctor-joined") {
        console.log("🔁 Proctor reconnected — resending offer...");
        createAndSendOffer();
    }
};

// Step 4: Offer sending logic
function createAndSendOffer() {
    peerConnection.createOffer()
        .then(offer => peerConnection.setLocalDescription(offer))
        .then(() => {
            socket.send(JSON.stringify({
                type: "offer",
                sdp: peerConnection.localDescription,
                from: studentUsername
            }));
        })
        .catch(err => console.error("Offer creation failed:", err));
}
