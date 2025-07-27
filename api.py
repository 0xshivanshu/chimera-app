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
    ORCHESTRATOR_PROMPT, INQUISITOR_PROMPT, investigation_tool_schemas, action_tool_schemas
)
# Import all tool modules
from tools.onboarding_tools import initialize_database, add_location_datapoint, add_behavioral_datapoint
from tools.investigation_tools import (
    check_geo_fence_otp, validate_impossible_travel, get_behavioral_anomaly_score, analyze_sms_phishing
)
from tools.action_tools import (
    lock_user_session, initiate_step_up_auth, send_notification, log_incident_to_memory
)
def is_json_verdict(message):
    """
    Checks if the message content is a valid JSON object containing a 'verdict' key.
    This is a robust way to detect the final answer from the Inquisitor.
    """
    # The .get() method is used to safely handle cases where 'content' might be missing.
    content = message.get("content", "")
    if not content:
        return False

    try:
        # Find the start of the JSON block
        json_start = content.find('{')
        if json_start == -1:
            return False
            
        # Find the end of the JSON block
        json_end = content.rfind('}') + 1
        if json_end == 0:
            return False

        # Extract the potential JSON string
        json_str = content[json_start:json_end]
        
        data = json.loads(json_str)
        # Check if it's a dictionary and has the required 'verdict' key
        if isinstance(data, dict) and 'verdict' in data:
            return True
    except (json.JSONDecodeError, IndexError):
        # If it's not valid JSON or doesn't have the right structure, it's not the final verdict.
        return False
    return False


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
    This function runs the definitive, two-phase agentic workflow
    using the modern, robust tool-calling pattern.
    """
    try:
        log.info(f"PHASE 1: Starting Investigation for user '{user_id}'.")

        # --- PHASE 1: INVESTIGATION ---
        
        # 1. Configure the LLM to be officially aware of the tools.
        inquisitor_llm_config = get_llm_config_for_model(INQUISITOR_MODEL)
        inquisitor_llm_config["tools"] = investigation_tool_schemas

        inquisitor = autogen.AssistantAgent(
            name="Inquisitor", 
            system_message=INQUISITOR_PROMPT, 
            llm_config=inquisitor_llm_config
        )

        # 2. Configure the proxy to ONLY execute tools.
        user_proxy_investigation = autogen.UserProxyAgent(
            name="UserProxyInvestigation",
            human_input_mode="NEVER",
            is_termination_msg=is_json_verdict,
            code_execution_config=False,
        )
        
        # 3. Register the functions so the proxy knows HOW to execute them.
        investigation_functions = {
            "check_geo_fence_otp": check_geo_fence_otp, 
            "validate_impossible_travel": validate_impossible_travel, 
            "get_behavioral_anomaly_score": get_behavioral_anomaly_score, 
            "analyze_sms_phishing": analyze_sms_phishing
        }
        user_proxy_investigation.register_function(function_map=investigation_functions)

        user_proxy_investigation.initiate_chat(
            recipient=inquisitor,
            message=initial_message,
            max_turns=10, # Increased max_turns to allow for more tool steps
        )
        
        # --- VERDICT VALIDATION LOGIC ---
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
            fallback_verdict = {
                "verdict": "Inconclusive Investigation", "threat_level": "MEDIUM",
                "reasoning": "The investigation agent failed to produce a valid JSON verdict. Manual review required."
            }
            verdict_json_str = json.dumps(fallback_verdict)
            action_message = f"User ID is '{user_id}'. The Inquisitor has provided the following fallback verdict. Take the appropriate actions based on your protocol. Verdict: {verdict_json_str}"

        # --- PHASE 2: ACTION ---
        log.info(f"PHASE 2: Starting Action Phase for user '{user_id}'.")
        
        orchestrator_llm_config = get_llm_config_for_model(ORCHESTRATOR_MODEL)
        orchestrator_llm_config["tools"] = action_tool_schemas

        orchestrator = autogen.AssistantAgent(
            name="Orchestrator", 
            system_message=ORCHESTRATOR_PROMPT, 
            llm_config=orchestrator_llm_config
        )

        user_proxy_action = autogen.UserProxyAgent(
            name="UserProxyAction", 
            human_input_mode="NEVER", 
            # THIS IS THE FINAL FIX: Make the lambda robust to None content.
            is_termination_msg=lambda x: x.get("content") and x.get("content", "").rstrip().endswith("TASK_COMPLETE"),
            code_execution_config=False,
        )        
        
        action_functions = {
            "lock_user_session": lock_user_session, 
            "initiate_step_up_auth": initiate_step_up_auth, 
            "send_notification": send_notification, 
            "log_incident_to_memory": log_incident_to_memory
        }
        user_proxy_action.register_function(function_map=action_functions)

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