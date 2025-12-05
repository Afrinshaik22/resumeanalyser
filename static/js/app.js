document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("resume-form");
  const fileInput = document.getElementById("resume");
  const fileNameSpan = document.getElementById("file-name");
  const loadingEl = document.getElementById("loading");
  const errorEl = document.getElementById("error");
  const resultsSection = document.getElementById("results");

  const domainValueEl = document.getElementById("domain-value");
  const skillsListEl = document.getElementById("skills-list");
  const strengthsListEl = document.getElementById("strengths-list");
  const weaknessesListEl = document.getElementById("weaknesses-list");
  const suggestionsListEl = document.getElementById("suggestions-list");

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) {
      fileNameSpan.textContent = file.name;
    } else {
      fileNameSpan.textContent = "No file selected";
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    errorEl.textContent = "";
    resultsSection.classList.add("hidden");

    const file = fileInput.files[0];
    if (!file) {
      errorEl.textContent = "Please select a PDF resume to upload.";
      return;
    }

    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      errorEl.textContent = "Only PDF files are supported.";
      return;
    }

    const formData = new FormData();
    formData.append("resume", file);

    const emailInput = document.getElementById("email");
    if (emailInput.value) {
      formData.append("email", emailInput.value);
    }

    loadingEl.classList.remove("hidden");

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong while analyzing the resume.");
      }

      // Populate results
      domainValueEl.textContent = data.domain || "-";

      const renderList = (el, items) => {
        el.innerHTML = "";
        if (!items || items.length === 0) {
          const li = document.createElement("li");
          li.textContent = "No items detected.";
          el.appendChild(li);
          return;
        }
        items.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          el.appendChild(li);
        });
      };

      // Skills are displayed as tags
      skillsListEl.innerHTML = "";
      if (data.skills && data.skills.length > 0) {
        data.skills.forEach((skill) => {
          const li = document.createElement("li");
          li.textContent = skill;
          skillsListEl.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "No skills detected.";
        skillsListEl.appendChild(li);
      }

      renderList(strengthsListEl, data.strengths);
      renderList(weaknessesListEl, data.weaknesses);
      renderList(suggestionsListEl, data.suggestions);

      resultsSection.classList.remove("hidden");
    } catch (err) {
      console.error(err);
      errorEl.textContent = err.message || "Unexpected error occurred.";
    } finally {
      loadingEl.classList.add("hidden");
    }
  });
});
