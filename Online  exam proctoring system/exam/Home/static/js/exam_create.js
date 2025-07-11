function addExamForm() {
    const container = document.getElementById("exam-forms-container");
    const originalForm = document.querySelector(".exam-form");
    const clone = originalForm.cloneNode(true);
  
    // Clear values and remove CSRF
    clone.querySelectorAll("input, textarea, select").forEach(el => {
      if (el.name !== "csrfmiddlewaretoken") el.value = "";
    });
  
    container.appendChild(clone);
  }
  
  function submitExams() {
    const forms = document.querySelectorAll(".single-exam-form");
    const exams = [];
  
    forms.forEach((form, index) => {
      const formData = new FormData(form);
      const exam = {};
  
      for (let [key, value] of formData.entries()) {
        exam[key] = value;
      }
  
      // Log to ensure email_list exists
      console.log(`Form ${index + 1}:`, exam);
  
      exams.push(exam);
    });
  
    // Check if all exams include email_list
    const missingEmail = exams.find(exam => exam.email_list === undefined);
    if (missingEmail) {
      alert("One or more exams are missing the email list!");
      return;
    }
  
    fetch("", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      },
      body: JSON.stringify({ exams })
    })
      .then(response => {
        if (!response.ok) {
          return response.text().then(text => {
            throw new Error("Server error: " + text);
          });
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          alert("Error: " + data.error);
          console.error(data.details || data);
        } else {
          alert(data.message || "Exams submitted!");
          console.log(data);
          location.reload();
        }
      })
      .catch(error => {
        alert("Submission failed!");
        console.error("Error:", error);
      });
  }
  