import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Backend Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BACKEND_BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
BACKEND_URL = f"{BACKEND_BASE_URL}/api/talent"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/knowthee")

# Frontend Configuration
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "localhost")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "8501")
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"

# API Configuration
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Docker-specific overrides
if os.getenv("DOCKER_ENV"):
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/knowthee")
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0") 