import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the .env file at the project root.
load_dotenv()

# --- API and Security Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
CHIMERA_API_KEY = os.getenv("CHIMERA_API_KEY")

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- Ollama and Model Configuration ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL")
INQUISITOR_MODEL = os.getenv("INQUISITOR_MODEL")
FORGER_MODEL = os.getenv("FORGER_MODEL")
ADVERSARY_MODEL = os.getenv("ADVERSARY_MODEL")

# --- Autogen LLM Configuration List ---
config_list = [
    {"model": model, "base_url": OLLAMA_BASE_URL, "api_type": "open_ai", "api_key": "ollama"}
    for model in [ORCHESTRATOR_MODEL, INQUISITOR_MODEL, FORGER_MODEL, ADVERSARY_MODEL] if model
]

def get_llm_config_for_model(model_name: str):
    """Finds the configuration for a specific model."""
    if not model_name:
        raise ValueError("Model name cannot be empty.")
    for config in config_list:
        if config["model"] == model_name:
            return {"config_list": [config]}
    raise ValueError(f"Model '{model_name}' not found in configuration.")

# --- Prompt Loading ---
def load_prompt(filename: str) -> str:
    """Loads a prompt from the prompts/ directory."""
    prompt_path = Path("prompts") / filename
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.critical(f"FATAL: Prompt file '{filename}' not found. The application cannot start without it.", exc_info=True)
        raise
    except Exception as e:
        logging.critical(f"FATAL: Failed to read prompt file '{filename}': {e}", exc_info=True)
        raise

ORCHESTRATOR_PROMPT = load_prompt("orchestrator.txt")
INQUISITOR_PROMPT = load_prompt("inquisitor.txt")
ADVERSARY_PROMPT = load_prompt("adversary.txt")