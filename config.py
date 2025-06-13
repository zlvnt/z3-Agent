import os
from dotenv import load_dotenv

load_dotenv()

# Token & API Key
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "1234z")

PERSONALITY_PATH = os.getenv("PERSONALITY_PATH", "personality1.json")
CONVERSATIONS_PATH = os.getenv("CONVERSATIONS_PATH", "conversations.json")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")