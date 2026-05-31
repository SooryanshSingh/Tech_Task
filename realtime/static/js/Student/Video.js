(async function () {

    console.log("[STUDENT] Init start");

    /* =========================
       EXAM ID
    ========================= */

    const examIdElement =
        document.getElementById("exam-id");

    if (!examIdElement) {

        console.error(
            "[STUDENT] Exam ID missing"
        );

        return;
    }

    const examId =
        examIdElement.value;

    /* =========================
       AGORA TOKEN
    ========================= */

    const res =
        await fetch(
            `/agora/token/${examId}/`
        );

    if (!res.ok) {

        console.error(
            "[STUDENT] Token fetch failed"
        );

        return;
    }

    const {
        token,
        appId,
        channel,
        uid
    } = await res.json();

    console.log(
        "[STUDENT] Token OK"
    );

    /* =========================
       AGORA CLIENT
    ========================= */

    const client =
        AgoraRTC.createClient({
            mode: "rtc",
            codec: "vp8",
        });

    await client.join(
        appId,
        channel,
        token,
        uid
    );

    console.log(
        "[STUDENT] Joined channel"
    );

    /* =========================
       CAMERA TRACK
    ========================= */

    const localVideoTrack =
        await AgoraRTC
            .createCameraVideoTrack();

    await client.publish([
        localVideoTrack
    ]);

    console.log(
        "[STUDENT] Camera published"
    );

    /* =========================
       DISPLAY VIDEO
    ========================= */

    await localVideoTrack.play(
        "student-video"
    );

    console.log(
        "[STUDENT] Local video playing"
    );

    /* =========================
       REAL VIDEO ELEMENT
       FOR FACE DETECTION
    ========================= */

    const mediaTrack =
        localVideoTrack
            .getMediaStreamTrack();

    const hiddenVideo =
        document.createElement("video");

    hiddenVideo.autoplay = true;

    hiddenVideo.muted = true;

    hiddenVideo.playsInline = true;

    hiddenVideo.style.position =
        "absolute";

    hiddenVideo.style.left =
        "-9999px";

    hiddenVideo.srcObject =
        new MediaStream([
            mediaTrack
        ]);

    document.body.appendChild(
        hiddenVideo
    );

    await new Promise(resolve => {

        hiddenVideo.onloadedmetadata =
            resolve;
    });
    
    hiddenVideo.play();
    
    console.log(
        "[STUDENT] Hidden video ready"
    );
    
    console.log(
        "[DEBUG] Initial dimensions:",
        hiddenVideo.videoWidth,
        hiddenVideo.videoHeight
    );
    
    console.log(
        "[DEBUG] Initial readyState:",
        hiddenVideo.readyState
    );

    /* =========================
       WEBSOCKET
    ========================= */

    const wsScheme =
        window.location.protocol
            === "https:"
            ? "wss"
            : "ws";

    const socket =
        new WebSocket(
            `${wsScheme}://${window.location.host}/ws/exam/tab/${examId}/`
        );

    socket.onopen = function () {

        console.log(
            "[STUDENT] Socket connected"
        );
    };

    socket.onclose = function () {

        console.error(
            "[STUDENT] Socket closed"
        );
    };

    /* =========================
       COOLDOWNS
    ========================= */

    const violationCooldowns = {};

    /* =========================
       GENERIC VIOLATION
    ========================= */

    function emitViolation(
        eventType,
        metadata = {}
    ) {

        const now = Date.now();

        if (
            violationCooldowns[eventType]
            &&
            now -
            violationCooldowns[eventType]
            < 10000
        ) {
            return;
        }

        violationCooldowns[eventType] =
            now;

        if (
            socket.readyState
            !== WebSocket.OPEN
        ) {

            console.error(
                "[VIOLATION] Socket not open"
            );

            return;
        }

        socket.send(JSON.stringify({

            type:
                "violation",

            event:
                eventType,

            metadata:
                metadata,

            timestamp:
                Date.now(),
        }));

        console.log(
            "[VIOLATION]",
            eventType
        );
    }



    /* =========================
       LOAD FACE MODELS
    ========================= */

    await faceapi.nets
        .tinyFaceDetector
        .loadFromUri(
            "/static/models"
        );

    console.log(
        "[STUDENT] Face models loaded"
    );

    /* =========================
       FACE MONITOR
    ========================= */

    async function monitorFace() {

        console.log(
            "[DEBUG] Video dimensions:",
            hiddenVideo.videoWidth,
            hiddenVideo.videoHeight
        );
    
        console.log(
            "[DEBUG] Ready state:",
            hiddenVideo.readyState
        );
    
        const detections =
            await faceapi.detectAllFaces(
                hiddenVideo,
                new faceapi.TinyFaceDetectorOptions({
                    inputSize: 416,
                    scoreThreshold: 0.2
                })
            );
    
        console.log(
            "[DEBUG] Faces detected:",
            detections.length
        );
    
        console.log(
            "[DEBUG] Raw detections:",
            detections
        );
    
        if (detections.length === 0) {
    
            emitViolation(
                "NO_FACE"
            );
        }
    
        if (detections.length > 1) {
    
            emitViolation(
                "MULTIPLE_FACES",
                {
                    face_count:
                        detections.length
                }
            );
        }
    }
        
       
    /* =========================
       START MONITORING
    ========================= */

    setInterval(
        monitorFace,
        20000
    );

    console.log(
        "[STUDENT] Monitoring started"
    );

})();