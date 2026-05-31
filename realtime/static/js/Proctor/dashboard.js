const tableBody = document.getElementById("student-table");

const wsScheme =
    window.location.protocol === "https:" ? "wss" : "ws";

const socket = new WebSocket(
    `${wsScheme}://${window.location.host}/ws/exam/tab/${EXAM_ID}/`
);

/*
full_session_id -> {
    countCell,
    riskCell,
    eventCell
}
*/

const students = {};

socket.onmessage = function (event) {

    const data = JSON.parse(event.data);

    if (
        !["student_joined", "violation_update"]
        .includes(data.type)
    ) {
        return;
    }

    const maskedId = data.masked_session_id;

    const fullSessionId = data.full_session_id;

    const violationCount =
        data.violation_count || 0;

    const riskScore =
        data.risk_score || 0;

    const eventType =
        data.event_type || "CONNECTED";

    if (!fullSessionId) {

        console.warn(
            "[PROCTOR] Missing session id",
            data
        );

        return;
    }

    /*
    ===============================
    CREATE NEW ROW
    ===============================
    */

    if (!students[fullSessionId]) {

        const row = document.createElement("tr");

        row.style.cursor = "pointer";

        row.title =
            "Click to open session view";

        row.onclick = () => {

            window.open(
                `/proctor/${EXAM_ID}/session/${fullSessionId}/data`,
                "_blank"
            );
        };

        /*
        SESSION
        */

        const sessionCell =
            document.createElement("td");

        sessionCell.innerText = maskedId;

        /*
        VIOLATION COUNT
        */

        const countCell =
            document.createElement("td");

        countCell.innerText = violationCount;

        /*
        RISK SCORE
        */

        const riskCell =
            document.createElement("td");

        riskCell.innerText = riskScore;

        /*
        LATEST EVENT
        */

        const eventCell =
            document.createElement("td");

        eventCell.innerText = eventType;

        /*
        APPEND
        */

        row.appendChild(sessionCell);

        row.appendChild(countCell);

        row.appendChild(riskCell);

        row.appendChild(eventCell);

        tableBody.appendChild(row);

        students[fullSessionId] = {

            countCell,

            riskCell,

            eventCell
        };
    }

    /*
    ===============================
    UPDATE EXISTING ROW
    ===============================
    */

    students[fullSessionId]
        .countCell.innerText =
        violationCount;

    students[fullSessionId]
        .riskCell.innerText =
        riskScore;

    students[fullSessionId]
        .eventCell.innerText =
        eventType;
};

socket.onopen = () => {

    console.log(
        "[PROCTOR] Dashboard WS connected"
    );
};

socket.onclose = () => {

    console.log(
        "[PROCTOR] Dashboard WS disconnected"
    );
};