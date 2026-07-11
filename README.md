# ZPEAK - Meeting Knowledge Assistant

> A real-time Chrome Extension that detects technical jargon from Google Meet captions and instantly explains it using a FastAPI backend and an intelligent knowledge base.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-orange)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Overview

Technical meetings often contain unfamiliar terminology such as **LangGraph**, **OpenTelemetry**, **Docker**, **Kubernetes**, or **Random Forest**. Looking up these terms interrupts the meeting and reduces productivity.

**ZPEAK** solves this problem by monitoring live meeting captions, detecting technical concepts in real time, and displaying concise explanations through a floating overlay.

The project combines deterministic entity recognition, fuzzy matching, and an extensible knowledge base to deliver fast and accurate explanations while minimizing false positives.

---

## Features

- Real-time Google Meet caption monitoring
- Chrome Extension (Manifest V3)
- Floating explanation overlay
- FastAPI backend
- SQLite knowledge base
- Deterministic phrase matching
- Multi-word technical entity recognition
- RapidFuzz-based fuzzy matching
- LLM fallback for unknown technical terms
- Low-latency processing
- Developer debugging and performance logging

---

## Demo

### Live Detection

```
Speaker:
"The LangGraph deployment failed in Kubernetes."

Detected:

✓ LangGraph
✓ Deployment
✓ Kubernetes
```

---

### Speech-to-Text Correction

Google Meet Caption:

```
Land Graph
Open Telemetry
Fast AP
```

Automatically recognized as

```
LangGraph
OpenTelemetry
FastAPI
```

using fuzzy matching.

---

## Architecture

```
Google Meet Captions
          │
          ▼
 Chrome Extension
          │
          ▼
 Caption Processing
          │
          ▼
 Exact Phrase Matching
          │
          ▼
 RapidFuzz Entity Matching
          │
          ▼
 SQLite Knowledge Base
          │
     Unknown Term?
       /        \
     Yes        No
      │          │
      ▼          ▼
   Ollama LLM   Return Definition
      │
      ▼
 Quality Validation
      │
      ▼
 Save Knowledge
      │
      ▼
 Floating Overlay
```

---

## Technology Stack

### Frontend

- Chrome Extension (Manifest V3)
- JavaScript
- HTML
- CSS

### Backend

- Python
- FastAPI
- SQLite
- RapidFuzz

### AI / NLP

- Ollama
- Deterministic Entity Recognition
- Fuzzy Matching
- Technical Phrase Detection

---

## Folder Structure

```
zpeak/

├── api/
│   ├── routers/
│   ├── services.py
│   ├── schemas.py
│   └── main.py
│
├── chrome-extension/
│   ├── background.js
│   ├── popup.js
│   ├── popup.html
│   ├── manifest.json
│   ├── content/
│   └── shared/
│
├── database/
│   └── terms.db
│
├── shared/
│
├── detect_terms.py
├── fast_extractor.py
├── knowledge_manager.py
├── llm_extractor.py
├── llm_service.py
├── stopwords.py
├── technical_phrases.py
├── technical_validator.py
├── knowledge_quality.py
│
├── requirements.txt
└── README.md
```

---

## How It Works

### Step 1

Google Meet generates live captions.

↓

### Step 2

The Chrome Extension captures newly appearing caption text.

↓

### Step 3

Technical entities are identified using:

- Exact phrase matching
- Multi-word entity detection
- RapidFuzz fuzzy matching

↓

### Step 4

Known terms are retrieved instantly from SQLite.

↓

### Step 5

Unknown terms are validated using a local LLM.

↓

### Step 6

Validated explanations appear in a floating overlay.

---

## Example

Input

```
The LangGraph deployment failed in Kubernetes.
OpenTelemetry traces show API latency.
```

Output

| Term | Category |
|------|----------|
| LangGraph | AI Framework |
| Deployment | DevOps |
| Kubernetes | Cloud |
| OpenTelemetry | Observability |
| API | Backend |

---

## Performance

Current optimizations include

- Exact phrase lookup
- Longest-phrase-first extraction
- RapidFuzz entity correction
- Multi-word entity protection
- Duplicate caption suppression
- Low-latency FastAPI backend
- SQLite caching

---

## Installation

Clone the repository

```bash
git clone https://github.com/vetrivel-28/zpeak.git

cd zpeak
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run FastAPI

```bash
uvicorn api.main:app --reload
```

Open

```
http://localhost:8000/docs
```

---

## Chrome Extension

1. Open Chrome

2. Go to

```
chrome://extensions
```

3. Enable

```
Developer Mode
```

4. Click

```
Load unpacked
```

5. Select

```
chrome-extension/
```

6. Join a Google Meet session

7. Enable captions

8. Start speaking

The extension will automatically display explanations for detected technical terms.

---

## Future Roadmap

- Meeting summaries
- Action item extraction
- Meeting history
- Multi-platform support (Zoom, Microsoft Teams)
- Export to PDF
- Personal glossary
- Team-specific technical dictionaries
- Analytics dashboard

---

## Author

**Vetrivel A**

M.Sc. Data Science Student

GitHub

https://github.com/vetrivel-28

LinkedIn

https://www.linkedin.com/in/vetrivel28/

---

## License

This project is licensed under the MIT License.streamlit run app.py
```

Run API:
```bash
uvicorn api.main:app --reload
```
