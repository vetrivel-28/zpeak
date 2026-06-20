document.addEventListener('DOMContentLoaded', () => {
  
  // Health Check
  chrome.runtime.sendMessage({ action: "health_check" }, (response) => {
    if (!response || !response.online) {
      document.getElementById("health-banner").classList.remove("hidden");
    }
  });

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.getAttribute('data-target')).classList.add('active');
      
      if (btn.getAttribute('data-target') === 'tab-debug') {
        refreshDebugState();
      }
    });
  });

  // Feature 2: Explain Term
  const btnExplain = document.getElementById("btn-explain");
  const inputTerm = document.getElementById("term-input");
  const searchResult = document.getElementById("search-result");

  btnExplain.addEventListener("click", () => {
    const term = inputTerm.value.trim();
    if (!term) return;

    btnExplain.disabled = true;
    btnExplain.textContent = "...";
    searchResult.classList.remove("hidden");
    searchResult.innerHTML = `<div class="loader-container"><div class="loader"></div></div>`;

    chrome.runtime.sendMessage({ action: "explain_term", term: term }, (response) => {
      btnExplain.disabled = false;
      btnExplain.textContent = "Explain";

      if (!response.success) {
        searchResult.innerHTML = `<div class="error-msg">${escapeHtml(response.error)}</div>`;
        return;
      }

      const data = response.data;
      const sourceLabel = data.source === 'database' ? 'Local DB' : (data.source === 'llm' ? 'AI Extracted' : data.source);
      
      searchResult.innerHTML = `
        <h3 class="term-title">
          ${escapeHtml(data.term)}
          <span class="badge">${escapeHtml(sourceLabel)}</span>
        </h3>
        <p class="definition-text">${escapeHtml(data.definition)}</p>
        <div class="meta-info">
          <span>Cat: ${escapeHtml(data.category)}</span>
        </div>
      `;
    });
  });

  inputTerm.addEventListener("keypress", (e) => {
    if (e.key === "Enter") btnExplain.click();
  });

  // Feature 3: Transcript Analyzer
  const btnAnalyze = document.getElementById("btn-analyze");
  const inputTranscript = document.getElementById("transcript-input");
  const analyzeLoader = document.getElementById("analyze-loader");
  const analyzeResults = document.getElementById("analyze-results");

  btnAnalyze.addEventListener("click", () => {
    const text = inputTranscript.value.trim();
    if (!text) return;

    btnAnalyze.disabled = true;
    analyzeResults.classList.add("hidden");
    analyzeLoader.classList.remove("hidden");

    chrome.runtime.sendMessage({ action: "analyze_transcript", text: text }, (response) => {
      btnAnalyze.disabled = false;
      analyzeLoader.classList.add("hidden");
      analyzeResults.classList.remove("hidden");

      if (!response.success) {
        analyzeResults.innerHTML = `<div class="error-msg">${escapeHtml(response.error)}</div>`;
        return;
      }

      const data = response.data;
      analyzeResults.innerHTML = '';
      
      // Known Terms Accordion
      if (data.known_terms && data.known_terms.length > 0) {
        analyzeResults.appendChild(createAccordion("Known Terms", data.known_terms, data.known_terms.length));
      }
      
      // New Terms Accordion
      if (data.new_terms && data.new_terms.length > 0) {
        analyzeResults.appendChild(createAccordion("New Terms Extracted", data.new_terms, data.new_terms.length));
      }
      
      // Unknown Terms Accordion
      if (data.unknown_terms && data.unknown_terms.length > 0) {
        const unknownMap = data.unknown_terms.map(t => ({ term: t, definition: "No definition found" }));
        analyzeResults.appendChild(createAccordion("Unknown Terms", unknownMap, data.unknown_terms.length));
      }
      
      if (analyzeResults.innerHTML === '') {
        analyzeResults.innerHTML = `<p style="color: #94A3B8; text-align: center;">No technical terms found.</p>`;
      }
    });
  });

  function createAccordion(title, termsList, count) {
    const acc = document.createElement("div");
    acc.className = "accordion";
    
    let html = `
      <div class="accordion-header">
        <span>${title}</span>
        <span class="badge" style="background: rgba(255,255,255,0.1); color: white;">${count}</span>
      </div>
      <div class="accordion-body">
    `;
    
    termsList.forEach(t => {
      html += `
        <div class="term-item">
          <strong style="color:#5EEAD4;">${escapeHtml(t.term)}</strong>
          <div style="font-size:12px; margin-top:4px;">${escapeHtml(t.definition)}</div>
        </div>
      `;
    });
    
    html += `</div>`;
    acc.innerHTML = html;
    
    const header = acc.querySelector(".accordion-header");
    const body = acc.querySelector(".accordion-body");
    header.addEventListener("click", () => {
      body.classList.toggle("open");
    });
    
    return acc;
  }

  // Feature: Debug Tab
  const btnRefreshDebug = document.getElementById("btn-refresh-debug");
  
  function refreshDebugState() {
    chrome.runtime.sendMessage({ action: "get_debug_state" }, (response) => {
      if (response) {
        document.getElementById("dbg-platform").textContent = response.platform || "None";
        document.getElementById("dbg-status").textContent = response.monitorStatus || "Inactive";
        document.getElementById("dbg-backend").textContent = response.backendStatus || "Unknown";
        document.getElementById("dbg-terms").textContent = response.termsDetected || "0";
        document.getElementById("dbg-latency").textContent = (response.apiLatency || 0) + "ms";
        document.getElementById("dbg-caption").textContent = response.lastCaption || "Waiting for captions...";
      }
    });
  }

  btnRefreshDebug.addEventListener("click", refreshDebugState);

  function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
  }
});
