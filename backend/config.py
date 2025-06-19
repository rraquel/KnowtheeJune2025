import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE_URL = f"{BACKEND_URL}/api/talent"

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/knowthee") 