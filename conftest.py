import os


os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("GROQ_API_BASE", "https://api.groq.com")
os.environ.setdefault("GROQ_MODEL", "test-model")
