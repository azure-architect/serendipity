# document_processor.py
import os
import json
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def process_with_agent(thought_object, agent, agent_name, agent_id, prompt_templates):
    """Process a thought object with an agent."""
    # Record the current stage in history
    thought_object["processing_history"].append({
        "stage": thought_object["processing_stage"],
        "timestamp": datetime.now().isoformat()
    })
    
    # Update the current processing stage
    thought_object["processing_stage"] = agent_name.lower()
    
    # Get the agent's LLM config name with robust fallback logic
    llm_config_name = None
    
    # Try different possible locations for the llm_config specification
    if hasattr(agent, 'llm_config'):
        llm_config_name = agent.llm_config
    elif hasattr(agent, 'custom_llm_config'):
        llm_config_name = agent.custom_llm_config
    elif hasattr(agent, 'llm') and hasattr(agent.llm, 'llm_config_name'):
        llm_config_name = agent.llm.llm_config_name
    elif hasattr(agent, 'llm') and isinstance(agent.llm, str):
        llm_config_name = agent.llm
    
    # Use default if no configuration is found
    if not llm_config_name:
        llm_config_name = 'default'
        print(f"Using default LLM config for {agent_name} as no valid config found")
    
    # Print the keys to check for case sensitivity or other issues
    print(f"All available template keys: {list(prompt_templates.keys())}")
    print(f"Agent ID: {agent_id}, Present in templates: {agent_id in prompt_templates}")
    
    if agent_id in prompt_templates:
        # Fill in the template with the thought content
        template = prompt_templates[agent_id]
        print(f"Template found for {agent_id}, length: {len(template)}")
        
        # Check for correct placeholder
        if "{thought_content}" in template:
            prompt = template.replace("{thought_content}", thought_object["content"])
        else:
            print(f"WARNING: Template doesn't contain {{thought_content}} placeholder. Using direct replacement.")
            prompt = template.replace("{{content}}", thought_object["content"])
        
        # Send the prompt to the LLM and get the response, passing the agent's LLM config name
        print(f"Sending thought to LLM with {agent_name} agent (using {llm_config_name} LLM config)...")
        from .llm_handler import communicate_with_llm
        llm_response = communicate_with_llm(prompt, llm_config_name)
        
        # Store the LLM response in the thought object
        thought_object[f"{agent_name.lower()}_results"] = llm_response
    else:
        # Try with lowercase version of the agent_id
        lowercase_id = agent_id.lower()
        if lowercase_id in prompt_templates:
            print(f"Found template using lowercase agent ID: {lowercase_id}")
            template = prompt_templates[lowercase_id]
            
            # Fill in the template with the thought content
            if "{thought_content}" in template:
                prompt = template.replace("{thought_content}", thought_object["content"])
            else:
                prompt = template.replace("{{content}}", thought_object["content"])
            
            # Send the prompt to the LLM and get the response, passing the agent's LLM config name
            print(f"Sending thought to LLM with {agent_name} agent (using {llm_config_name} LLM config)...")
            from .llm_handler import communicate_with_llm
            llm_response = communicate_with_llm(prompt, llm_config_name)
            
            # Store the LLM response in the thought object
            thought_object[f"{agent_name.lower()}_results"] = llm_response
        else:
            # Fallback if no prompt template is defined
            print(f"No prompt template found for {agent_id} or {lowercase_id}, skipping LLM call")
            thought_object[f"{agent_name.lower()}_results"] = f"Processed by {agent_name} (no LLM interaction)"
    
    print(f"Processed thought with {agent_name} agent")
    return thought_object

def pass_to_next_agent(thought_object, next_agent, next_agent_name, next_agent_id, prompt_templates):
    """
    Pass a thought object to the next agent.
    
    Args:
        thought_object (dict): The thought object to pass
        next_agent: The next agent to process the thought object
        next_agent_name (str): The name of the next agent (for display)
        next_agent_id (str): The ID of the next agent (for looking up the prompt template)
        prompt_templates (dict): Dictionary of prompt templates
        
    Returns:
        dict: The thought object (for chaining)
    """
    print(f"Passing thought to {next_agent_name} agent")
    return process_with_agent(thought_object, next_agent, next_agent_name, next_agent_id, prompt_templates)