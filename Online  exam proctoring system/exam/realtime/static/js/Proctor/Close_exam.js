document.addEventListener("DOMContentLoaded", function () {
    const examIdElement = document.getElementById("exam-id");

    if (!examIdElement) {
        console.error("Exam ID element not found!");
        return;
    }

    const examId = parseInt(examIdElement.value);
    console.log("Parsed exam ID:", examId);

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const examSocket = new WebSocket(
        `${wsScheme}://${window.location.host}/ws/exam/${examId}/`
    );
    
    document.getElementById("close-exam-button").addEventListener("click", function () {
        console.log("HMM");
        console.log("WebSocket ReadyState:", examSocket.readyState);

        if (examSocket.readyState === WebSocket.OPEN) {
            examSocket.send(JSON.stringify({
                type: "close_exam",
                exam_id: examId
            }));
            console.log("Close exam message sent!");
        } else {
            console.error("WebSocket is not open. ReadyState: ", examSocket.readyState);
        }
    });

});


