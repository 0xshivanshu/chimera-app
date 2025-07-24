import faiss
import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from logger_config import log
from config import API_BASE_URL, CHIMERA_API_KEY

# --- Setup for Memory and Models ---
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
VECTOR_DIMENSION = embedding_model.get_sentence_embedding_dimension()

FAISS_INDEX_PATH = "memory/faiss_index.bin"
INCIDENT_LOG_PATH = "memory/incident_log.json"

# --- Initialize or Load Memory Components ---
try:
    faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    log.info(f"Loaded existing FAISS index with {faiss_index.ntotal} vectors.")
except RuntimeError:
    log.warning("No FAISS index found. Creating a new one.")
    faiss_index = faiss.IndexFlatL2(VECTOR_DIMENSION)

try:
    with open(INCIDENT_LOG_PATH, 'r', encoding='utf-8') as f:
        incident_log = json.load(f)
    log.info(f"Loaded existing incident log with {len(incident_log)} entries.")
except (FileNotFoundError, json.JSONDecodeError):
    log.warning("No incident log found or log is corrupted. Starting fresh.")
    incident_log = {} # Use a dictionary to map the FAISS index ID to the summary text

def _save_memory():
    """Atomically saves the FAISS index and the incident log."""
    try:
        faiss.write_index(faiss_index, FAISS_INDEX_PATH)
        with open(INCIDENT_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(incident_log, f, indent=2)
    except Exception as e:
        log.error(f"CRITICAL: Failed to save memory to disk: {e}", exc_info=True)


# --- Real, API-Driven Action Tools ---

def _make_internal_api_call(endpoint: str, payload: dict) -> dict:
    """Helper function to make authenticated internal API calls."""
    try:
        if not API_BASE_URL or not CHIMERA_API_KEY:
            raise ValueError("API_BASE_URL and CHIMERA_API_KEY must be configured.")
        
        headers = {"X-API-Key": CHIMERA_API_KEY, "Content-Type": "application/json"}
        response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, json=payload, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.RequestException as e:
        log.error(f"API call to endpoint '{endpoint}' failed: {e}", exc_info=True)
        return {"error": f"Failed to execute action via API. Details: {e}"}

def lock_user_session(user_id: str, reason: str) -> dict:
    """Makes a real API call to an internal endpoint to lock a user's session."""
    log.info(f"Executing REAL action: lock_user_session for user '{user_id}'.")
    payload = {"user_id": user_id, "reason": reason}
    return _make_internal_api_call("/v1/internal/lock_session", payload)

def initiate_step_up_auth(user_id: str, reason: str) -> dict:
    """Makes a real API call to an internal endpoint to request step-up auth."""
    log.info(f"Executing REAL action: initiate_step_up_auth for user '{user_id}'.")
    payload = {"user_id": user_id, "reason": reason}
    return _make_internal_api_call("/v1/internal/step_up_auth", payload)

def send_notification(user_id: str, message: str, level: str) -> dict:
    """Makes a real API call to an internal endpoint to send a notification."""
    log.info(f"Executing REAL action: send_notification to user '{user_id}'.")
    payload = {"user_id": user_id, "message": message, "level": level}
    return _make_internal_api_call("/v1/internal/send_notification", payload)

def log_incident_to_memory(summary_text: str) -> dict:
    """Logs a resolved incident to long-term memory (FAISS + JSON)."""
    try:
        log.info(f"Logging incident to long-term memory: '{summary_text}'")
        embedding = embedding_model.encode([summary_text])
        
        # Add to FAISS index
        new_index_id = faiss_index.ntotal
        faiss_index.add(np.array(embedding, dtype=np.float32))
        
        # Add text summary to our JSON log, mapping the FAISS index ID to the text
        incident_log[str(new_index_id)] = summary_text
        
        # Persist both to disk
        _save_memory()
        
        log.info(f"Successfully logged incident. Total incidents: {faiss_index.ntotal}.")
        return {"status": "success", "message": f"Incident logged. Total incidents: {faiss_index.ntotal}."}
    except Exception as e:
        log.error(f"Failed to log incident to memory: {e}", exc_info=True)
        return {"error": f"Failed to write to memory files. Details: {e}"}