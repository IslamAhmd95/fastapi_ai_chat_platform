import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
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
