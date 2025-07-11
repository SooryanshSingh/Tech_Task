

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
