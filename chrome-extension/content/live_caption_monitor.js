console.log("[CONTENT] injected");

let isMonitoringPaused = false;
let pendingBatch = "";
const recentCaptionHashes = new Map(); // Store hash -> timestamp for 5m TTL

let lastCaptionTime = 0;
let debugStats = {
  captionMutations: 0,
  nonCaptionMutations: 0,
  backendCalls: 0,
  termsRendered: 0
};

const UI_SPAM_WORDS = [
  "Camera", "Microphone", "Speakers", "USB", "Ready to join", "Backgrounds", "Join now"
];

function checkUIForSpam(text) {
  const lowerText = text.toLowerCase();
  return UI_SPAM_WORDS.some(w => lowerText.includes(w.toLowerCase()));
}

// Simple string hash
function getCaptionHash(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = ((hash << 5) - hash) + text.charCodeAt(i);
    hash |= 0;
  }
  return hash.toString();
}

const MEET_SELECTORS = [
  'div[class*="a4cQT"]', 
  'div[class*="Tccvwe"]', 
  'div[jsname="tX9u1b"]', 
  '.iO8Dzf',
  '[aria-live="polite"]',
  '[aria-live="assertive"]',
  '[role="alert"]',
  '[role="status"]',
  'div[class*="caption"]',
  'div[class*="transcript"]',
  'div[jsname="YSxPC"]'
];

const TEAMS_SELECTORS = [
  'span[data-tid="closed-caption-text"]', 
  'div[data-tid="closed-captions-container"]'
];

function getPlatform() {
  if (window.location.hostname.includes("meet.google.com")) return "Google Meet";
  if (window.location.hostname.includes("teams.microsoft.com")) return "MS Teams";
  return "Unknown";
}

const isMeet = getPlatform() === "Google Meet";
if (isMeet) {
  console.log("[MEET] detected");
}

function updateDebugState(lastCaption) {
  chrome.runtime.sendMessage({
    action: "update_debug_state",
    state: {
      platform: getPlatform(),
      monitorStatus: isMonitoringPaused ? "Paused (Backend Offline)" : "Active",
      lastCaption: lastCaption || "(None)",
      stats: debugStats
    }
  });
}

function extractSpeaker(node) {
  if (!node) return "Unknown";
  // Try to find the nearest speaker container (Meet usually uses div.zs7s8d or similar)
  try {
    const container = node.closest('div[jsname="tX9u1b"]') || node.closest('.iO8Dzf') || node.parentElement;
    if (container) {
       // Look for speaker name div
       const speakerDiv = container.querySelector('.zs7s8d, [class*="speaker"], [class*="name"]');
       if (speakerDiv) return (speakerDiv.innerText || speakerDiv.textContent || "Unknown").trim();
    }
  } catch(e) {}
  return "Unknown";
}

function processCaptionText(node, text) {
  if (!text) return;
  const now = Date.now();
  
  const speaker = extractSpeaker(node);
  const hash = getCaptionHash(speaker + "|" + text);
  
  if (recentCaptionHashes.has(hash) && (now - recentCaptionHashes.get(hash) < 5 * 60 * 1000)) {
    return; // Drop immediately, no backend call
  }
  
  recentCaptionHashes.set(hash, now);
  pendingBatch += " " + text;
  lastCaptionTime = now;
  console.log(`[CAPTION_ACCEPTED] ${speaker}: ${text}`);
  updateDebugState(text.substring(0, 50) + "...");
}

function createObserver() {
  return new MutationObserver((mutations) => {
    if (isMonitoringPaused) return;
    
    const selectors = isMeet ? MEET_SELECTORS : TEAMS_SELECTORS;

    mutations.forEach((mutation) => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
             const matches = selectors.some(sel => node.matches && node.matches(sel) || (node.querySelector && node.querySelector(sel)));
             if (matches) {
                debugStats.captionMutations++;
                const text = (node.innerText || node.textContent || "").trim();
                if (text.length <= 5 || !text.includes(" ")) {
                    console.log(`[CAPTION_REJECTED_UI_TEXT] ${text}`);
                    return;
                }
                if (checkUIForSpam(text)) {
                    console.log(`[UI_TEXT_BLOCKED] ${text}`);
                    return;
                }
                processCaptionText(node, text);
             } else {
                // Deep scan fallback for heavily nested added nodes
                let foundNested = false;
                selectors.forEach(sel => {
                  if (node.querySelectorAll) {
                    node.querySelectorAll(sel).forEach(n => {
                      foundNested = true;
                      debugStats.captionMutations++;
                      const text = (n.innerText || n.textContent || "").trim();
                      if (text.length <= 5 || !text.includes(" ")) {
                          console.log(`[CAPTION_REJECTED_UI_TEXT] ${text}`);
                          return;
                      }
                      if (checkUIForSpam(text)) {
                          console.log(`[UI_TEXT_BLOCKED] ${text}`);
                          return;
                      }
                      processCaptionText(n, text);
                    });
                  }
                });
                
                if (!foundNested) {
                    debugStats.nonCaptionMutations++;
                    const nodeText = (node.innerText || node.textContent || "").trim();
                    if (nodeText.length > 0) {
                        console.log(`[NON_CAPTION_MUTATION_BLOCKED] ${nodeText.substring(0, 40)}`);
                    }
                }
             }
          }
        });
      } else if (mutation.type === 'characterData') {
        const parent = mutation.target.parentElement;
        if (parent) {
           const isMatch = selectors.some(sel => (parent.matches && parent.matches(sel)) || parent.closest(sel));
           if (isMatch) {
              debugStats.captionMutations++;
              const text = (mutation.target.textContent || "").trim();
              if (text.length <= 5 || !text.includes(" ")) {
                  console.log(`[CAPTION_REJECTED_UI_TEXT] ${text}`);
                  return;
              }
              if (checkUIForSpam(text)) {
                  console.log(`[UI_TEXT_BLOCKED] ${text}`);
                  return;
              }
              processCaptionText(parent, text);
           } else {
              debugStats.nonCaptionMutations++;
              const text = (mutation.target.textContent || "").trim();
              if (text.length > 0) {
                 console.log(`[NON_CAPTION_MUTATION_BLOCKED] ${text.substring(0, 40)}`);
              }
           }
        }
      }
    });
    
    // Cleanup hashes TTL
    const now = Date.now();
    for (const [hash, ts] of recentCaptionHashes.entries()) {
      if (now - ts > 5 * 60 * 1000) {
        recentCaptionHashes.delete(hash);
      }
    }
  });
}

let observer = null;
let currentObserverTarget = null;
let lastMeetingState = "";
let lastCaptionState = "";

const VERIFIED_CONTAINERS = isMeet ? [
  'div[class*="a4cQT"]', 
  'div[jsname="tX9u1b"]',
  'div[class*="Tccvwe"]',
  'div[class*="caption"]'
] : TEAMS_SELECTORS;

function checkMeetingState() {
  // 1. Check if joined
  let isJoined = true;
  const buttons = document.querySelectorAll('button, span, div[role="button"]');
  for (const btn of buttons) {
      const text = (btn.textContent || "").trim().toLowerCase();
      if (text === "join now" || text === "ask to join" || text === "ready to join") {
          isJoined = false;
          break;
      }
  }

  if (!isJoined) {
     if (lastMeetingState !== "NOT_JOINED") {
         console.log("[MEETING_NOT_JOINED]");
         lastMeetingState = "NOT_JOINED";
     }
     
     if (observer) {
         observer.disconnect();
         observer = null;
         currentObserverTarget = null;
     }
     return;
  }
  
  if (lastMeetingState !== "JOINED") {
      console.log("[MEETING_JOINED]");
      lastMeetingState = "JOINED";
  }
  
  // 2. Check Captions
  let captionContainer = null;
  for (const sel of VERIFIED_CONTAINERS) {
      captionContainer = document.querySelector(sel);
      if (captionContainer) break;
  }
  
  if (!captionContainer) {
      if (lastCaptionState !== "DISABLED") {
          console.log("[CAPTIONS_DISABLED]");
          lastCaptionState = "DISABLED";
      }
      if (observer) {
          observer.disconnect();
          observer = null;
          currentObserverTarget = null;
      }
  } else {
      if (lastCaptionState !== "ENABLED") {
          console.log("[CAPTIONS_ENABLED]");
          lastCaptionState = "ENABLED";
      }
      
      // Attach strictly to the verified container
      if (!observer || currentObserverTarget !== captionContainer) {
          if (observer) observer.disconnect();
          
          observer = createObserver();
          observer.observe(captionContainer, {
              childList: true,
              subtree: true,
              characterData: true
          });
          currentObserverTarget = captionContainer;
          console.log("[OBSERVER] attached to caption container");
      }
  }
}

setInterval(checkMeetingState, 1000);

function flushBatch() {
  if (isMonitoringPaused) return;
  
  // Kill switch: If no caption node has changed in the last 30 seconds
  if (Date.now() - lastCaptionTime > 30000) {
     pendingBatch = ""; // Clear out stale data
     return; // Do not call backend, do not extract, do not update overlay
  }
  
  const textToSend = pendingBatch.trim();
  if (textToSend.length > 0) {
    pendingBatch = ""; // reset for next batch
    debugStats.backendCalls++;
    
    chrome.runtime.sendMessage({ action: "process_caption_batch", text: textToSend }, (response) => {
       if (response && response.success && response.terms) {
          response.terms.forEach(term => {
             if (window.mkaShowLiveCard) {
                debugStats.termsRendered++;
                window.mkaShowLiveCard(term);
             }
          });
       }
    });
  }
}

// Health check loop
setInterval(() => {
  chrome.runtime.sendMessage({ action: "health_check" }, (response) => {
    if (!response || !response.online) {
      isMonitoringPaused = true;
      updateDebugState();
    } else {
      isMonitoringPaused = false;
    }
  });
}, 5000);

// Flush API batch
setInterval(flushBatch, 5000); 

// Initial debug state
setTimeout(() => updateDebugState(""), 1000);
