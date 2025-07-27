# import autogen
# import json
# import os
# from pathlib import Path
# from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
# from pydantic import BaseModel
# from logger_config import log, setup_logging
# from schemas import AlertPayload, LocationDatapoint, BehavioralDatapoint
# from security import get_api_key
# from config import (
#     get_llm_config_for_model, ORCHESTRATOR_MODEL, INQUISITOR_MODEL,
#     ORCHESTRATOR_PROMPT, INQUISITOR_PROMPT, LOG_LEVEL
# )
# # Import all tool modules
# from tools.onboarding_tools import initialize_database, add_location_datapoint, add_behavioral_datapoint
# from tools.investigation_tools import (
#     check_geo_fence_otp, validate_impossible_travel, get_behavioral_anomaly_score, analyze_sms_phishing
# )
# from tools.action_tools import (
#     lock_user_session, initiate_step_up_auth, send_notification, log_incident_to_memory
# )

# # --- FastAPI App Initialization and Lifecycle ---
# app = FastAPI(title="Project Chimera API", version="3.0.0")

# @app.on_event("startup")
# async def startup_event():
#     setup_logging()
#     log.info("---- Project Chimera Server Starting Up ----")
    
#     # Ensure required directories exist
#     Path("memory").mkdir(exist_ok=True)
#     Path("coding").mkdir(exist_ok=True)
    
#     initialize_database()
#     log.info("Startup complete. All systems nominal.")

# @app.on_event("shutdown")
# async def shutdown_event():
#     log.info("---- Project Chimera Server Shutting Down ----")

# # --- Internal Action Schemas and Endpoints ---
# class ActionPayload(BaseModel): user_id: str; reason: str
# class NotificationPayload(BaseModel): user_id: str; message: str; level: str

# @app.post("/v1/internal/lock_session", dependencies=[Depends(get_api_key)])
# async def internal_lock_session(payload: ActionPayload):
#     log.info(f"[INTERNAL] ACTION: Lock session for '{payload.user_id}'. Reason: {payload.reason}")
#     return {"status": "success", "action": "session_locked", "user_id": payload.user_id}

# @app.post("/v1/internal/step_up_auth", dependencies=[Depends(get_api_key)])
# async def internal_step_up_auth(payload: ActionPayload):
#     log.info(f"[INTERNAL] ACTION: Trigger step-up auth for '{payload.user_id}'. Reason: {payload.reason}")
#     return {"status": "success", "action": "step_up_initiated", "user_id": payload.user_id}

# @app.post("/v1/internal/send_notification", dependencies=[Depends(get_api_key)])
# async def internal_send_notification(payload: NotificationPayload):
#     log.info(f"[INTERNAL] ACTION: Send '{payload.level}' notification to '{payload.user_id}': {payload.message}")
#     return {"status": "success", "action": "notification_sent", "user_id": payload.user_id}

# # --- Core Investigation Logic ---
# def run_investigation(initial_message: str, user_id: str):
#     """
#     This function runs the definitive, two-phase agentic workflow.
#     This version fixes the tool-calling incompatibility with the Ollama model.
#     """
#     try:
#         log.info(f"PHASE 1: Starting Investigation for user '{user_id}'.")

#         # --- PHASE 1: INVESTIGATION ---
        
#         # We use the standard LLM config without the "tools" parameter.
#         inquisitor_llm_config = get_llm_config_for_model(INQUISITOR_MODEL)
        
#         inquisitor = autogen.AssistantAgent(
#             name="Inquisitor", 
#             system_message=INQUISITOR_PROMPT, 
#             llm_config=inquisitor_llm_config
#         )

#         user_proxy_investigation = autogen.UserProxyAgent(
#             name="UserProxyInvestigation",
#             human_input_mode="NEVER",
#             # This config is necessary for the proxy to execute function calls.
#             code_execution_config={"last_n_messages": 1, "work_dir": "coding"},
#         )
        
#         # --- START OF FIX ---
#         # We define the tools and register them in the classic, robust way.
#         investigation_functions = {
#             "check_geo_fence_otp": check_geo_fence_otp, 
#             "validate_impossible_travel": validate_impossible_travel, 
#             "get_behavioral_anomaly_score": get_behavioral_anomaly_score, 
#             "analyze_sms_phishing": analyze_sms_phishing
#         }
#         # Registering the functions with BOTH agents is the key to the classic method.
#         # The Inquisitor learns the function signatures, and the UserProxy learns how to execute them.
#         inquisitor.register_function(function_map=investigation_functions)
#         user_proxy_investigation.register_function(function_map=investigation_functions)
#         # --- END OF FIX ---

#         # We initiate the chat without the "tool_choice" parameter.
#         user_proxy_investigation.initiate_chat(
#             recipient=inquisitor,
#             message=initial_message,
#             max_turns=5,
#         )
        
#         # Correctly extract the last message from the chat history.
#         inquisitor_messages = user_proxy_investigation.chat_messages[inquisitor]
#         last_message = inquisitor_messages[-1]
#         verdict_json_str = last_message['content'].strip().replace("TERMINATE", "")
        
#         log.info(f"PHASE 1: Investigation complete. Verdict received: {verdict_json_str}")

#         # --- PHASE 2: ACTION ---
#         log.info(f"PHASE 2: Starting Action Phase for user '{user_id}'.")
        
#         orchestrator = autogen.AssistantAgent(name="Orchestrator", system_message=ORCHESTRATOR_PROMPT, llm_config=get_llm_config_for_model(ORCHESTRATOR_MODEL))
#         user_proxy_action = autogen.UserProxyAgent(name="UserProxyAction", human_input_mode="NEVER", is_termination_msg=lambda x: x.get("content", "").rstrip() == "TASK_COMPLETE", code_execution_config={"last_n_messages": 1, "work_dir": "coding"})
        
#         action_functions = {"lock_user_session": lock_user_session, "initiate_step_up_auth": initiate_step_up_auth, "send_notification": send_notification, "log_incident_to_memory": log_incident_to_memory}
#         # Register the action functions with both the Orchestrator and the proxy.
#         orchestrator.register_function(function_map=action_functions)
#         user_proxy_action.register_function(function_map=action_functions)

#         action_message = f"User ID is '{user_id}'. The Inquisitor has provided the following verdict. Take the appropriate actions based on your protocol. Verdict: {verdict_json_str}"
        
#         user_proxy_action.initiate_chat(
#             recipient=orchestrator,
#             message=action_message,
#             max_turns=5,
#         )

#         log.info("PHASE 2: Action phase complete. Guardian Council investigation has successfully concluded.")

#     except Exception as e:
#         log.critical(f"FATAL ERROR in background investigation task: {e}", exc_info=True)


# # --- Public API Endpoints ---
# # IMPORTANT: Update the process_alert function signature
# @app.post("/v1/alert", status_code=202, dependencies=[Depends(get_api_key)])
# async def process_alert(payload: AlertPayload, background_tasks: BackgroundTasks):
#     initial_message = f"New Alert for user '{payload.user_id}': {payload.model_dump_json()}"
#     # Pass the user_id explicitly to the background task
#     background_tasks.add_task(run_investigation, initial_message, payload.user_id)
#     return {"status": "accepted", "message": "Alert received, investigation initiated."}

# @app.post("/v1/onboard/location", status_code=200, dependencies=[Depends(get_api_key)])
# async def onboard_location_data(payload: LocationDatapoint):
#     return add_location_datapoint(payload.user_id, payload.lat, payload.lon)

# @app.post("/v1/onboard/behavior", status_code=200, dependencies=[Depends(get_api_key)])
# async def onboard_behavior_data(payload: BehavioralDatapoint):
#     return add_behavioral_datapoint(payload.user_id, payload.kinetic_data)

# api.py (Definitive Version)

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
app = FastAPI(title="Project Chimera API", version="3.1.0") # Version bump for the fix

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
def run_investigation(initial_message: str, user_id: str):
    """
    This function runs the definitive, two-phase agentic workflow.
    This version includes robust error handling for the Inquisitor's verdict.
    """
    try:
        log.info(f"PHASE 1: Starting Investigation for user '{user_id}'.")

        # --- PHASE 1: INVESTIGATION ---
        inquisitor = autogen.AssistantAgent(
            name="Inquisitor", 
            system_message=INQUISITOR_PROMPT, 
            llm_config=get_llm_config_for_model(INQUISITOR_MODEL)
        )
        user_proxy_investigation = autogen.UserProxyAgent(
            name="UserProxyInvestigation",
            human_input_mode="NEVER",
            # This function tells the proxy to STOP when it sees a final verdict.
            is_termination_msg=lambda x: "verdict" in x.get("content", "").lower(),
            code_execution_config=False,
        )

        
        investigation_functions = {
            "check_geo_fence_otp": check_geo_fence_otp, 
            "validate_impossible_travel": validate_impossible_travel, 
            "get_behavioral_anomaly_score": get_behavioral_anomaly_score, 
            "analyze_sms_phishing": analyze_sms_phishing
        }
        user_proxy_investigation.register_function(function_map=investigation_functions)
        inquisitor.register_function(function_map=investigation_functions)

        user_proxy_investigation.initiate_chat(
            recipient=inquisitor,
            message=initial_message,
            max_turns=5,
        )
        
        inquisitor_messages = user_proxy_investigation.chat_messages[inquisitor]
        last_message = inquisitor_messages[-1]
        verdict_json_str = last_message['content'].strip().replace("TERMINATE", "")
        
        # --- VERDICT VALIDATION ---
        try:
            # Attempt to parse the final message as JSON. This is our critical guardrail.
            verdict_data = json.loads(verdict_json_str)
            log.info(f"PHASE 1: Investigation complete. Valid JSON verdict received: {verdict_data}")
            action_message = f"User ID is '{user_id}'. The Inquisitor has provided the following verdict. Take the appropriate actions based on your protocol. Verdict: {verdict_json_str}"
        except json.JSONDecodeError:
            # If parsing fails, the Inquisitor has failed its primary duty.
            log.error(f"PHASE 1 FAILED: Inquisitor did not return valid JSON. Final message: '{verdict_json_str}'")
            # Create a fallback verdict to trigger a safe, high-alert action.
            fallback_verdict = {
                "verdict": "Inconclusive Investigation",
                "confidence": 85, # Set a medium-high confidence to ensure it's not ignored.
                "reasoning": "The investigation agent failed to produce a valid JSON verdict. Manual review required."
            }
            verdict_json_str = json.dumps(fallback_verdict)
            action_message = f"User ID is '{user_id}'. The Inquisitor has provided the following fallback verdict. Take the appropriate actions based on your protocol. Verdict: {verdict_json_str}"

        # --- PHASE 2: ACTION ---
        log.info(f"PHASE 2: Starting Action Phase for user '{user_id}'.")
        
        orchestrator = autogen.AssistantAgent(name="Orchestrator", system_message=ORCHESTRATOR_PROMPT, llm_config=get_llm_config_for_model(ORCHESTRATOR_MODEL))
        user_proxy_action = autogen.UserProxyAgent(
            name="UserProxyAction", 
            human_input_mode="NEVER", 
            is_termination_msg=lambda x: x.get("content", "").rstrip() == "TASK_COMPLETE", 
            code_execution_config=False
        )
        
        action_functions = {
            "lock_user_session": lock_user_session, 
            "initiate_step_up_auth": initiate_step_up_auth, 
            "send_notification": send_notification, 
            "log_incident_to_memory": log_incident_to_memory
        }
        user_proxy_action.register_function(function_map=action_functions)
        orchestrator.register_function(function_map=action_functions)
        
        user_proxy_action.initiate_chat(
            recipient=orchestrator,
            message=action_message,
            max_turns=5,
        )

        log.info("PHASE 2: Action phase complete. Guardian Council investigation has successfully concluded.")

    except Exception as e:
        log.critical(f"FATAL ERROR in background investigation task: {e}", exc_info=True)

        
# --- Public API Endpoints ---
@app.post("/v1/alert", status_code=202, dependencies=[Depends(get_api_key)])
async def process_alert(payload: AlertPayload, background_tasks: BackgroundTasks):
    initial_message = f"New Alert for user '{payload.user_id}': {payload.model_dump_json()}"
    background_tasks.add_task(run_investigation, initial_message, payload.user_id)
    return {"status": "accepted", "message": "Alert received, investigation initiated."}

@app.post("/v1/onboard/location", status_code=200, dependencies=[Depends(get_api_key)])
async def onboard_location_data(payload: LocationDatapoint):
    return add_location_datapoint(payload.user_id, payload.lat, payload.lon)

@app.post("/v1/onboard/behavior", status_code=200, dependencies=[Depends(get_api_key)])
async def onboard_behavior_data(payload: BehavioralDatapoint):
    return add_behavioral_datapoint(payload.user_id, payload.kinetic_data)