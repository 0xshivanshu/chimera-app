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


# --- TOOL SCHEMA DEFINITIONS ---
# This is the modern, structured way to define tools for autogen agents.

investigation_tool_schemas = [
    {
        "type": "function",
        "function": {
            "name": "validate_impossible_travel",
            "description": "Checks if a user's travel between their last known location and the current one is physically possible.",
            "parameters": { "type": "object", "properties": { "user_id": {"type": "string"}, "current_location": {"type": "object"} }, "required": ["user_id", "current_location"] }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_behavioral_anomaly_score",
            "description": "Compares live typing/mouse data to a user's stored profile to detect behavioral changes.",
            "parameters": { "type": "object", "properties": { "user_id": {"type": "string"}, "live_kinetic_data": {"type": "object"} }, "required": ["user_id", "live_kinetic_data"] }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_geo_fence_otp",
            "description": "Calculates the geographic distance between an OTP request and the user's SIM card.",
            "parameters": { "type": "object", "properties": { "otp_location": {"type": "object"}, "sim_location": {"type": "object"} }, "required": ["otp_location", "sim_location"] }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_sms_phishing",
            "description": "Analyzes the text of an SMS to determine if it is a phishing attempt.",
            "parameters": { "type": "object", "properties": { "sms_text": {"type": "string"} }, "required": ["sms_text"] }
        }
    }
]

action_tool_schemas = [
    { "type": "function", "function": { "name": "lock_user_session", "description": "Locks a user's session.", "parameters": { "type": "object", "properties": { "user_id": {"type": "string"}, "reason": {"type": "string"} }, "required": ["user_id", "reason"] } } },
    { "type": "function", "function": { "name": "initiate_step_up_auth", "description": "Initiates multi-factor authentication for a user.", "parameters": { "type": "object", "properties": { "user_id": {"type": "string"}, "reason": {"type": "string"} }, "required": ["user_id", "reason"] } } },
    { "type": "function", "function": { "name": "send_notification", "description": "Sends a notification to a user.", "parameters": { "type": "object", "properties": { "user_id": {"type": "string"}, "message": {"type": "string"}, "level": {"type": "string"} }, "required": ["user_id", "message", "level"] } } },
    { "type": "function", "function": { "name": "log_incident_to_memory", "description": "Logs an incident summary to long-term memory.", "parameters": { "type": "object", "properties": { "summary_text": {"type": "string"} }, "required": ["summary_text"] } } }
]