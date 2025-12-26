import json
import os
import threading

CONFIG_FILE = os.getenv("CONFIG_FILE", "config.json")
NGINX_CONFIG_FILE = os.getenv("NGINX_CONFIG_FILE", "/etc/nginx/sites-available/deploy.conf")
_lock = threading.Lock()

def load_config() -> dict:
    with _lock:
        if not os.path.exists(CONFIG_FILE):
            return {"deployments": []}
        with open(CONFIG_FILE) as f:
            return json.load(f)

def save_config(config: dict):
    with _lock:
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(config, f, indent=2)
        os.replace(tmp, CONFIG_FILE)

def get_deployment(repo: str, branch: str):
    cfg = load_config()
    for d in cfg.get("deployments", []):
        if d["repo"] == repo and d["branch"] == branch:
            return d
    return None
