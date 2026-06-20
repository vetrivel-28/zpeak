// scripts/test_whitelist.js
const fs = require('fs');
const path = require('path');

const stopwordsPath = path.join(__dirname, '../chrome-extension/shared/conversation_stopwords.js');
let stopwordsCode = fs.readFileSync(stopwordsPath, 'utf8');

// Convert const to var so eval leaks them to the outer scope
stopwordsCode = stopwordsCode.replace(/const /g, 'var ');
eval(stopwordsCode);

const expectedTerms = [
  "API",
  "LangGraph",
  "OpenTelemetry",
  "CrewAI",
  "FastAPI",
  "Docker",
  "Kubernetes"
];

console.log("=== WHITELIST VERIFICATION ===");
let allPassed = true;

expectedTerms.forEach(term => {
  const isWhitelisted = WHITELIST.some(w => w.toLowerCase() === term.toLowerCase());
  if (isWhitelisted) {
    console.log(`[PASS] ${term} is explicitly whitelisted.`);
  } else {
    console.log(`[FAIL] ${term} is NOT whitelisted!`);
    allPassed = false;
  }
});

if (allPassed) {
  console.log("All critical terms resolve perfectly and bypass fuzzy filtering.");
} else {
  process.exit(1);
}
