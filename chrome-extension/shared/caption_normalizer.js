// chrome-extension/shared/caption_normalizer.js

const NORMALIZATION_MAP = {
  "apa": "api",
  "land graph": "LangGraph",
  "lang graph": "LangGraph",
  "open telemetry": "OpenTelemetry",
  "crew ai": "CrewAI",
  "fast api": "FastAPI",
  "back end": "backend",
  "front end": "frontend",
  "machine learning": "Machine Learning",
  "deep learning": "Deep Learning",
  "cubeernetes": "Kubernetes",
  "kubernates": "Kubernetes",
  "docker compose": "Docker Compose",
  "postgress": "PostgreSQL"
};

function normalizeCaptionText(text) {
  let normalized = text;
  const textLower = text.toLowerCase();
  
  // Check for existing tech context in the raw text to prevent false positive normalizations
  const hasTechContext = TECH_CONTEXT.some(tech => textLower.includes(tech.toLowerCase()));
  
  for (const [key, value] of Object.entries(NORMALIZATION_MAP)) {
    // Risky acronyms like "apa" should only be normalized if we are already in a technical context
    if (key === "apa" && !hasTechContext) {
      continue;
    }
    
    const regex = new RegExp(`\\b${key}\\b`, 'gi');
    if (normalized.match(regex)) {
      console.log(`[NORMALIZED] ${key} -> ${value}`);
      normalized = normalized.replace(regex, value);
    }
  }
  
  return normalized;
}
