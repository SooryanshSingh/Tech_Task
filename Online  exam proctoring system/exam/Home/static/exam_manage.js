document.addEventListener('DOMContentLoaded', function() {
    const addQuestionButton = document.getElementById('addQuestion');
    const questionsContainer = document.getElementById('questions');
  
    addQuestionButton.addEventListener('click', function() {
      const questionCount = questionsContainer.getElementsByClassName('question-fieldset').length + 1;
      const newQuestionId = `question_${questionCount}`;
      const newQuestionFieldset = document.createElement('fieldset');
      newQuestionFieldset.setAttribute('class', 'question-fieldset');
      newQuestionFieldset.setAttribute('data-question-id', newQuestionId);
  
      newQuestionFieldset.innerHTML = `
        <legend>Question ${questionCount}</legend>
        <label for="${newQuestionId}">Question Text:</label><br>
        <textarea id="${newQuestionId}" name="${newQuestionId}"></textarea><br><br>
  
        <div class="answers">
          <button type="button" class="add-answer" data-question-id="${newQuestionId}">Add Answer</button><br><br>
        </div>
      `;
  
      questionsContainer.appendChild(newQuestionFieldset);
    });
  
    // Add Answer button functionality
    questionsContainer.addEventListener('click', function(event) {
      if (event.target && event.target.classList.contains('add-answer')) {
        const questionId = event.target.getAttribute('data-question-id');
        const answersContainer = questionsContainer.querySelector(`[data-question-id="${questionId}"] .answers`);
        const answerCount = answersContainer.getElementsByClassName('answer').length + 1;
        const newAnswerId = `answer_${questionId}_${answerCount}`;
  
        const newAnswerDiv = document.createElement('div');
        newAnswerDiv.setAttribute('class', 'answer');
        newAnswerDiv.setAttribute('data-answer-id', newAnswerId);
  
        newAnswerDiv.innerHTML = `
          <label for="${newAnswerId}">Answer Text:</label><br>
          <textarea id="${newAnswerId}" name="${newAnswerId}"></textarea><br>
          <input type="checkbox" id="correct_${newAnswerId}" name="correct_${newAnswerId}">
          <label for="correct_${newAnswerId}">Correct Answer</label><br><br>
        `;
  
        answersContainer.appendChild(newAnswerDiv);
      }
    });
  });
  