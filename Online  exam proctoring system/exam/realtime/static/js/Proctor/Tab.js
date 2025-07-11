document.addEventListener("DOMContentLoaded", function () {
    const examIdElement = document.getElementById("exam-id");
    console.log("KKK");
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";

    if (!examIdElement) {
        console.error("Exam ID element not found!");
        return;
    }

    const examId = parseInt(examIdElement.value);
    console.log("Parsed exam ID:", examId);


    const tab = new WebSocket(`${wsScheme}://${window.location.host}/ws/exam/tab/${examId}/`);
        tab.onmessage= function (e) {
    const data= JSON.parse(e.data);
    if (data.type === "tab_change") {
    const sender = data.name;
    const message = data.message || "Tab change detected";
    
    alert(`⚠️ Tab Change Detected!\n\nFrom: ${sender}\nMessage: ${message}`);
    }
}
});

