import os
import json
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    _default_cors_origins = '["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080"]'
    try:
        CORS_ORIGINS = json.loads(
            os.getenv("CORS_ORIGINS", _default_cors_origins))
    except json.JSONDecodeError:
        # Fallback to safe defaults if env var contains invalid JSON
        CORS_ORIGINS = json.loads(_default_cors_origins)

    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    RATE_LIMIT_TIMES = int(os.getenv("RATE_LIMIT_TIMES", 5))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # seconds
    AI_USAGE_LIMIT = int(os.getenv("AI_USAGE_LIMIT", 10))
    RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
    RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
    TESTING = os.getenv("TESTING", "False").lower() == "true"


settings = Settings()
