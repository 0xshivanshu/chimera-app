import json
import requests
import numpy as np
from logger_config import log
from tools.action_tools import faiss_index, incident_log, embedding_model
from config import ADVERSARY_MODEL, OLLAMA_BASE_URL, API_BASE_URL, CHIMERA_API_KEY

def query_past_incidents(query_text: str, top_k: int = 3) -> dict:
    """
    Searches the FAISS vector index for past incidents similar to the query text.
    Returns the original summary text for the LLM to analyze.
    """
    log.info(f"Adversary querying past incidents with: '{query_text}'")
    try:
        if faiss_index.ntotal == 0:
            return {"status": "success", "results": "No incidents logged in memory yet."}
            
        query_embedding = embedding_model.encode([query_text])
        # Ensure top_k is not greater than the number of items in the index
        k = min(top_k, faiss_index.ntotal)
        distances, indices = faiss_index.search(np.array(query_embedding, dtype=np.float32), k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            # The key in incident_log is a string
            if str(idx) in incident_log:
                results.append({
                    "incident_summary": incident_log[str(idx)],
                    "similarity_score": 1 - distances[0][i] # Convert L2 distance to a similarity score for context
                })
        return {"status": "success", "results": results}
    except Exception as e:
        log.error(f"Error querying past incidents: {e}", exc_info=True)
        return {"error": str(e)}

def craft_synthetic_attack_payload(description: str) -> dict:
    """
    Uses the powerful Adversary LLM (via Ollama) to generate a JSON payload for a synthetic attack.
    """
    log.info(f"Adversary crafting synthetic attack for description: '{description}'")
    prompt = f"""You are a cybersecurity testing expert. Based on the following attack description, generate a valid JSON payload that conforms to the project's AlertPayload schema. The JSON output MUST be a single, valid JSON object and nothing else. Attack Description: "{description}" """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/chat/completions",
            json={
                "model": ADVERSARY_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "response_format": {"type": "json_object"}
            },
            timeout=90
        )
        response.raise_for_status()
        payload_str = response.json()['choices'][0]['message']['content']
        payload_json = json.loads(payload_str)
        return {"status": "success", "payload": payload_json}
    except Exception as e:
        log.error(f"Error crafting synthetic attack payload: {e}", exc_info=True)
        return {"error": str(e)}

def execute_test_scenario(payload: dict) -> dict:
    """
    Executes a test scenario by sending a crafted payload to the main /v1/alert endpoint.
    """
    log.info("Adversary executing test scenario...")
    log.debug(f"Executing with payload: {json.dumps(payload, indent=2)}")
    try:
        headers = {"X-API-Key": CHIMERA_API_KEY, "Content-Type": "application/json"}
        response = requests.post(f"{API_BASE_URL}/v1/alert", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return {"status": "success", "result": "Test scenario successfully injected into the system."}
    except requests.RequestException as e:
        log.error(f"Error executing test scenario: {e}", exc_info=True)
        return {"error": str(e)}