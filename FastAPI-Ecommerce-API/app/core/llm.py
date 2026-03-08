"""
Configuration module for the multi-agent system.
Handles LLM initialization.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_litellm import ChatLiteLLM

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH, override=True)

DEFAULT_MODEL = os.getenv("LLM_MODEL_ID")

if not DEFAULT_MODEL:
    raise ValueError("❌ DEFAULT_MODEL is missing in your .env file")

# --- LLM Configuration ---
try:
    llm = ChatLiteLLM(
        model=DEFAULT_MODEL,
        temperature=0.1,
        max_tokens=4096,
        timeout=20,
    )
    print("✅ LiteLLM configuration successful")

except Exception as e:
    raise RuntimeError(f"❌ LLM configuration failed: {e}")

__all__ = ['llm']