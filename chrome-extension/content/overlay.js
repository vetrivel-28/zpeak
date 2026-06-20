window.mkaInjectOverlayContainer = function() {
  if (document.getElementById("mka-live-overlay-container")) return;
  const container = document.createElement("div");
  container.id = "mka-live-overlay-container";
  document.body.appendChild(container);
};

window.mkaShowLiveCard = function(data) {
  window.mkaInjectOverlayContainer();
  const container = document.getElementById("mka-live-overlay-container");
  
  if (container.children.length >= 5) {
    // Remove oldest
    window.mkaRemoveCard(container.children[0]);
  }
  
  const card = document.createElement("div");
  card.className = "mka-live-card";
  
  const sourceLabel = data.source === 'database' ? 'Local DB' : 'AI Extracted';
  const badgeClass = data.source === 'database' ? 'mka-live-badge-db' : 'mka-live-badge-llm';
  
  const safeTerm = window.mkaEscapeHtml(data.term);
  const safeDef = window.mkaEscapeHtml(data.definition);
  const safeCat = window.mkaEscapeHtml(data.category);
  
  card.innerHTML = `
    <div class="mka-live-card-header">
      <span class="mka-live-term">${safeTerm}</span>
      <span class="mka-live-badge ${badgeClass}">${sourceLabel}</span>
    </div>
    <div class="mka-live-body">
      ${safeDef}
    </div>
    <div class="mka-live-footer">
      <span class="mka-live-meta">Cat: ${safeCat}</span>
    </div>
  `;
  
  container.appendChild(card);
  
  // Auto dismiss after 15 seconds
  setTimeout(() => window.mkaRemoveCard(card), 15000);
};

window.mkaRemoveCard = function(card) {
  if (!card || !card.parentNode) return;
  card.classList.add("removing");
  setTimeout(() => {
    if (card.parentNode) card.parentNode.removeChild(card);
  }, 300);
};

window.mkaEscapeHtml = function(unsafe) {
  if (!unsafe) return "";
  return unsafe
       .replace(/&/g, "&amp;")
       .replace(/</g, "&lt;")
       .replace(/>/g, "&gt;")
       .replace(/"/g, "&quot;")
       .replace(/'/g, "&#039;");
};
