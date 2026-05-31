let blurTimeout;

const tab = new WebSocket(
    `${wsScheme}://${window.location.host}/ws/exam/tab/${examId}/`
);


    /* =========================
       FULLSCREEN START
    ========================= */

    document.documentElement
        .requestFullscreen()
        .catch(err => {

            console.log(
                "Fullscreen failed",
                err
            );
        });

/* ================= TAB / MINIMIZE DETECTION ================= */

document.addEventListener("visibilitychange", function () {

    if (document.hidden) {

        blurTimeout = setTimeout(() => {

            sendViolation("TAB_SWITCH");

        }, 1000);

    } else {

        clearTimeout(blurTimeout);
    }
});

/* ================= FULLSCREEN DETECTION ================= */

document.addEventListener("fullscreenchange", function () {

    if (!document.fullscreenElement) {

        sendViolation("FULLSCREEN_EXIT");
    }
});

/* ================= GENERIC VIOLATION SENDER ================= */

function sendViolation(eventType) {

    if (tab.readyState === WebSocket.OPEN) {

        tab.send(JSON.stringify({

            type: "violation",

            event: eventType
        }));
    }
}