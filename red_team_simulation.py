import autogen
from logger_config import log, setup_logging
from config import get_llm_config_for_model, ADVERSARY_MODEL, ADVERSARY_PROMPT
from tools.adversary_tools import query_past_incidents, craft_synthetic_attack_payload, execute_test_scenario

def run_red_team_simulation():
    """
    Initializes and runs the Adversary agent to test the system's defenses.
    """
    setup_logging()
    log.info("="*50)
    log.info("INITIALIZING RED TEAM SIMULATION")
    log.info("="*50)

    adversary_llm_config = get_llm_config_for_model(ADVERSARY_MODEL)

    adversary = autogen.AssistantAgent(
        name="Adversary",
        system_message=ADVERSARY_PROMPT,
        llm_config=adversary_llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name="RedTeamOperator",
        human_input_mode="NEVER",
        is_termination_msg=lambda x: x.get("content", "").rstrip() == "TASK_COMPLETE",
        code_execution_config={"last_n_messages": 1, "work_dir": "coding"}
    )

    # Register adversary tools with both agents
    adversary_tools = {
        "query_past_incidents": query_past_incidents,
        "craft_synthetic_attack_payload": craft_synthetic_attack_payload,
        "execute_test_scenario": execute_test_scenario,
    }
    user_proxy.register_function(function_map=adversary_tools)
    adversary.register_function(function_map=adversary_tools)

    groupchat = autogen.GroupChat(agents=[user_proxy, adversary], messages=[], max_round=10)
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=adversary_llm_config)

    initial_task = "Review past incidents related to location and behavior, then craft and execute a new, subtle attack that combines a small travel distance with a minor behavioral anomaly to test the system's sensitivity."
    
    manager.initiate_chat(recipient=adversary, message=initial_task)

    log.info("="*50)
    log.info("RED TEAM SIMULATION CONCLUDED")
    log.info("="*50)

if __name__ == "__main__":
    run_red_team_simulation()