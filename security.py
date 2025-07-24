from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import CHIMERA_API_KEY
import logging

log = logging.getLogger(__name__)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_from_header: str = Security(api_key_header)):
    """Validates the API key from the request header against the one in the environment."""
    if not CHIMERA_API_KEY:
        log.critical("FATAL: API Key is not configured on the server. The application is insecure.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server is improperly configured.")
    
    if api_key_from_header and api_key_from_header == CHIMERA_API_KEY:
        return api_key_from_header
    else:
        log.warning("Unauthorized access attempt: Invalid or missing API Key.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key.")