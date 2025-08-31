from pydantic import BaseModel, Field
from typing import Dict, Any

# --- Onboarding Schemas ---
class LocationDatapoint(BaseModel):
    user_id: str
    lat: float
    lon: float

class BehavioralDatapoint(BaseModel):
    user_id: str
    kinetic_data: Dict[str, Any] = Field(..., example={"typing_speed_wpm": 65, "mouse_speed_pps": 250})

# --- Alert Schema ---
class AlertPayload(BaseModel):
    alert_type: str = Field(..., description="The type of the alert, e.g., 'Geo-Fence OTP Failure'.")
    user_id: str = Field(..., description="The unique identifier for the user.")
    event_data: Dict[str, Any] = Field(..., description="A flexible dictionary containing alert-specific data.")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_type": "Geo-Fence OTP Failure",
                "user_id": "user_12345",
                "event_data": {
                    "otp_location": {"lat": 28.6139, "lon": 77.2090},
                    "sim_location": {"lat": 19.0760, "lon": 72.8777}
                }
            }
        }

class UserCreate(BaseModel):
    email: str
    password: str

class UserInDB(BaseModel):
    email: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str