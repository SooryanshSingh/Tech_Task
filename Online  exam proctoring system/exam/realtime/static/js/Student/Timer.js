document.addEventListener("DOMContentLoaded", function () {
 
    const timerDisplay = document.getElementById("timer");
    
    function updateTimer() {
        fetch(`/get_remaining_time/${examId}/`)
            .then(response => response.json())
            .then(data => {
                let timeLeft = Math.floor(data.remaining_time);
    
                if (timeLeft <= 0) {
                    window.location.href = `/test_end/${examId}/`;
                    clearInterval(timerInterval);
                } else {
                    let minutes = Math.floor(timeLeft / 60);
                    let seconds = timeLeft % 60;
                    timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                }   
            })
            .catch(error => console.error("Error fetching timer:", error));
    }
    
    updateTimer();  
    const timerInterval = setInterval(updateTimer, 1000);
    });
    