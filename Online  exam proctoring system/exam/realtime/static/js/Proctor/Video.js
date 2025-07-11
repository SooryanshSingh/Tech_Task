document.addEventListener("DOMContentLoaded", function () {
    const examIdElement = document.getElementById("exam-id");

    if (!examIdElement) {
        console.error("Exam ID element not found!");
        return;
    }

    const examId = parseInt(examIdElement.value);
    console.log("Parsed exam ID:", examId);

    // Determine ws or wss based on current page protocol
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/stream/${examId}/`);

    const peerConnection = new RTCPeerConnection();
    const videoContainer = document.getElementById("remote-video");

    peerConnection.ontrack = event => {
        // Clear previous video (if any)
        videoContainer.innerHTML = "";
        const video = document.createElement("video");
        video.srcObject = event.streams[0];
        video.autoplay = true;
        video.controls = false;
        video.playsInline = true;
        videoContainer.appendChild(video);
    };

    peerConnection.onicecandidate = event => {
        if (event.candidate) {
            socket.send(JSON.stringify({ type: "candidate", candidate: event.candidate }));
        }
    };

    socket.onmessage = async event => {
        const data = JSON.parse(event.data);

        if (data.type === "offer") {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            socket.send(JSON.stringify({ type: "answer", sdp: answer }));
        } else if (data.type === "candidate") {
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (err) {
                console.error("Error adding received ICE candidate:", err);
            }
        }
    };
});
