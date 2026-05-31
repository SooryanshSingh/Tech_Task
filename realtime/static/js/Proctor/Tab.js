document.addEventListener("DOMContentLoaded", function () {
    const examIdElement = document.getElementById("exam-id");
    const timelineDiv = document.getElementById("timeline");

    if (!examIdElement || !timelineDiv) {
        return;
    }

    const examId = parseInt(examIdElement.value);
    const pathParts = window.location.pathname.split("/");
    const sessionId = pathParts[pathParts.indexOf("session") + 1];

    const STORAGE_KEY = `exam_${examId}_session_${sessionId}_timeline`;

    function getCurrentTime() {
        return new Date().toLocaleTimeString();
    }

    function addEventToTimeline(text) {
        const time = getCurrentTime();

        const div = document.createElement("div");
        div.classList.add("timeline-event");
        div.innerHTML = `<span class="time">${time}</span> — ${text}`;
        timelineDiv.prepend(div);

        const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        stored.push({ time, text });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    }

    function loadTimelineFromStorage() {
        const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        stored.forEach(event => {
            const div = document.createElement("div");
            div.classList.add("timeline-event");
            div.innerHTML = `<span class="time">${event.time}</span> — ${event.text}`;
            timelineDiv.appendChild(div);
        });
    }

    loadTimelineFromStorage();

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
        `${wsScheme}://${window.location.host}/ws/exam/tab/${examId}/`
    );

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (
            data.type === "violation_update" &&
            data.full_session_id === sessionId
        ) {
            addEventToTimeline(
                `${data.event_type}`
            );        }
    };
});
