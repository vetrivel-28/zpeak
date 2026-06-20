# Chrome Extension MVP Testing Guide

## 1. Installation (Developer Mode)

1. Open Google Chrome.
2. Navigate to `chrome://extensions/`.
3. Enable **Developer mode** in the top right corner.
4. Click **Load unpacked** in the top left.
5. Select the `D:\zpeak\meeting-term-explainer\chrome-extension` directory.
6. The extension will appear with the generated Teal/Indigo icon.

## 2. Testing the Backend Health Check

1. Stop your FastAPI backend server if it is running.
2. Open the Extension Popup.
3. You should immediately see a red banner: **Backend Offline - Please start: `uvicorn api.main:app --reload`**.
4. Start the backend: `uvicorn api.main:app --reload`
5. Close and reopen the popup. The banner should be gone.

## 3. Testing Popup Search (Feature 2)

1. Open the popup.
2. Ensure you are on the **Search** tab.
3. Type `LangGraph` and hit Enter or click **Explain**.
4. A card should appear with the definition, categorized as Local DB or AI Extracted.
5. Try typing a fake term like `HyperVectorAgentMeshX9000`. It should show a strict error message without stalling on an LLM call.

## 4. Testing Transcript Analyzer (Feature 3)

1. Open the popup and click the **Analyzer** tab.
2. Paste a few sentences into the large text box:
   > "We should use LangGraph to orchestrate our new LLM workflow. Maybe we can stream the traces back to OpenTelemetry for debugging."
3. Click **Analyze Transcript**.
4. The loader will spin. Once done, an accordion menu will appear separating:
   - Known Terms
   - New Terms
   - Unknown Terms
5. Click the accordion headers to expand/collapse the definitions.

## 5. Testing Right-Click Tooltip (Feature 1 & 4)

1. Open a random webpage (e.g., Wikipedia, or a basic text file loaded in Chrome).
2. Highlight a technical word, for example: `Django`.
3. Right-click the highlighted word.
4. Select **Explain Term** from the native context menu.
5. Without the page reloading, a dark glassmorphic tooltip should fade in directly under your mouse cursor, showing the word, a loading indicator, and then dynamically swapping to the definition.
6. Click anywhere else on the page to dismiss the tooltip.

## 6. Testing Settings (Feature 8)

1. Right-click the extension icon in your Chrome toolbar.
2. Click **Options**.
3. Change the backend URL to a random URL and hit **Save**.
4. The extension will now attempt to route API calls to that URL. (Revert it to `http://127.0.0.1:8000` to restore functionality).

## 7. Testing Cache (Feature 6)

1. Search for `OpenTelemetry` in the popup. Note the slight delay (if it goes to LLM) or instant return (if DB).
2. Search for it again. The background script caches successful lookups in `chrome.storage.local` with a 24-hour TTL, so the second query should skip the API entirely.
