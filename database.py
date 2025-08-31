# database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

log = logging.getLogger(__name__)
load_dotenv()

MONGO_DB_URI = os.getenv("MONGO_DB_URI")

if not MONGO_DB_URI:
    log.critical("FATAL: MONGO_DB_URI is not set in the .env file.")
    raise ValueError("MONGO_DB_URI is not configured.")

try:
    client = MongoClient(MONGO_DB_URI)
    # The database name is part of the URI, but we can also access it like this
    # The actual database and collections are created lazily on first use
    db = client.get_database() 
    log.info("Successfully connected to MongoDB.")
except Exception as e:
    log.critical(f"FATAL: Could not connect to MongoDB: {e}", exc_info=True)
    raise

# We can define our collections here for easy access
user_collection = db["users"]