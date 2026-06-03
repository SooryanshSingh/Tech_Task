document.addEventListener("DOMContentLoaded", function () {
    const examIdElement = document.getElementById("exam-id");
    const timelineDiv = document.getElementById("timeline");

    if (!examIdElement || !timelineDiv) {
        return;
    }
    function loadTimelineFromStorage() {

        const stored =
            JSON.parse(
                localStorage.getItem(
                    STORAGE_KEY
                )
            ) || [];
    
        stored.forEach(event => {
    
            const evidenceLink =
                event.evidence_url
                    ? `
                        <a
                            href="${event.evidence_url}"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            View Evidence
                        </a>
                      `
                    : "";
    
            const div =
                document.createElement("div");
    
            div.classList.add(
                "timeline-event"
            );
    
            div.innerHTML =
                `
            <span class="time">
                ${event.log_timestamp}
            </span>                —
                ${event.event_type}
                ${evidenceLink}
                `;
    
            timelineDiv.appendChild(
                div
            );
        });
    }

    const examId = parseInt(examIdElement.value);
    const pathParts = window.location.pathname.split("/");
    const sessionId = pathParts[pathParts.indexOf("session") + 1];

    const STORAGE_KEY = `exam_${examId}_session_${sessionId}_timeline`;

    function getCurrentTime() {
        return new Date().toLocaleTimeString();
    }

    function addEventToTimeline(event) {

        const time =event.log_timestamp || getCurrentTime();    
        const evidenceLink =
            event.evidence_url
                ? `
                    <a
                        href="${event.evidence_url}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        View Evidence
                    </a>
                  `
                : "";
    
        const div =
            document.createElement("div");
    
        div.classList.add(
            "timeline-event"
        );
    
        div.innerHTML =
            `
            <span class="time">
                ${time}
            </span>
            —
            ${event.event_type}
            ${evidenceLink}
            `;
    
        timelineDiv.prepend(
            div
        );
    
        const stored =
            JSON.parse(
                localStorage.getItem(
                    STORAGE_KEY
                )
            ) || [];
    
        stored.push(event);
    
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(stored)
        );
    }
        loadTimelineFromStorage();

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
        `${wsScheme}://${window.location.host}/ws/exam/tab/${examId}/`
    );

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);

    console.log(
        "[TIMELINE WS]",
        data
    );
        if (
            data.type === "violation_update" &&
            data.full_session_id === sessionId
        ) {
            addEventToTimeline(
                data
            );        }
    };
});
