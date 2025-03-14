# tools/file_watcher.py
import os
import json
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CaptureHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        
    def on_created(self, event):
        # Skip directories and metadata files
        if event.is_directory or os.path.basename(event.src_path).startswith("meta_") or os.path.basename(event.src_path).startswith("."):
            return
            
        # Process the file
        print(f"New file detected: {event.src_path}")
        content = read_file(event.src_path)
        if content:
            self.callback(content)

def process_existing_files(folder_path, callback):
    """Process existing files in the folder."""
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
    """Watch a folder for new files and call the callback function when a new file is detected."""
    event_handler = CaptureHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    
    print(f"Watching folder: {folder_path}")
    return observer

def read_file(file_path):
    """Read a file and create a dictionary object from its contents."""
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