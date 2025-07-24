import sqlite3
import json
import time
from sentence_transformers import SentenceTransformer
import numpy as np
from logger_config import log

# --- Database and Model Setup ---
DB_PATH = "memory/user_profiles.db"
# This model is loaded once and reused, which is efficient.
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_db_connection():
    """
    Establishes and returns a database connection.
    CRITICAL FIX: Sets `check_same_thread=False` for FastAPI compatibility.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Creates the necessary tables if they don't exist."""
    log.info("Initializing user profile database at 'memory/user_profiles.db'...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Table for user location history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS location_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL
        )
        """)
        # Table for user behavioral profiles (stores embeddings as JSON)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavioral_profiles (
            user_id TEXT PRIMARY KEY,
            embeddings_json TEXT NOT NULL
        )
        """)
        conn.commit()
        conn.close()
        log.info("User profile database initialized successfully.")
    except Exception as e:
        log.critical(f"FATAL: Could not initialize the database at {DB_PATH}: {e}", exc_info=True)
        # This is a fatal error, so we raise it to stop the application startup.
        raise

def add_location_datapoint(user_id: str, lat: float, lon: float) -> dict:
    """Adds a new timestamped location datapoint for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO location_history (user_id, timestamp, lat, lon) VALUES (?, ?, ?, ?)",
            (user_id, time.time(), lat, lon)
        )
        conn.commit()
        conn.close()
        # Demoted to DEBUG as this is a frequent, operational event.
        log.debug(f"Added location datapoint for user '{user_id}'.")
        return {"status": "success", "message": "Location datapoint added."}
    except Exception as e:
        log.error(f"Failed to add location datapoint for user '{user_id}': {e}", exc_info=True)
        return {"error": str(e)}

def add_behavioral_datapoint(user_id: str, kinetic_data: dict) -> dict:
    """Adds a new behavioral data point to a user's profile."""
    try:
        # Convert structured kinetic data into a descriptive sentence for better embedding quality.
        kinetic_string = f"typing speed: {kinetic_data.get('typing_speed_wpm', 0)} words per minute, " \
                         f"mouse speed: {kinetic_data.get('mouse_speed_pps', 0)} pixels per second"
        
        embedding = embedding_model.encode(kinetic_string).tolist()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT embeddings_json FROM behavioral_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            # User exists, append new embedding and keep the list at a max size.
            embeddings_list = json.loads(row['embeddings_json'])
            embeddings_list.append(embedding)
            max_embeddings = 20 # Keep the profile relevant to recent behavior
            embeddings_list = embeddings_list[-max_embeddings:]
            new_embeddings_json = json.dumps(embeddings_list)
            cursor.execute(
                "UPDATE behavioral_profiles SET embeddings_json = ? WHERE user_id = ?",
                (new_embeddings_json, user_id)
            )
        else:
            # This is the first data point for a new user.
            new_embeddings_json = json.dumps([embedding])
            cursor.execute(
                "INSERT INTO behavioral_profiles (user_id, embeddings_json) VALUES (?, ?)",
                (user_id, new_embeddings_json)
            )
        conn.commit()
        conn.close()
        log.debug(f"Added behavioral datapoint for user '{user_id}'.")
        return {"status": "success", "message": "Behavioral datapoint added."}
    except Exception as e:
        log.error(f"Failed to add behavioral datapoint for user '{user_id}': {e}", exc_info=True)
        return {"error": str(e)}