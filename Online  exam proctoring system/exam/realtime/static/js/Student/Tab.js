
let blurTimeout;
const studentUsername = document.getElementById("student-username").value; // hidden input

const tab = new WebSocket(`${wsScheme}://${window.location.host}/ws/exam/tab/${examId}/`);

window.addEventListener('blur', function() {
    blurTimeout = setTimeout(() => {
        sendTabChangeMessage();
    }, 1000);
});

window.addEventListener('focus', function() {
    clearTimeout(blurTimeout);
});

function sendTabChangeMessage() {
    if (tab.readyState === WebSocket.OPEN) {
        tab.send(JSON.stringify({
            type: "tab_change",
            exam_id: examId,
            name: studentUsername,
            message: "Student has changed the tab or window."
        }));
    } else {
        console.error("WebSocket is not open. Cannot send tab change notification.");
    }
}

