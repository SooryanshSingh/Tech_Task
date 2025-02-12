

const chatSocket = new WebSocket(
    'ws://' + window.location.hostname + ':8000/ws/chat/' + roomName + '/'
);

   chatSocket.onmessage = function(e) {
    console.log("Chat");
        const data = JSON.parse(e.data);
        const chatLog = document.querySelector('#chat-log');
        const sender = data.sender || 'Unknown';

        if (sender !== username) {
            chatLog.innerHTML += '<div class="received-message"><strong>(' + sender + '): </strong>' + data.message + '</div>';
            chatLog.scrollTop = chatLog.scrollHeight;
        }
    };

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};

document.querySelector('#chat-message-input').focus();

document.querySelector('#chat-message-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        e.preventDefault(); 
        document.querySelector('#chat-message-submit').click(); 
    }
});
document.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && e.target.id !== "chat-message-input") {
        e.preventDefault();  
    }
});

document.querySelector('#chat-message-submit').onclick = function (e) {
    e.preventDefault();
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    if (message.trim()) {
        const chatLog = document.querySelector('#chat-log');
        chatLog.innerHTML += '<div class="sent-message"><strong>(' + username + '): </strong>' + message + '</div>';
        chatLog.scrollTop = chatLog.scrollHeight;
        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'message': message,
                'sender': username
            }));
        } else {
            console.error('WebSocket is not open. Message not sent.');
        }
        messageInputDom.value = '';
    }
};

const chatToggleButton = document.getElementById('chat-toggle-button');
const chatCloseButton = document.getElementById('chat-close-button');
const chatContainer = document.getElementById('chat-container');

chatToggleButton.onclick = function (e) {
    chatContainer.classList.add('active');
    chatToggleButton.style.display = 'none';
};

chatCloseButton.onclick = function (e) {
    chatContainer.classList.remove('active');
    chatToggleButton.style.display = 'block';
};

const questionLinks = document.querySelectorAll('.question-link');
const questionItems = document.querySelectorAll('.question-item');
let currentQuestionIndex = 0;

questionLinks.forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        const questionId = this.dataset.questionId;
        showQuestion(questionId);
    });
});

document.getElementById('prev-button').addEventListener('click', function () {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        showQuestionByIndex(currentQuestionIndex);
    }
});

document.getElementById('next-button').addEventListener('click', function () {
    if (currentQuestionIndex < questionItems.length - 1) {
        currentQuestionIndex++;
        showQuestionByIndex(currentQuestionIndex);
    }
});

document.getElementById('clear-button').addEventListener('click', function () {
    const currentQuestion = questionItems[currentQuestionIndex];
    const radioInputs = currentQuestion.querySelectorAll('input[type="radio"]');
    radioInputs.forEach(input => {
        input.checked = false;
    });
    checkAllAnswered();
    storeAnswers(); 
});

function showQuestion(questionId) {
    questionItems.forEach(item => {
        item.classList.remove('active');
        if (item.id === questionId) {
            item.classList.add('active');
            currentQuestionIndex = Array.from(questionItems).indexOf(item);
        }
    });
    updateNavigationButtons();
}

function showQuestionByIndex(index) {
    questionItems.forEach(item => {
        item.classList.remove('active');
    });
    questionItems[index].classList.add('active');
    updateNavigationButtons();
}

function updateNavigationButtons() {
    const prevButton = document.getElementById('prev-button');
    const nextButton = document.getElementById('next-button');

    prevButton.disabled = currentQuestionIndex === 0;
    nextButton.disabled = currentQuestionIndex === questionItems.length - 1;
}

const submitButton = document.querySelector('.submit-button');
const radioInputs = document.querySelectorAll('input[type="radio"]');

function checkAllAnswered() {
    const answeredQuestions = new Set();
    radioInputs.forEach(input => {
        if (input.checked) {
            answeredQuestions.add(input.name);
        }
    });
    if (answeredQuestions.size === questionItems.length) {
        submitButton.disabled = false;
    } else {
        submitButton.disabled = true;
    }
}

radioInputs.forEach(input => {
    input.addEventListener('change', function () {
        storeAnswers(); 
        checkAllAnswered();
    });
});
function storeAnswers() {
        const answers = {};
        radioInputs.forEach(input => {
            if (input.checked) {
                answers[input.name] = input.value;
            }
        });
        sessionStorage.setItem('examAnswers', JSON.stringify(answers));
    }

    function restoreAnswers() {
        const storedAnswers = sessionStorage.getItem('examAnswers');
        if (storedAnswers) {
            const answers = JSON.parse(storedAnswers);
            Object.keys(answers).forEach(name => {
                const input = document.querySelector(`input[name="${name}"][value="${answers[name]}"]`);
                if (input) {
                    input.checked = true;
                }
            });
        }
        checkAllAnswered(); 
    }

    


    window.onload = function () {
restoreAnswers(); 

document.getElementById('exam-form').onsubmit = function (e) {
    localStorage.removeItem('answers'); 
};
};


document.addEventListener("DOMContentLoaded", function () {
const examIdElement = document.getElementById("exam-id");

if (!examIdElement) {
    console.error("Exam ID element not found! Make sure the input exists.");
    return;
}

const examId = examIdElement.value; 

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
const isProctor = "{{ is_proctor|yesno:'true,false' }}" === "true";

if (!isProctor) {
let blurTimeout;

window.addEventListener('blur', function() {
    blurTimeout = setTimeout(() => {
        sendTabChangeMessage();
    }, 1000);
});

window.addEventListener('focus', function() {
    clearTimeout(blurTimeout);
});

function sendTabChangeMessage() {
    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'message': 'Student has changed the tab or window.',
            'sender': username
        }));
    }
}
}




if (isProctor){
console.log("isProctor:", isProctor);

const examSocket = new WebSocket(
'ws://' + window.location.hostname + ':8000/ws/exam/' + examId + '/'
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

}
