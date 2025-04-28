const form = document.getElementById("uploadForm");
const responseDiv = document.getElementById("response");
const submitBtn = document.getElementById("submitBtn");
const btnText = submitBtn.querySelector(".btn-text");
const btnLoading = submitBtn.querySelector(".btn-loading");

// Set loading state
function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  btnText.style.display = isLoading ? "none" : "inline-block";
  btnLoading.style.display = isLoading ? "inline-block" : "none";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  responseDiv.innerHTML = '';
  
  // Show loading state
  setLoading(true);
  
  const formData = new FormData(form);

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if (res.ok) {
      responseDiv.innerHTML = `
        <div class="message success">
          ✅ Uploaded: ${data.inserted}<br>
          ⚠️ Duplicates: ${data.duplicates}
        </div>
      `;
      return;
    }

    if (data.detail && data.detail.errors) {
      const items = data.detail.errors
        .map(e => `<li>Row ${e.row ?? '–'}: ${e.error}</li>`)
        .join("");
      responseDiv.innerHTML = `
        <div class="message error">
          ❌ <strong>Validation failed</strong><br>
          Accepted: ${data.detail.accepted}<br>
          <ul style="padding-left:1rem;">${items}</ul>
        </div>
      `;
    } else {
      const txt = typeof data.detail === "object"
        ? JSON.stringify(data.detail, null, 2)
        : data.detail;
      responseDiv.innerHTML = `<div class="message error">❌ ${txt}</div>`;
    }
  } catch (err) {
    responseDiv.innerHTML = `<div class="message error">❌ Network/Error: ${err.message}</div>`;
  } finally {
    // Hide loading state
    setLoading(false);
  }
});