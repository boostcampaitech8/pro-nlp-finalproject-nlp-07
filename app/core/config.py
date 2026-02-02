import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")
API_V1_STR = "/api/v1"
PROJECT_NAME = "Chatbot API"
