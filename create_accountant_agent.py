import subprocess
import time
import os

MODEL_NAME = "gemini-3-pro-preview-cloud"
AGENT_NAME = "accountant"
MODELFILE_PATH = "/home/shiva/vikarma/Accountant.modelfile"

def check_model_exists(name):
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    return name in result.stdout

def create_agent():
    print(f"Checking for cloud model {MODEL_NAME}...")
    if not check_model_exists(MODEL_NAME):
        print(f"Model {MODEL_NAME} not found. Pulling from Ollama Cloud...")
        subprocess.run(["ollama", "pull", MODEL_NAME])

    print(f"Creating agent {AGENT_NAME} from cloud base...")
    subprocess.run(["ollama", "create", AGENT_NAME, "-f", MODELFILE_PATH])
    print(f"Agent {AGENT_NAME} (Cloud) created successfully.")

if __name__ == "__main__":
    create_agent()
