importScripts("shared/conversation_stopwords.js", "shared/caption_normalizer.js");

const DEFAULT_BACKEND = "http://127.0.0.1:8000";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

let debugState = {
  platform: "None",
  monitorStatus: "Inactive",
  lastCaption: "",
  apiLatency: 0,
  termsDetected: 0,
  backendStatus: "Unknown"
};

let recent_terms_cache = {}; // term -> timestamp
const LIVE_TERM_TTL = 120 * 1000; // 120 seconds

function cleanRecentTerms() {
  const now = Date.now();
  for (const [term, timestamp] of Object.entries(recent_terms_cache)) {
    if (now - timestamp > LIVE_TERM_TTL) {
      delete recent_terms_cache[term];
    }
  }
}

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
  console.log("[BACKGROUND] message received: " + request.action);
  
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
  
  if (request.action === "update_debug_state") {
    debugState = { ...debugState, ...request.state };
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === "get_debug_state") {
    handleHealthCheck().then(res => {
      debugState.backendStatus = res.online ? "Online" : "Offline";
      sendResponse(debugState);
    });
    return true;
  }
  
  if (request.action === "process_caption_batch") {
    handleProcessCaptionBatch(request.text).then(sendResponse);
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

async function handleProcessCaptionBatch(text) {
  cleanRecentTerms();
  const startTime = Date.now();
  
  // Rule 4: Normalize captions
  const normalizedText = normalizeCaptionText(text);
  
  const result = await handleAnalyzeTranscript(normalizedText);
  
  const latency = Date.now() - startTime;
  debugState.apiLatency = latency;

  if (!result.success) return result;

  const data = result.data;
  let termsToShow = [];
  const now = Date.now();

  const allTerms = [...(data.known_terms || []), ...(data.new_terms || [])];
  
  // Sort terms by length descending to process longest phrases first (for consumed-token tracking)
  allTerms.sort((a, b) => b.term.length - a.term.length);
  
  let consumedRanges = [];
  
  for (let item of allTerms) {
    const termLower = item.term.toLowerCase();
    
    // Consumed-Token Tracking: Verify term exists in text and is not part of a larger consumed phrase
    let foundUnconsumed = false;
    let searchIdx = 0;
    while (true) {
       const idx = normalizedText.toLowerCase().indexOf(termLower, searchIdx);
       if (idx === -1) break;
       
       const endIdx = idx + termLower.length;
       // Check if this substring overlaps with any already consumed range
       const isConsumed = consumedRanges.some(r => 
          (idx >= r.start && idx < r.end) || 
          (endIdx > r.start && endIdx <= r.end) || 
          (idx <= r.start && endIdx >= r.end)
       );
       
       if (!isConsumed) {
          foundUnconsumed = true;
          consumedRanges.push({ start: idx, end: endIdx });
          break; // We found a valid, unconsumed slot for this term!
       }
       searchIdx = idx + 1;
    }
    
    if (!foundUnconsumed) {
       console.log(`[TOKEN_SKIPPED] ${item.term} -> fully consumed fragment`);
       continue;
    }
    
    // Short Garbage Rejection
    const isShortWhitelist = SHORT_WHITELIST.some(w => w.toLowerCase() === termLower);
    if (item.term.length <= 3 && !isShortWhitelist) {
       console.log(`[OVERLAY_BLOCKED] ${item.term} -> length <= 3 and not in short whitelist`);
       continue;
    }

    // Check cache
    if (recent_terms_cache[termLower]) continue;
    
    // Rule 7: Whitelist Priority
    const isWhitelisted = WHITELIST.some(w => w.toLowerCase() === termLower);
    
    if (!isWhitelisted) {
      // Rule 1: Conversation Filtering
      if (STOPWORDS.includes(termLower)) {
        console.log(`[OVERLAY_BLOCKED] ${item.term} -> stopword`);
        continue;
      }
      
      // Rule 2: Person Name Rejection
      if (COMMON_NAMES.includes(termLower)) {
        console.log(`[OVERLAY_BLOCKED] ${item.term} -> person_name`);
        continue;
      }
      
      // Determine source & confidence
      let source = "llm";
      if (data.known_terms && data.known_terms.some(t => t.term === item.term)) {
        source = "database";
      }
      
      // Rule 6: Confidence Threshold (Only apply to LLM terms)
      if (source === "llm" && (item.confidence === undefined || item.confidence < 0.80)) {
        console.log(`[OVERLAY_BLOCKED] ${item.term} -> low confidence (${item.confidence})`);
        continue;
      }
      
      // Rule 3: Technical Context Gate (Only apply to LLM terms)
      if (source === "llm") {
        const hasTechContext = TECH_CONTEXT.some(tech => normalizedText.toLowerCase().includes(tech.toLowerCase()));
        if (!hasTechContext) {
          console.log(`[OVERLAY_BLOCKED] ${item.term} -> no technical context`);
          continue;
        }
      }
    }
    
    // Accepted!
    console.log(`[OVERLAY_ALLOWED] ${item.term}`);
    recent_terms_cache[termLower] = now;
    
    if (data.known_terms && data.known_terms.some(t => t.term === item.term)) {
        item.source = "database";
    } else {
        item.source = "llm";
    }
    
    termsToShow.push(item);
    debugState.termsDetected++;
  }

  // Rule 9: Maximum Cards (Sort by confidence, keep top 5)
  termsToShow.sort((a, b) => {
    const confA = a.source === 'database' ? 1.0 : (a.confidence || 0);
    const confB = b.source === 'database' ? 1.0 : (b.confidence || 0);
    return confB - confA;
  });
  
  if (termsToShow.length > 5) {
    termsToShow = termsToShow.slice(0, 5);
  }
  
  if (termsToShow.length > 0) {
      console.log(`[FINAL_TERMS] ${termsToShow.map(t => t.term).join(", ")}`);
  }

  return { success: true, terms: termsToShow };
}
