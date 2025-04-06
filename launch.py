#!/usr/bin/env python
"""
Launcher script for the Tesseract Project
Starts both backend and frontend in separate processes.
"""
import subprocess
import threading
import time
import os
import signal
import sys
import webbrowser
import logging
from typing import List

# Try to import configuration
try:
    from utils.env_loader import get_config
    config = get_config()
except ImportError:
    # Fallback to default configuration
    print("Warning: Could not load configuration from .env file. Using default values.")
    
    class DefaultConfig:
        def __init__(self):
            self.api_host = "0.0.0.0"
            self.api_port = 8000
            self.api_reload = True
            self.ui_port = 8501
            self.browser_auto_open = True
            self.log_level = "INFO"
            self.log_dir = "logs"
            
    config = DefaultConfig()

# Configure logging
if not os.path.exists(config.log_dir):
    os.makedirs(config.log_dir, exist_ok=True)
    
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(config.log_dir, "launcher.log"))
    ]
)
logger = logging.getLogger("launcher")

def print_colored(message: str, color: str):
    """Print a colored message to the terminal."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "end": "\033[0m"
    }
    
    print(f"{colors.get(color, '')}{message}{colors['end']}")

def run_process(cmd: List[str], name: str, color: str):
    """Run a process and capture its output."""
    print_colored(f"Starting {name}...", color)
    logger.info(f"Starting {name} with command: {' '.join(cmd)}")
    
    # Use shell=True on Windows for Python command
    use_shell = sys.platform == "win32" and cmd[0] == "python"
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=use_shell
        )
        
        # Store the process for later termination
        global processes
        processes.append(process)
        
        # Print process output with color coding
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print_colored(f"[{name}] {output.strip()}", color)
                
        return_code = process.poll()
        print_colored(f"{name} exited with return code {return_code}", color)
        logger.info(f"{name} exited with return code {return_code}")
    except Exception as e:
        error_msg = f"Error running {name}: {str(e)}"
        print_colored(error_msg, "red")
        logger.error(error_msg)

def start_api():
    """Start the FastAPI backend."""
    api_cmd = [
        "python", "-m", "uvicorn", 
        "api.fastapi_app:app", 
        "--host", config.api_host, 
        "--port", str(config.api_port)
    ]
    
    # Add reload flag if configured
    if config.api_reload:
        api_cmd.append("--reload")
        
    run_process(api_cmd, "API", "cyan")

def start_ui():
    """Start the Streamlit frontend."""
    ui_cmd = [
        "python", "-m", "streamlit", 
        "run", "frontend/app.py",
        "--server.port", str(config.ui_port)
    ]
    run_process(ui_cmd, "UI", "magenta")

def open_browser():
    """Open web browser to the application."""
    if config.browser_auto_open:
        wait_time = 5  # Seconds to wait for services to start
        print_colored(f"Opening browser in {wait_time} seconds...", "green")
        time.sleep(wait_time)
        webbrowser.open(f"http://localhost:{config.ui_port}")

def create_env_file():
    """Create a .env file if it doesn't exist."""
    if not os.path.exists(".env"):
        print_colored("Creating default .env file...", "yellow")
        
        content = """# Tesseract Project Environment Configuration

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Frontend Configuration
UI_PORT=8501
BROWSER_AUTO_OPEN=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs
"""
        
        try:
            with open(".env", 'w') as f:
                f.write(content)
            
            print_colored(".env file created. You may want to review and update the settings.", "green")
            logger.info(".env file created with default settings")
        except Exception as e:
            print_colored(f"Error creating .env file: {str(e)}", "red")
            logger.error(f"Error creating .env file: {str(e)}")

def signal_handler(sig, frame):
    """Handle process termination."""
    print_colored("\nShutting down...", "yellow")
    for process in processes:
        try:
            process.terminate()
        except:
            pass
    sys.exit(0)

if __name__ == "__main__":
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Store processes for cleanup
    processes = []
    
    # Register signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create threads for each component
    api_thread = threading.Thread(target=start_api)
    ui_thread = threading.Thread(target=start_ui)
    browser_thread = threading.Thread(target=open_browser)
    
    # Start threads
    api_thread.start()
    
    print_colored("Waiting for API to start...", "yellow")
    time.sleep(5)  # Wait for API to start
    
    ui_thread.start()
    browser_thread.start()
    
    # Display information about the running services
    print_colored(f"""
    ┌─────────────────────────────────┐
    │                                 │
    │      Tesseract Project          │
    │                                 │
    │   API: http://{config.api_host}:{config.api_port}    │
    │   UI:  http://localhost:{config.ui_port}    │
    │                                 │
    │   Press Ctrl+C to exit          │
    │                                 │
    └─────────────────────────────────┘
    """, "green")
    
    # Wait for threads to finish
    try:
        api_thread.join()
        ui_thread.join()
    except KeyboardInterrupt:
        print_colored("\nExiting...", "yellow")
        for process in processes:
            process.terminate()