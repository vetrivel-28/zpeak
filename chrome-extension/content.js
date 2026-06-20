let lastMouseX = 0;
let lastMouseY = 0;
let activeTooltip = null;

// Track mouse position for tooltip placement
document.addEventListener("contextmenu", (e) => {
  lastMouseX = e.pageX;
  lastMouseY = e.pageY;
});

// Also track mousedown in case contextmenu triggers strangely
document.addEventListener("mousedown", (e) => {
  if (e.button === 2) { // Right click
    lastMouseX = e.pageX;
    lastMouseY = e.pageY;
  }
});

// Dismiss tooltip if clicking outside
document.addEventListener("click", (e) => {
  if (activeTooltip && !activeTooltip.contains(e.target)) {
    activeTooltip.remove();
    activeTooltip = null;
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "show_tooltip_loading") {
    showTooltipLoading(request.term);
  } else if (request.action === "show_tooltip_result") {
    updateTooltipResult(request.result);
  }
});

function createTooltipBase() {
  if (activeTooltip) {
    activeTooltip.remove();
  }
  
  const tooltip = document.createElement("div");
  tooltip.className = "mka-tooltip-container";
  
  // Position it near the mouse
  tooltip.style.left = `${lastMouseX + 15}px`;
  tooltip.style.top = `${lastMouseY + 15}px`;
  
  document.body.appendChild(tooltip);
  activeTooltip = tooltip;
  return tooltip;
}

function showTooltipLoading(term) {
  const tooltip = createTooltipBase();
  tooltip.innerHTML = `
    <div class="mka-tooltip-header">
      <span class="mka-term">${escapeHtml(term)}</span>
      <span class="mka-badge mka-badge-loading">Analyzing...</span>
    </div>
    <div class="mka-tooltip-body">
      <div class="mka-loader"></div>
    </div>
  `;
}

function updateTooltipResult(response) {
  if (!activeTooltip) return; // Might have been closed by user

  if (!response.success) {
    activeTooltip.innerHTML = `
      <div class="mka-tooltip-header">
        <span class="mka-term mka-error-text">Error</span>
      </div>
      <div class="mka-tooltip-body mka-error-text">
        ${escapeHtml(response.error)}
      </div>
    `;
    return;
  }

  const data = response.data;
  
  let sourceBadge = '';
  if (data.source === 'database') sourceBadge = '<span class="mka-badge mka-badge-db">Local DB</span>';
  else if (data.source === 'llm') sourceBadge = '<span class="mka-badge mka-badge-llm">AI Extracted</span>';
  else sourceBadge = `<span class="mka-badge mka-badge-rejected">${escapeHtml(data.source)}</span>`;
  
  activeTooltip.innerHTML = `
    <div class="mka-tooltip-header">
      <span class="mka-term">${escapeHtml(data.term)}</span>
      ${sourceBadge}
    </div>
    <div class="mka-tooltip-body">
      ${escapeHtml(data.definition)}
    </div>
    <div class="mka-tooltip-footer">
      <span class="mka-category">${escapeHtml(data.category)}</span>
    </div>
  `;
}

function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
