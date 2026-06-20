import re

COMMON_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "let", "let's", "yes", "no", "yeah", "nope", "okay", "ok", "right", "sure", "hey", "guys"
}

CONTRACTIONS = {
    "i'll", "i've", "we're", "don't", "can't", "it's", "that's", "we'll", "you'll", "isn't", "aren't",
    "wasn't", "weren't", "haven't", "hasn't", "hadn't", "won't", "wouldn't", "doesn't", "didn't",
    "couldn't", "shouldn't", "mightn't", "mustn't", "would've", "should've", "could've", "might've",
    "must've", "who's", "what's", "where's", "when's", "why's", "how's", "they'll", "he'll", "she'll",
    "they're", "they've", "you're", "you've", "i'm", "let's", "there's", "here's"
}

PEOPLE_WORDS = {
    "person", "people", "man", "woman", "guy", "girl", "boy", "child", "children",
    "he", "she", "him", "her", "they", "them", "their", "theirs", "we", "us", "our",
    "vetrivel", "rahul", "john", "jane", "alice", "bob", "mike", "sarah", "priya", "kumar"
}

TIME_WORDS = {
    "yesterday", "today", "tomorrow", "now", "later", "soon", "morning", "afternoon",
    "evening", "night", "day", "week", "month", "year", "hour", "minute", "second",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "am", "pm"
}

LOCATION_WORDS = {
    "library", "office", "home", "building", "room", "floor", "street", "city",
    "country", "state", "world", "place", "location", "area", "region"
}

GENERIC_VERBS = {
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "make", "made", "take", "took", "get", "got", "go", "went", "come", "came",
    "see", "saw", "know", "knew", "think", "thought", "say", "said", "tell", "told",
    "ask", "asked", "work", "worked", "try", "tried", "leave", "left", "call", "called",
    "need", "needed", "feel", "felt", "become", "became", "leave", "put", "mean", "keep",
    "let", "begin", "seem", "help", "talk", "turn", "start", "might", "show", "hear",
    "play", "run", "move", "like", "live", "believe", "hold", "bring", "happen",
    "write", "provide", "sit", "stand", "lose", "pay", "meet", "include", "continue",
    "set", "learn", "change", "lead", "understand", "watch", "follow", "stop", "create",
    "speak", "read", "allow", "add", "spend", "grow", "open", "walk", "win", "offer",
    "remember", "love", "consider", "appear", "buy", "wait", "serve", "die", "send",
    "expect", "build", "stay", "fall", "cut", "reach", "kill", "remain", "suggest",
    "raise", "pass", "sell", "require", "report", "decide", "pull", "failed", "discuss",
    "discussed", "fail", "success", "succeed"
}

GENERIC_ADJECTIVES = {
    "good", "bad", "better", "worse", "best", "worst", "great", "small", "big", "large",
    "little", "long", "short", "high", "low", "old", "new", "young", "early", "late",
    "important", "public", "private", "true", "false", "real", "fake", "right", "wrong",
    "free", "full", "empty", "hard", "soft", "easy", "difficult", "simple", "complex",
    "clear", "dark", "light", "heavy", "strong", "weak", "fast", "slow", "early", "late",
    "hot", "cold", "warm", "cool", "clean", "dirty", "dry", "wet", "fine", "nice",
    "beautiful", "ugly", "happy", "sad", "angry", "calm", "excited", "bored", "tired",
    "sick", "healthy", "poor", "rich", "cheap", "expensive", "safe", "dangerous"
}

CONVERSATION_WORDS = {
    "meeting", "discussion", "chat", "talk", "call", "lunch plans", "lunch", "dinner",
    "breakfast", "food", "drink", "coffee", "tea", "water", "performance measurement",
    "dataset balance", "notes", "share", "check", "issue", "problem", "task", "update"
}

GENERIC_NOUNS = {
    "graph", "land", "telemetry", "learning", "machine", "cloud", "system", 
    "project", "meeting", "subject", "plan", "font", "english",
    "random", "boost", "model", "cluster", "pipeline", "dashboard",
    "data", "rest", "deployment", "workflow", "system", "forest", "linear", "distal"
}

SHORT_WHITELIST = {
    "api", "sql", "aws", "jwt", "cpu", "gpu", "ml", "ai", "nlp", "llm", "cnn", "rnn"
}

def check_rejection(term):
    """
    Checks if a term should be rejected and returns (is_rejected: bool, reason: str).
    """
    if not term:
        return True, "empty string"
        
    term_lower = term.lower()
    
    # 1. Contraction Filter
    if term_lower in CONTRACTIONS or "'" in term_lower:
        # e.g., "I'll", "Let's"
        return True, "contraction"
        
    clean_term = "".join(c for c in term_lower if c.isalnum() or c.isspace()).strip()
    
    # 2. Time Token Filter
    if re.fullmatch(r'\d{1,2}(:\d{2})?\s*(am|pm)', term_lower):
        return True, "time token"
    if clean_term in TIME_WORDS:
        return True, "time token"
    
    # 3. Person Name Detection
    if clean_term in PEOPLE_WORDS:
        return True, "probable person name"
        
    # 4. Location Filter
    if clean_term in LOCATION_WORDS:
        return True, "location reference"
        
    # 5. Generic Word Filter
    if clean_term in GENERIC_VERBS:
        return True, "generic verb"
    if clean_term in GENERIC_ADJECTIVES:
        return True, "generic adjective"
    if clean_term in COMMON_WORDS:
        return True, "common stopword"
    if clean_term in CONVERSATION_WORDS:
        return True, "conversation word"
    if clean_term in GENERIC_NOUNS:
        return True, "generic noun"
        
    # 6. Short Term Filter (Phase 9.4)
    if len(clean_term) < 4 and clean_term not in SHORT_WHITELIST:
        return True, "short generic term"
        
    return False, ""

def is_stopword(term):
    """
    Legacy wrapper for existing usages. Returns True if rejected.
    """
    is_rejected, _ = check_rejection(term)
    return is_rejected
