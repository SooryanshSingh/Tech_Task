
const examIdElement = document.getElementById("exam-id");
    

const examId = parseInt(examIdElement.value);
console.log("ok");
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
const examSocket = new WebSocket(
    `${wsScheme}://${window.location.host}/ws/exam/${examId}/`
);

    
    examSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
    
        if (data.type === "exam_closed") {
            window.location.href = `/test_end/${examId}/`;
        }
       
        
      
    
    };
    
    examSocket.onclose = function (e) {
    console.error("Exam WebSocket closed unexpectedly.");
    };