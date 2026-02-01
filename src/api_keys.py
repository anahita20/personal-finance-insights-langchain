import os
from dotenv import load_dotenv
from pathlib import Path

env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_file)

class GeminiAPIConfig:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
