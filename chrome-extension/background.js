const DEFAULT_BACKEND = "http://127.0.0.1:8000";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.get("backend_url", (data) => {
    if (!data.backend_url) {
      chrome.storage.sync.set({ backend_url: DEFAULT_BACKEND });
    }
  });

  chrome.contextMenus.create({
    id: "explain-term",
    title: "Explain Term",
    contexts: ["selection"]
  });
});

async function getBackendUrl() {
  const data = await chrome.storage.sync.get("backend_url");
  return data.backend_url || DEFAULT_BACKEND;
}

// Fetch with timeout wrapper (Feature 7)
async function fetchWithTimeout(resource, options = {}) {
  const { timeout = 8000 } = options;
  
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  const response = await fetch(resource, {
    ...options,
    signal: controller.signal  
  });
  clearTimeout(id);
  return response;
}

// Feature 6: TTL Caching
async function getCachedTerm(term) {
  const data = await chrome.storage.local.get(term);
  if (data[term]) {
    const now = Date.now();
    if (now - data[term].timestamp < CACHE_TTL_MS) {
      return data[term].result;
    } else {
      await chrome.storage.local.remove(term);
    }
  }
  return null;
}

async function setCachedTerm(term, result) {
  await chrome.storage.local.set({
    [term]: {
      result: result,
      timestamp: Date.now()
    }
  });
}

// Message Listener for Popup and Content Scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "explain_term") {
    handleExplainTerm(request.term).then(sendResponse);
    return true; // Keep message channel open for async
  }
  
  if (request.action === "analyze_transcript") {
    handleAnalyzeTranscript(request.text).then(sendResponse);
    return true;
  }
  
  if (request.action === "health_check") {
    handleHealthCheck().then(sendResponse);
    return true;
  }
});

// Feature 1: Context Menu
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "explain-term" && info.selectionText) {
    const term = info.selectionText.trim();
    if (term) {
      // First, tell content script to show loading state
      chrome.tabs.sendMessage(tab.id, { action: "show_tooltip_loading", term: term });
      
      const result = await handleExplainTerm(term);
      
      // Then, send the result
      chrome.tabs.sendMessage(tab.id, { action: "show_tooltip_result", result: result });
    }
  }
});

// API Handlers
async function handleExplainTerm(term) {
  try {
    const cached = await getCachedTerm(term);
    if (cached) return { success: true, data: cached, cached: true };

    const baseUrl = await getBackendUrl();
    const response = await fetchWithTimeout(`${baseUrl}/term`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ term: term }),
      timeout: 10000 // LLM can take time
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      return { success: false, error: errData.error || errData.detail || "Invalid response from backend" };
    }

    const data = await response.json();
    if (data.saved !== false) { // Cache successful lookups
      await setCachedTerm(term, data);
    }
    return { success: true, data: data, cached: false };

  } catch (error) {
    let msg = "Unknown error occurred";
    if (error.name === 'AbortError') msg = "Request timed out. The backend is taking too long.";
    else if (error.message.includes('Failed to fetch')) msg = "Backend is offline or unreachable.";
    return { success: false, error: msg };
  }
}

async function handleAnalyzeTranscript(text) {
  try {
    const baseUrl = await getBackendUrl();
    const response = await fetchWithTimeout(`${baseUrl}/explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
      timeout: 15000
    });

    if (!response.ok) throw new Error("Invalid response");
    const data = await response.json();
    return { success: true, data: data };

  } catch (error) {
    return { success: false, error: "Analysis failed. Ensure backend is running." };
  }
}

async function handleHealthCheck() {
  try {
    const baseUrl = await getBackendUrl();
    const response = await fetchWithTimeout(`${baseUrl}/health`, { timeout: 2000 });
    if (response.ok) return { online: true };
    return { online: false };
  } catch (error) {
    return { online: false };
  }
}
