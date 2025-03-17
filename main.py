# main.py
import os
import sys
import yaml
import time
from typing import Dict, Any
from watchdog.observers import Observer

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv is not installed. Environment variables from .env file won't be loaded.")
    print("Install with: pip install python-dotenv")
    def load_dotenv(*args, **kwargs):
        pass

from core.factory import create_adapter_from_config
from tools.file_watcher import watch_folder, process_existing_files, CaptureHandler

def load_env_vars(env_path: str = None):
    """Load environment variables from .env file."""
    if env_path is None:
        # Try to find .env in the project root
        env_path = os.path.join(project_root, '.env')
    
    # Load environment variables from .env file
    load_dotenv(env_path)
    
    # Check for OLLAMA_BASE_URL
    if not os.getenv("OLLAMA_BASE_URL"):
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {config_path}: {e}")
        return {}

def load_configs(
    agents_path: str = "config/agents.yaml",
    llms_path: str = "config/llms.yaml", 
    prompts_path: str = "config/prompts.yaml",
    system_path: str = "config/system.yaml"
) -> Dict[str, Any]:
    """Load and merge multiple configuration files."""
    
    # Load each configuration file
    agents_config = load_config(agents_path)
    llms_config = load_config(llms_path)
    prompts_config = load_config(prompts_path)
    system_config = load_config(system_path)
    
    # Create a merged config
    merged_config = {
        "agents": agents_config.get("agents", {}),
        "llm_configs": llms_config,
        "prompts": prompts_config,
        "folders": system_config.get("folders", {})
    }
    
    return merged_config

def setup_folder_processing(config):
    """Set up folder watching and processing based on config."""
    # Get folder paths from config
    folders = config.get("folders", {})
    base_path = folders.get("base", "")
    capture_folder = os.path.join(base_path, folders.get("capture", "_inbox"))
    
    print(f"Watching folder: {capture_folder}")
    
    # Process any existing files first
    process_existing_files(capture_folder, lambda x: process_thought(x, config))
    
    # Set up folder watching
    observer = watch_folder(capture_folder, lambda x: process_thought(x, config))
    
    return observer

def process_thought(thought_object, config):
    """Process a thought through the pipeline using tools module."""
    from tools.document_processor import process_with_agent, pass_to_next_agent
    from tools.output_writer import write_result
    
    # Get agent pipeline
    agent_pipeline = [
        ("capture", "Capture"),
        ("contextualize", "Contextualize"),
        ("clarify", "Clarify"),
        ("categorize", "Categorize"),
        ("crystallize", "Crystallize"),
        ("connect", "Connect")
    ]
    
    # Setup prompt templates
    prompt_templates = {}
    for agent_id in [stage[0] for stage in agent_pipeline]:
        template_key = f"{agent_id}_prompt_template"
        if template_key in config.get("prompts", {}):
            prompt_templates[agent_id] = config["prompts"][template_key]
    
    # Create a mock agent for each stage
    agents = {}
    for agent_id, agent_config in config.get("agents", {}).items():
        # Create a simple object with attributes needed by the document_processor
        agent = type('Agent', (), {})()
        agent.role = agent_config.get("role", "")
        agent.goal = agent_config.get("goal", "")
        agent.backstory = agent_config.get("backstory", "")
        agent.llm_config = agent_config.get("llm_config", "default")
        agents[agent_id] = agent
    
    # Process the thought through each stage
    current_thought = thought_object
    
    for agent_id, agent_name in agent_pipeline:
        if agent_id in agents:
            print(f"Processing with {agent_name} agent...")
            agent = agents[agent_id]
            current_thought = process_with_agent(
                current_thought, 
                agent,
                agent_name,
                agent_id,
                prompt_templates
            )
    
    # Write the final result
    output_folder = os.path.join(
        config.get("folders", {}).get("base", ""),
        config.get("folders", {}).get("connect", "6-Connect")
    )
    write_result(current_thought, output_folder)
    
    return current_thought

def main():
    # Load configuration
    config = load_configs(
        "config/agents.yaml", 
        "config/llms.yaml",
        "config/prompts.yaml",
        "config/system.yaml"
    )
    
    # Load environment variables
    load_env_vars()
    
    # Import and initialize LLM configurations
    from tools.llm_handler import initialize_llm_configs
    initialize_llm_configs("config/llms.yaml")  # Actually call the function
    
    # Set up folder processing
    observer = setup_folder_processing(config)
    
    # Keep the main thread running
    try:
        print("Thought Processing System running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()