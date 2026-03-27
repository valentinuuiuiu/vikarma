import subprocess
import time
import os

MODEL_NAME = "ministral-3:3b"
AGENT_NAME = "accountant"
MODELFILE_PATH = "/home/shiva/vikarma/Accountant.modelfile"

def check_model_exists(name):
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    return name in result.stdout

def create_agent():
    print(f"Checking for base model {MODEL_NAME}...")
    while not check_model_exists(MODEL_NAME):
        time.sleep(10)

    print(f"Base model {MODEL_NAME} found. Creating agent {AGENT_NAME}...")
    subprocess.run(["ollama", "create", AGENT_NAME, "-f", MODELFILE_PATH])
    print(f"Agent {AGENT_NAME} created successfully.")

if __name__ == "__main__":
    create_agent()
