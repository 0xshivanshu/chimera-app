# api.py (Your Definitive Version + Authentication Logic)
from datetime import timedelta

import autogen
import json
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, APIRouter, status
from pydantic import BaseModel

# --- Chimera Core Imports ---
from logger_config import log, setup_logging
from schemas import AlertPayload, LocationDatapoint, BehavioralDatapoint, UserCreate # Added UserCreate
from security import get_api_key
from config import (
    get_llm_config_for_model, ORCHESTRATOR_MODEL, INQUISITOR_MODEL,
    ORCHESTRATOR_PROMPT, INQUISITOR_PROMPT, investigation_tool_schemas, action_tool_schemas
)
# --- Tool Imports ---
from tools.onboarding_tools import initialize_database, add_location_datapoint, add_behavioral_datapoint
from tools.investigation_tools import (
    check_geo_fence_otp, validate_impossible_travel, get_behavioral_anomaly_score, analyze_sms_phishing
)
from tools.action_tools import (
    lock_user_session, initiate_step_up_auth, send_notification, log_incident_to_memory
)

# --- NEW: Auth Imports ---
from database import user_collection
from auth_utils import get_password_hash, verify_password, create_access_token

# =================================================================
# FastAPI App Initialization and Lifecycle
# =================================================================
app = FastAPI(title="Project Chimera API", version="3.2.0")

@app.on_event("startup")
async def startup_event():
    setup_logging()
    log.info("---- Project Chimera Server Starting Up ----")
    # NOTE: We remove initialize_database() as it's for SQLite.
    # MongoDB connection is now handled in database.py
    log.info("Startup complete. All systems nominal.")

@app.on_event("shutdown")
async def shutdown_event():
    log.info("---- Project Chimera Server Shutting Down ----")

# =================================================================
# Core Investigation Logic (Preserved from your file)
# =================================================================
def is_json_verdict(message):
    content = message.get("content", "")
    if not content:
        return False
    try:
        json_start = content.find('{')
        if json_start == -1: return False
        json_end = content.rfind('}') + 1
        if json_end == 0: return False
        json_str = content[json_start:json_end]
        data = json.loads(json_str)
        if isinstance(data, dict) and 'verdict' in data:
            return True
    except (json.JSONDecodeError, IndexError):
        return False
    return False

def run_investigation(initial_message: str, user_id: str):
    try:
        log.info(f"PHASE 1: Starting Investigation for user '{user_id}'.")
        inquisitor_llm_config = get_llm_config_for_model(INQUISITOR_MODEL)
        inquisitor_llm_config["tools"] = investigation_tool_schemas
        inquisitor = autogen.AssistantAgent(name="Inquisitor", system_message=INQUISITOR_PROMPT, llm_config=inquisitor_llm_config)
        user_proxy_investigation = autogen.UserProxyAgent(name="UserProxyInvestigation", human_input_mode="NEVER", is_termination_msg=is_json_verdict, code_execution_config=False)
        investigation_functions = {
            "check_geo_fence_otp": check_geo_fence_otp, 
            "validate_impossible_travel": validate_impossible_travel, 
            "get_behavioral_anomaly_score": get_behavioral_anomaly_score, 
            "analyze_sms_phishing": analyze_sms_phishing
        }
        user_proxy_investigation.register_function(function_map=investigation_functions)
        user_proxy_investigation.initiate_chat(recipient=inquisitor, message=initial_message, max_turns=10)
        
        last_message_content = user_proxy_investigation.last_message(inquisitor)["content"]
        json_start = last_message_content.find('{')
        json_end = last_message_content.rfind('}') + 1
        verdict_json_str = last_message_content[json_start:json_end] if json_start != -1 else last_message_content
        
        try:
            verdict_data = json.loads(verdict_json_str)
            log.info(f"PHASE 1: Investigation complete. Valid JSON verdict received: {verdict_data}")
            action_message = f"User ID is '{user_id}'. The Inquisitor has provided the following verdict. Take the appropriate actions based on your protocol. Verdict: {verdict_json_str}"
        except json.JSONDecodeError:
            log.error(f"PHASE 1 FAILED: Could not extract valid JSON from final message: '{last_message_content}'")
            fallback_verdict = {"verdict": "Inconclusive Investigation", "threat_level": "MEDIUM", "reasoning": "The investigation agent failed to produce a valid JSON verdict."}
            verdict_json_str = json.dumps(fallback_verdict)
            action_message = f"User ID is '{user_id}'. The Inquisitor has provided the following fallback verdict. Verdict: {verdict_json_str}"

        log.info(f"PHASE 2: Starting Action Phase for user '{user_id}'.")
        orchestrator_llm_config = get_llm_config_for_model(ORCHESTRATOR_MODEL)
        orchestrator_llm_config["tools"] = action_tool_schemas
        orchestrator = autogen.AssistantAgent(name="Orchestrator", system_message=ORCHESTRATOR_PROMPT, llm_config=orchestrator_llm_config)
        user_proxy_action = autogen.UserProxyAgent(name="UserProxyAction", human_input_mode="NEVER", is_termination_msg=lambda x: x.get("content") and x.get("content", "").rstrip().endswith("TASK_COMPLETE"), code_execution_config=False)        
        action_functions = {"lock_user_session": lock_user_session, "initiate_step_up_auth": initiate_step_up_auth, "send_notification": send_notification, "log_incident_to_memory": log_incident_to_memory}
        user_proxy_action.register_function(function_map=action_functions)
        user_proxy_action.initiate_chat(recipient=orchestrator, message=action_message, max_turns=5)
        log.info("PHASE 2: Action phase complete. Guardian Council investigation has successfully concluded.")
    except Exception as e:
        log.critical(f"FATAL ERROR in background investigation task: {e}", exc_info=True)
        
# =================================================================
# NEW: AUTHENTICATION ROUTER (Public, no API key needed)
# =================================================================
auth_router = APIRouter()

@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    log.info(f"Attempting to register new user: {user.email}")
    existing_user = user_collection.find_one({"email": user.email})
    if existing_user:
        log.warning(f"Registration failed for {user.email}: email already exists.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )
    
    hashed_password = get_password_hash(user.password)
    user_document = {"email": user.email, "hashed_password": hashed_password}
    try:
        result = user_collection.insert_one(user_document)
        log.info(f"Successfully inserted user with ID: {result.inserted_id}")
    except Exception as e:
        log.error(f"DATABASE ERROR: Failed to insert user {user.email}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user due to a database error.",
        )
    # --- END OF BLOCK ---
    return {"status": "success", "message": "User registered successfully."}

# in api.py

@auth_router.post("/login")
async def login_user(user: UserCreate):
    log.info(f"Login attempt for user: {user.email}")
    
    # Step 1: Find the user in the database
    db_user = user_collection.find_one({"email": user.email})
    if not db_user:
        log.warning(f"Login failed for {user.email}: User not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    
    log.info(f"User '{user.email}' found in database. Verifying password...")
    
    # Step 2: Verify the password
    is_password_correct = verify_password(user.password, db_user["hashed_password"])
    if not is_password_correct:
        log.warning(f"Login failed for {user.email}: Incorrect password.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    
    log.info(f"Password for '{user.email}' is correct. Creating access token...")
    
    # Step 3: Create the access token
    try:
        access_token_expires = timedelta(days=1)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        log.info(f"Successfully created token for '{user.email}'.")
        # Ensure the token is a valid string before returning
        if not isinstance(access_token, str):
            log.error("FATAL: create_access_token did not return a string!")
            raise HTTPException(status_code=500, detail="Token generation failed.")
            
    except Exception as e:
        log.error(f"TOKEN CREATION FAILED for user {user.email}. Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token.",
        )
        
    # Step 4: Return the token
    return {"access_token": access_token, "token_type": "bearer"}
# =================================================================
# CORE CHIMERA ROUTER (Protected by API key)
# =================================================================
chimera_router = APIRouter(dependencies=[Depends(get_api_key)])

# --- Internal Action Schemas and Endpoints ---
class ActionPayload(BaseModel): user_id: str; reason: str
class NotificationPayload(BaseModel): user_id: str; message: str; level: str

@chimera_router.post("/internal/lock_session")
async def internal_lock_session(payload: ActionPayload):
    log.info(f"[INTERNAL] ACTION: Lock session for '{payload.user_id}'. Reason: {payload.reason}")
    return {"status": "success", "action": "session_locked", "user_id": payload.user_id}

@chimera_router.post("/internal/step_up_auth")
async def internal_step_up_auth(payload: ActionPayload):
    log.info(f"[INTERNAL] ACTION: Trigger step-up auth for '{payload.user_id}'. Reason: {payload.reason}")
    return {"status": "success", "action": "step_up_initiated", "user_id": payload.user_id}

@chimera_router.post("/internal/send_notification")
async def internal_send_notification(payload: NotificationPayload):
    log.info(f"[INTERNAL] ACTION: Send '{payload.level}' notification to '{payload.user_id}': {payload.message}")
    return {"status": "success", "action": "notification_sent", "user_id": payload.user_id}

# --- Public API Endpoints ---
@chimera_router.post("/alert", status_code=202)
async def process_alert(payload: AlertPayload, background_tasks: BackgroundTasks):
    initial_message = f"New Alert for user '{payload.user_id}': {payload.model_dump_json()}"
    background_tasks.add_task(run_investigation, initial_message, payload.user_id)
    return {"status": "accepted", "message": "Alert received, investigation initiated."}

@chimera_router.post("/onboard/location", status_code=200)
async def onboard_location_data(payload: LocationDatapoint):
    return add_location_datapoint(payload.user_id, payload.lat, payload.lon)

@chimera_router.post("/onboard/behavior", status_code=200)
async def onboard_behavior_data(payload: BehavioralDatapoint):
    return add_behavioral_datapoint(payload.user_id, payload.kinetic_data)

# =================================================================
# Include Routers in the Main App
# =================================================================
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chimera_router, prefix="/v1", tags=["Chimera Core"])