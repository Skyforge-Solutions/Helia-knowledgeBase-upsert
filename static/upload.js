const form = document.getElementById("uploadForm");
const responseDiv = document.getElementById("response");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  responseDiv.innerHTML = '';           
  const formData = new FormData(form);

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if (res.ok) {
      responseDiv.innerHTML = `
        ✅ Uploaded: ${data.inserted}<br>
        ⚠️ Duplicates: ${data.duplicates}
      `;
      return;
    }

    if (data.detail && data.detail.errors) {
      const items = data.detail.errors
        .map(e => `<li>Row ${e.row ?? '–'}: ${e.error}</li>`)
        .join("");
      responseDiv.innerHTML = `
        ❌ <strong>Validation failed</strong><br>
        Accepted: ${data.detail.accepted}<br>
        <ul style="color:red; padding-left:1rem;">${items}</ul>
      `;
    } else {
      const txt = typeof data.detail === "object"
        ? JSON.stringify(data.detail, null, 2)
        : data.detail;
      responseDiv.innerHTML = `<pre style="color:red;">❌ ${txt}</pre>`;
    }
  } catch (err) {
    responseDiv.innerHTML = `❌ Network/Error: ${err.message}`;
  }
});