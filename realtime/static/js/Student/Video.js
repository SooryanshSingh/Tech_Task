

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


    function captureEvidence() {
        console.log(
            "[CAPTURE START]"
        );
        console.log(
            "[VIDEO DIMENSIONS]",
            hiddenVideo.videoWidth,
            hiddenVideo.videoHeight
        );

        if (
            hiddenVideo.videoWidth === 0 ||
            hiddenVideo.videoHeight === 0
        ) {
    
            console.warn(
                "[EVIDENCE] Video not ready"
            );
    
            return null;
        }
    
        const canvas =
            document.createElement("canvas");
    
       
        canvas.width = 640;
        canvas.height = 360;
    
        const ctx =
            canvas.getContext("2d");
    
        ctx.drawImage(
            hiddenVideo,
            0,
            0,
            canvas.width,
            canvas.height
        );
    
        const image = canvas.toDataURL(
            "image/jpeg",
            0.8
        );
        
        console.log(
            "[CAPTURE SUCCESS]",
            image.length
        );
        
    
        return image
    }

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

        let evidence = null;

        if (
            eventType === "NO_FACE" ||
            eventType === "MULTIPLE_FACES" ||
            eventType === "PHONE_DETECTED"
        ) {
        
            try {
        
                evidence = captureEvidence();
                console.log(
                    "[EVIDENCE VALUE]",
                    evidence
                );
                
                console.log(
                    "[EVIDENCE LENGTH]",
                    evidence?.length
                );
        
            } catch(err) {
        
                console.error(
                    "[EVIDENCE ERROR]",
                    err
                );
            }
        }        
        socket.send(JSON.stringify({
        
            type:
                "violation",
        
            event:
                eventType,
        
            metadata:
                metadata,
        
            evidence:
                evidence,
        
            timestamp:
                Date.now(),
        }));
        }



    /* =========================
       LOAD FACE MODELS
    ========================= */

    let faceDetector = null;
    async function initFaceDetector() {

        try {
    
            console.log(
                "[INIT] Starting MediaPipe"
            );
    
            const vision =
                await FilesetResolver.forVisionTasks(
                    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
                );
    
            console.log(
                "[INIT] Vision loaded"
            );
    
            console.log(
                "[INIT] Creating detector"
            );
    
            faceDetector =
                await FaceDetector.createFromOptions(
                    vision,
                    {
                        baseOptions: {
                            modelAssetPath:
                            "/static/models/blaze_face_short_range.tflite"
                        },
    
                        runningMode:
                        "VIDEO",
    
                        minDetectionConfidence:
                        0.5
                    }
                );
    
            console.log(
                "[MEDIAPIPE READY]"
            );
    
        } catch (err) {
    
            console.error(
                "[MEDIAPIPE ERROR]",
                err
            );
        }
    }   
    console.log(
        "[IMPORTS]",
        window.FaceDetector,
        window.FilesetResolver
    ); 
    await initFaceDetector(); 
    let multipleFaceCounter = 0;

async function monitorFace() {

    if (!faceDetector) {
        return;
    }

    const result =
        faceDetector.detectForVideo(
            hiddenVideo,
            performance.now()
        );

    const faces =
        result.detections || [];

    console.log(
        "[MEDIAPIPE] Faces:",
        faces.length
    );

    if (faces.length === 0) {

        emitViolation(
            "NO_FACE"
        );

        multipleFaceCounter = 0;

        return;
    }

    if (faces.length > 1) {

        multipleFaceCounter++;

        console.log(
            "[MEDIAPIPE] Streak:",
            multipleFaceCounter
        );

        if (
            multipleFaceCounter >= 3
        ) {

            emitViolation(
                "MULTIPLE_FACES",
                {
                    face_count:
                    faces.length
                }
            );

            multipleFaceCounter = 0;
        }

    } else {

        multipleFaceCounter = 0;
    }
}
  

    setInterval(
        monitorFace,
        20000
    );

    console.log(
        "[STUDENT] Monitoring started"
    );

})();