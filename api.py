import autogen
import json
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from logger_config import log, setup_logging
from schemas import AlertPayload, LocationDatapoint, BehavioralDatapoint
from security import get_api_key
from config import (
    get_llm_config_for_model, ORCHESTRATOR_MODEL, INQUISITOR_MODEL,
    ORCHESTRATOR_PROMPT, INQUISITOR_PROMPT, LOG_LEVEL
)
# Import all tool modules
from tools.onboarding_tools import initialize_database, add_location_datapoint, add_behavioral_datapoint
from tools.investigation_tools import (
    check_geo_fence_otp, validate_impossible_travel, get_behavioral_anomaly_score, analyze_sms_phishing
)
from tools.action_tools import (
    lock_user_session, initiate_step_up_auth, send_notification, log_incident_to_memory
)

# --- FastAPI App Initialization and Lifecycle ---
app = FastAPI(title="Project Chimera API", version="3.0.0")

@app.on_event("startup")
async def startup_event():
    setup_logging()
    log.info("---- Project Chimera Server Starting Up ----")
    initialize_database()
    log.info("Startup complete. All systems nominal.")

@app.on_event("shutdown")
async def shutdown_event():
    log.info("---- Project Chimera Server Shutting Down ----")

# --- Internal Action Schemas and Endpoints ---
class ActionPayload(BaseModel): user_id: str; reason: str
class NotificationPayload(BaseModel): user_id: str; message: str; level: str

@app.post("/v1/internal/lock_session", dependencies=[Depends(get_api_key)])
async def internal_lock_session(payload: ActionPayload):
    log.info(f"[INTERNAL] ACTION: Lock session for '{payload.user_id}'. Reason: {payload.reason}")
    return {"status": "success", "action": "session_locked", "user_id": payload.user_id}

@app.post("/v1/internal/step_up_auth", dependencies=[Depends(get_api_key)])
async def internal_step_up_auth(payload: ActionPayload):
    log.info(f"[INTERNAL] ACTION: Trigger step-up auth for '{payload.user_id}'. Reason: {payload.reason}")
    return {"status": "success", "action": "step_up_initiated", "user_id": payload.user_id}

@app.post("/v1/internal/send_notification", dependencies=[Depends(get_api_key)])
async def internal_send_notification(payload: NotificationPayload):
    log.info(f"[INTERNAL] ACTION: Send '{payload.level}' notification to '{payload.user_id}': {payload.message}")
    return {"status": "success", "action": "notification_sent", "user_id": payload.user_id}

# --- Core Investigation Logic ---
def run_investigation(initial_message: str):
    try:
        log.info("Guardian Council investigation initiated in background task.")
        orchestrator = autogen.AssistantAgent(name="Orchestrator", system_message=ORCHESTRATOR_PROMPT, llm_config=get_llm_config_for_model(ORCHESTRATOR_MODEL))
        inquisitor = autogen.AssistantAgent(name="Inquisitor", system_message=INQUISITOR_PROMPT, llm_config=get_llm_config_for_model(INQUISITOR_MODEL))
        user_proxy = autogen.UserProxyAgent(name="UserProxy", human_input_mode="NEVER", is_termination_msg=lambda x: x.get("content", "").rstrip() == "TASK_COMPLETE", code_execution_config=False)

        investigation_functions = {"check_geo_fence_otp": check_geo_fence_otp, "validate_impossible_travel": validate_impossible_travel, "get_behavioral_anomaly_score": get_behavioral_anomaly_score, "analyze_sms_phishing": analyze_sms_phishing}
        action_functions = {"lock_user_session": lock_user_session, "initiate_step_up_auth": initiate_step_up_auth, "send_notification": send_notification, "log_incident_to_memory": log_incident_to_memory}
        
        user_proxy.register_function(function_map={**investigation_functions, **action_functions})
        inquisitor.register_function(function_map=investigation_functions)
        orchestrator.register_function(function_map=action_functions)

        groupchat = autogen.GroupChat(agents=[user_proxy, orchestrator, inquisitor], messages=[], max_round=15)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=get_llm_config_for_model(ORCHESTRATOR_MODEL))
        manager.initiate_chat(recipient=orchestrator, message=initial_message)
        log.info("Guardian Council investigation has successfully concluded.")
    except Exception as e:
        log.critical(f"FATAL ERROR in background investigation task: {e}", exc_info=True)

# --- Public API Endpoints ---
@app.post("/v1/alert", status_code=202, dependencies=[Depends(get_api_key)])
async def process_alert(payload: AlertPayload, background_tasks: BackgroundTasks):
    initial_message = f"New Alert for user '{payload.user_id}': {payload.model_dump_json()}"
    background_tasks.add_task(run_investigation, initial_message)
    return {"status": "accepted", "message": "Alert received, investigation initiated."}

@app.post("/v1/onboard/location", status_code=200, dependencies=[Depends(get_api_key)])
async def onboard_location_data(payload: LocationDatapoint):
    return add_location_datapoint(payload.user_id, payload.lat, payload.lon)

@app.post("/v1/onboard/behavior", status_code=200, dependencies=[Depends(get_api_key)])
async def onboard_behavior_data(payload: BehavioralDatapoint):
    return add_behavioral_datapoint(payload.user_id, payload.kinetic_data)