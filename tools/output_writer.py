import os
import json
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

