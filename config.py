import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Load all configs from .env ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
CHIMERA_API_KEY = os.getenv("CHIMERA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- Model Name Definitions ---
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL")
INQUISITOR_MODEL = os.getenv("INQUISITOR_MODEL")
FORGER_MODEL = os.getenv("FORGER_MODEL")
ADVERSARY_MODEL = os.getenv("ADVERSARY_MODEL")

# --- Build the Master Configuration List ---
config_list = []
all_models = {
    ORCHESTRATOR_MODEL, INQUISITOR_MODEL,
    FORGER_MODEL, ADVERSARY_MODEL
}

for model in all_models:
    if not model:
        continue

    # If the model is from Groq, configure it for the Groq API
    if "llama-3.1" in model:
        if not GROQ_API_KEY:
            logging.warning(f"Model '{model}' is a Groq model, but GROQ_API_KEY is not set.")
            continue
        config_list.append({
            "model": model,
            "api_key": GROQ_API_KEY,
            "base_url": "https://api.groq.com/openai/v1"
        })
    # Otherwise, configure it as a local Ollama model
    else:
        config_list.append({
            "model": model,
            "base_url": OLLAMA_BASE_URL,
            "api_type": "open_ai",
            "api_key": "ollama"
        })

def get_llm_config_for_model(model_name: str):
    """Finds the configuration for a specific model from the master list."""
    if not model_name:
        raise ValueError("Model name cannot be empty.")
    for config in config_list:
        if config.get("model") == model_name:
            return {"config_list": [config]}
    raise ValueError(f"Model '{model_name}' not found in any configuration. Check your .env and config.py.")

# --- Prompt Loading ---
def load_prompt(filename: str) -> str:
    """Loads a prompt from the prompts/ directory."""
    prompt_path = Path("prompts") / filename
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.critical(f"FATAL: Prompt file '{filename}' not found.", exc_info=True)
        raise
    except Exception as e:
        logging.critical(f"FATAL: Failed to read prompt file '{filename}': {e}", exc_info=True)
        raise

ORCHESTRATOR_PROMPT = load_prompt("orchestrator.txt")
INQUISITOR_PROMPT = load_prompt("inquisitor.txt")
ADVERSARY_PROMPT = load_prompt("adversary.txt")