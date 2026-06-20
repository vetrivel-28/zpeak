document.addEventListener('DOMContentLoaded', () => {
  const urlInput = document.getElementById("backend-url");
  const saveBtn = document.getElementById("btn-save");
  const statusEl = document.getElementById("status");

  // Load current
  chrome.storage.sync.get("backend_url", (data) => {
    if (data.backend_url) {
      urlInput.value = data.backend_url;
    }
  });

  // Save
  saveBtn.addEventListener("click", () => {
    let url = urlInput.value.trim();
    if (url.endsWith('/')) {
      url = url.slice(0, -1);
    }
    
    chrome.storage.sync.set({ backend_url: url }, () => {
      statusEl.classList.remove("hidden");
      setTimeout(() => {
        statusEl.classList.add("hidden");
      }, 2000);
    });
  });
});
