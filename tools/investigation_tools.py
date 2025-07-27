import json
import time
from typing import Dict, Any
from geopy.distance import great_circle
from transformers import pipeline
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from logger_config import log
from .onboarding_tools import get_db_connection, embedding_model

# --- Tool 1: Geo-Fence OTP Validation ---
def check_geo_fence_otp(otp_location: Dict[str, float], sim_location: Dict[str, float]) -> Dict[str, Any]:
    """Calculates the distance between OTP request and SIM location with robust error handling."""
    try:
        loc1 = (otp_location.get('lat'), otp_location.get('lon'))
        loc2 = (sim_location.get('lat'), sim_location.get('lon'))
        # Ensure all coordinates are valid numbers before calculation.
        if not all(isinstance(coord, (int, float)) for coord in loc1 + loc2):
            return {"error": "Invalid or missing lat/lon values provided."}
            
        distance_km = great_circle(loc1, loc2).kilometers
        is_match = distance_km <= 50  # Using a 50km radius to account for inaccuracies.
        log.info(f"Geo-fence check: distance is {distance_km:.2f}km.")
        result = {"status": "success", "distance_km": round(distance_km, 2), "is_match": is_match}
        print(f"DEBUG: GROUND TRUTH from check_geo_fence_otp -> {result}")
        return result

    except Exception as e:
        log.error(f"Error in check_geo_fence_otp: {e}", exc_info=True)
        return {"error": f"Failed to calculate distance. Details: {e}"}

# --- Tool 2: Impossible Travel (DB-Driven) ---
def validate_impossible_travel(user_id: str, current_location: Dict[str, float]) -> Dict[str, Any]:
    """Checks for impossible travel using the user's location history from the SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT lat, lon, timestamp FROM location_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,)
        )
        last_session = cursor.fetchone()
        conn.close()

        if not last_session:
            log.warning(f"No location history for user '{user_id}'. Cannot perform impossible travel check.")
            return {"status": "skipped", "message": "No prior location history for user."}

        current_time = time.time()
        time_elapsed_seconds = current_time - last_session['timestamp']
        
        loc1 = (last_session['lat'], last_session['lon'])
        loc2 = (current_location.get('lat'), current_location.get('lon'))
        if not all(isinstance(coord, (int, float)) for coord in loc1 + loc2):
            return {"error": "Invalid or missing lat/lon values for current location."}

        distance_km = great_circle(loc1, loc2).kilometers
        # Using a generous max travel speed of 800 km/h (commercial flight).
        max_travel_speed_kph = 800
        min_required_time_seconds = (distance_km / max_travel_speed_kph) * 3600 if max_travel_speed_kph > 0 else float('inf')
        # A check to ensure we're not comparing a future event to a past one in a weird clock-skew scenario.
        is_impossible = time_elapsed_seconds < min_required_time_seconds and time_elapsed_seconds > 0

        log.info(f"Impossible travel check for '{user_id}': travel of {distance_km:.2f}km in {time_elapsed_seconds/3600:.2f} hours. Impossible: {is_impossible}")
        result = {
            "status": "success", "is_impossible": is_impossible,
            "details": f"Travel of {distance_km:.2f}km in {time_elapsed_seconds/3600:.2f} hours was deemed {'impossible' if is_impossible else 'possible'}."
        }
        print(f"DEBUG: GROUND TRUTH from validate_impossible_travel -> {result}")
        return result

    except Exception as e:
        log.error(f"Error in validate_impossible_travel for user '{user_id}': {e}", exc_info=True)
        return {"error": str(e)}

# --- Tool 3: Behavioral Anomaly (DB-Profile Driven) ---
def get_behavioral_anomaly_score(user_id: str, live_kinetic_data: dict) -> Dict[str, Any]:
    """
    Calculates a statistical anomaly score by comparing live numerical data to the user's stored SQLite profile.
    This version uses a direct numerical comparison (normalized Euclidean distance).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT kinetic_json FROM behavioral_profiles WHERE user_id = ?", (user_id,))
        profile = cursor.fetchone()
        conn.close()

        min_samples_for_baseline = 5
        if not profile or len(json.loads(profile['kinetic_json'])) < min_samples_for_baseline:
            log.warning(f"Not enough behavioral data for user '{user_id}' to form a reliable baseline.")
            return {"status": "skipped", "message": f"Baseline requires at least {min_samples_for_baseline} data points."}
        
        baseline_data = [np.array([d['typing_speed_wpm'], d['mouse_speed_pps']]) for d in json.loads(profile['kinetic_json'])]
        baseline_data = np.array(baseline_data)

        profile_mean = np.mean(baseline_data, axis=0)
        profile_std = np.std(baseline_data, axis=0)
        
        profile_std[profile_std == 0] = 1 

        live_data = np.array([
            live_kinetic_data.get('typing_speed_wpm', 0),
            live_kinetic_data.get('mouse_speed_pps', 0)
        ])

        z_scores = (live_data - profile_mean) / profile_std
        anomaly_score = np.linalg.norm(z_scores)
        
        anomaly_threshold = 3.0 # A common threshold for Z-scores (roughly 99.7% of data)
        is_anomalous = anomaly_score > anomaly_threshold        
        log.info(f"Behavioral anomaly check for '{user_id}': score {anomaly_score:.3f}. Anomalous: {is_anomalous}")
        result = {"status": "success", "is_anomalous": is_anomalous, "anomaly_score": round(anomaly_score, 3)}
        print(f"DEBUG: GROUND TRUTH from get_behavioral_anomaly_score -> {result}")
        return result

    except Exception as e:
        log.error(f"Error in get_behavioral_anomaly_score for user '{user_id}': {e}", exc_info=True)
        return {"error": str(e)}
    
    
# --- Tool 4: SMS Phishing Analysis (Pre-trained Model) ---
try:
    # Load model once on module import for efficiency.
    sms_classifier = pipeline("text-classification", model="mrm8488/bert-tiny-finetuned-sms-spam-detection")
except Exception as e:
    log.critical(f"FATAL: Could not load the SMS classification model. This tool will be disabled. Error: {e}", exc_info=True)
    sms_classifier = None

def analyze_sms_phishing(sms_text: str) -> Dict[str, Any]:
    """Analyzes SMS text for phishing using a pre-trained Hugging Face model."""
    if sms_classifier is None:
        log.error("SMS classification tool was called, but the model is not available.")
        return {"error": "SMS classification model is not available."}
    try:
        if not sms_text or not isinstance(sms_text, str):
            return {"error": "Invalid or empty SMS text provided."}
        result = sms_classifier(sms_text)[0]
        is_phishing = result['label'] == 'LABEL_1'
        confidence = result['score']
        log.info(f"SMS analysis complete. Phishing: {is_phishing} with confidence {confidence:.2f}.")
        result_dict = {"status": "success", "is_phishing": is_phishing, "confidence": round(confidence, 3)}
        print(f"DEBUG: GROUND TRUTH from analyze_sms_phishing -> {result_dict}")
        return result_dict
    except Exception as e:
        log.error(f"Error during SMS phishing analysis: {e}", exc_info=True)
        return {"error": str(e)}