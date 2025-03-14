import os
import json
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
 # Changed from langchain_community.llms import Ollama

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CaptureHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        
    def on_created(self, event):
        # Skip directories and metadata files
        if event.is_directory or os.path.basename(event.src_path).startswith("meta_"):
            return
            
        # Process the file
        print(f"New file detected: {event.src_path}")
        content = read_file(event.src_path)
        if content:
            self.callback(content)

def process_existing_files(folder_path, callback):
    """
    Process existing files in the folder.
    
    Args:
        folder_path (str): Path to the folder to process
        callback (function): Function to call for each file
        
    Returns:
        int: Number of files processed
    """
    if not os.path.exists(folder_path):
        return 0
        
    count = 0
    print(f"Checking for existing files in {folder_path}...")
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Skip directories and metadata files
        if os.path.isdir(file_path) or filename.startswith("meta_") or filename.startswith("."):
            continue
            
        # Process the file
        print(f"Found existing file: {file_path}")
        content = read_file(file_path)
        if content:
            callback(content)
            count += 1
            
    return count

def watch_folder(folder_path, callback):
    """
    Watch a folder for new files and call the callback function when a new file is detected.
    
    Args:
        folder_path (str): Path to the folder to watch
        callback (function): Function to call when a new file is detected
    """
    event_handler = CaptureHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    
    print(f"Watching folder: {folder_path}")
    return observer

def read_file(file_path):
    """
    Read a file and create a dictionary object from its contents.
    
    Args:
        file_path (str): Path to the file to read
        
    Returns:
        dict: Dictionary containing the file content and metadata
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Create a dictionary with the content and basic metadata
    timestamp = datetime.now().isoformat()
    file_id = f"thought_{int(time.time())}"
    file_name = os.path.basename(file_path)
    
    thought_object = {
        "id": file_id,
        "timestamp": timestamp,
        "original_filename": file_name,
        "original_path": file_path,
        "content": content,
        "processing_stage": "capture",
        "processing_history": []
    }
    
    print(f"Read file: {file_name}")
    return thought_object

def communicate_with_llm(prompt, model_name="qwen2.5:14b", provider="ollama", temperature=0.7, api_key=None):
    """
    Communicate with the LLM and get a response.
    
    Args:
        prompt (str): The prompt to send to the LLM.
        model_name (str): The name of the model to use.
        provider (str): The provider to use ("ollama", "gemini", "openai", etc.)
        temperature (float): The temperature setting for generation.
        api_key (str): API key for external providers (not needed for Ollama)
        
    Returns:
        str: The response from the LLM.
    """
    print("========= COMMUNICATE WITH LLM FUNCTION CALLED =========")
    print(f"Using provider: {provider}, model: {model_name}")
    print(f"Prompt first 100 chars: {prompt[:100]}...")
    
    try:
        # Configure model based on provider
        if provider.lower() == "ollama":
            # Ollama is local, use the direct model name format
            full_model_name = f"ollama/{model_name}"
            litellm.ollama_api_base = "http://localhost:11434"
        elif provider.lower() == "gemini":
            # For Gemini, use the gemini model format
            full_model_name = f"gemini/{model_name}"
            # Set API key if provided
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
        elif provider.lower() == "openai":
            # For OpenAI, use the openai model format
            full_model_name = f"openai/{model_name}"
            # Set API key if provided
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        else:
            # Default fallback to Ollama
            print(f"Unknown provider '{provider}', falling back to Ollama")
            full_model_name = f"ollama/{model_name}"
            litellm.ollama_api_base = "http://localhost:11434"
        
        print(f"Using model: {full_model_name}")
        
        # Get response from LLM
        response = litellm.completion(
            model=full_model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        
        # Extract the actual response text
        response_text = response.choices[0].message.content
        
        print(f"Received response from LLM, length: {len(response_text)}")
        return response_text
    except Exception as e:
        print(f"LLM ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return f"ERROR: Failed to communicate with LLM: {str(e)}"

def process_with_agent(thought_object, agent, agent_name, agent_id, prompt_templates):
    """Process a thought object with an agent."""
    # Record the current stage in history
    thought_object["processing_history"].append({
        "stage": thought_object["processing_stage"],
        "timestamp": datetime.now().isoformat()
    })
    
    # Update the current processing stage
    thought_object["processing_stage"] = agent_name.lower()
    
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
        
        # Send the prompt to the LLM and get the response
        print(f"Sending thought to LLM with {agent_name} agent...")
        llm_response = communicate_with_llm(prompt)
        
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
            
            # Send the prompt to the LLM and get the response
            print(f"Sending thought to LLM with {agent_name} agent...")
            llm_response = communicate_with_llm(prompt)
            
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

def write_result(thought_object, output_folder):
    """
    Write the processed thought object to a file in the output folder.
    
    Args:
        thought_object (dict): The processed thought object
        output_folder (str): The folder to write the result to
        
    Returns:
        str: Path to the output file
    """
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Create a filename based on the thought ID
    output_filename = f"processed_{thought_object['id']}.json"
    output_path = os.path.join(output_folder, output_filename)
    
    # Write the thought object to a JSON file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(thought_object, file, indent=2)
    
    print(f"Wrote result to: {output_path}")
    return output_path