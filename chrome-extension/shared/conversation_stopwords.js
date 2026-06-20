// chrome-extension/shared/conversation_stopwords.js

const STOPWORDS = [
  "hello", "hi", "hey", "guys", "team", "everyone", "thanks", "thank",
  "please", "welcome", "meeting", "call", "project", "work", "worked",
  "working", "fix", "fixed", "checking", "check", "send", "sent", "cost",
  "budget", "plan", "planning", "yesterday", "today", "tomorrow", "morning",
  "afternoon", "evening", "week", "month", "year", "okay", "ok", "fine",
  "good", "better", "best", "issue", "problem", "update", "discussion", "notes"
];

const COMMON_NAMES = [
  "rahul", "vetrivel", "john", "alex", "mike", "david", "robert", "sarah"
];

const TECH_CONTEXT = [
  "api", "backend", "frontend", "database", "docker", "kubernetes", "deployment",
  "server", "cloud", "microservice", "terraform", "aws", "ec2", "s3", "vpc",
  "iam", "redis", "postgresql", "kafka", "rabbitmq", "langgraph", "crewai",
  "opentelemetry", "agno", "python", "fastapi", "llm", "telemetry", "trace",
  "sql", "javascript", "agent"
];

const SHORT_WHITELIST = [
  "API", "SQL", "AWS", "JWT", "CPU", "GPU", "ML", "AI", "NLP", "LLM"
];

const WHITELIST = [
  "API", "REST API", "FastAPI", "LangGraph", "CrewAI", "OpenTelemetry", "Agno",
  "Docker", "Docker Compose", "Kubernetes", "Redis", "PostgreSQL", "Kafka",
  "RabbitMQ", "Terraform", "AWS", "EC2", "S3", "IAM", "VPC", "CI/CD", "GitHub Actions"
];
