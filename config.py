import os
import json

CONFIG_FILE = os.getenv("CONFIG_FILE")

def load_config():
    if not CONFIG_FILE or not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError("CONFIG_FILE environment variable missing or file does not exist")
    with open(CONFIG_FILE) as f:
        return json.load(f)

def get_deployment(repo: str, branch: str):
    config = load_config()
    for deployment in config.get("deployments", []):
        if deployment["repo"] == repo and deployment["branch"] == branch:
            return deployment
    return None
