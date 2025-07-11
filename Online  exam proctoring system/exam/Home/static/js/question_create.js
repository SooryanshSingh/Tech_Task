function addQuestionForm() {
    const container = document.getElementById("question-forms-container");
    const originalForm = document.querySelector(".question-form");
    const clone = originalForm.cloneNode(true);

    // Clear all inputs and remove CSRF
    clone.querySelectorAll("input, textarea").forEach(el => el.value = "");
    const csrfInput = clone.querySelector("input[name='csrfmiddlewaretoken']");
    if (csrfInput) csrfInput.remove();

    container.appendChild(clone);
  }

  function submitQuestions() {
    const forms = document.querySelectorAll(".single-question-form");
    const questions = [];

    forms.forEach(form => {
      const formData = new FormData(form);
      const question = {};

      for (let [key, value] of formData.entries()) {
        question[key] = value.trim();
      }

      questions.push(question);
    });

    fetch("", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      },
      body: JSON.stringify({ questions })
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert("Error: " + data.error);
        console.error(data.details || data);
      } else {
        alert(data.message || "Questions submitted!");
        console.log(data);
        location.reload();  
      }
    })
    .catch(error => {
      alert("Submission failed!");
      console.error("Error:", error);
    });
  }