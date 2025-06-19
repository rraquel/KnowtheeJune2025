import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/talent") 