from flask import Flask, request
from dotenv import load_dotenv

import subprocess
import hmac
import hashlib
import os
import json

app = Flask(__name__)

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
CONFIG_FILE = os.getenv("CONFIG_FILE")

if not CONFIG_FILE:
    exit(1)

# Load configuration
with open(CONFIG_FILE) as f:
    config = json.load(f)

def update_nginx(repo_config):
    # Path to Nginx default config
    nginx_file = "/etc/nginx/sites-available/default"
    nginx_path = repo_config["nginx_path"]
    port = repo_config["port"]

    # Read current config
    with open(nginx_file, "r") as f:
        content = f.read()

    # Add location block if not present
    if nginx_path not in content:
        location_block = f"""
            location {nginx_path} {{
                proxy_pass http://localhost:{port}/;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }}
        """
        # Insert before last closing bracket of server block
        content = content.replace("}", location_block + "\n}", 1)
        with open(nginx_file, "w") as f:
            f.write(content)
        # Reload Nginx
        subprocess.run(["nginx", "-t"], check=True)
        subprocess.run(["systemctl", "reload", "nginx"], check=True)

@app.route("/webhook", methods=["POST"])
def webhook():
    if WEBHOOK_SECRET:
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature: return "Missing/Invalid signature", 400
        _, signature = signature.split('=')
        mac = hmac.new(WEBHOOK_SECRET.encode(), msg=request.data, digestmod=hashlib.sha256)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            return "Invalid signature", 400

    data = request.json
    repo_name = data["repository"]["name"]
    branch = data["ref"].split("/")[-1]

    # Find repo in config
    repo_config = next((r for r in config["repos"] if r["name"] == repo_name and r["branch"] == branch), None)
    if not repo_config:
        return "No matching repo or branch", 200

    path = f"/opt/apps/{repo_name}"

    # Pull latest code
    subprocess.run(["git", "-C", path, "fetch"], check=True)
    subprocess.run(["git", "-C", path, "reset", "--hard", f"origin/{branch}"], check=True)

    # Build Docker image
    subprocess.run(["docker", "build", "-t", repo_config["docker_image"], path], check=True)

    # Stop and remove old container
    subprocess.run(["docker", "stop", repo_config["docker_image"]], check=False)
    subprocess.run(["docker", "rm", repo_config["docker_image"]], check=False)

    # Run container on configured port
    subprocess.run([
        "docker", "run", "-d",
        "--name", repo_config["docker_image"],
        "-p", f"{repo_config['port']}:80",
        repo_config["docker_image"]
    ], check=True)

    # Update Nginx config
    update_nginx(repo_config)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
