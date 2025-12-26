# Deployment Manager

A **Flask-based GitHub webhook deployment manager** with **Docker-based deployment automation** and a **Streamlit dashboard** for managing deployment configuration. Supports multiple deployments, branch-based auto-deploy, Nginx reverse proxy configuration, and private network dashboard access.

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Directory Structure](#directory-structure)
4. [Environment Setup](#environment-setup)
5. [Configuration](#configuration)
6. [Running the Services](#running-the-services)
7. [Systemd Setup](#systemd-setup)
8. [Security Considerations](#security-considerations)
9. [Using the Dashboard](#using-the-dashboard)
10. [Deployment Workflow](#deployment-workflow)
11. [Troubleshooting](#troubleshooting)

---

## Features

* Webhook-based deployment automation triggered by Git pushes
* Multi-deployment support with per-deployment configuration
* Docker-based build, run, and management of applications
* Automatic Nginx configuration for routing deployed apps
* Streamlit dashboard to **view and edit deployment configuration live**
* Deployment state tracking with last-deploy timestamp and container status
* Secure operation on private network or VPN

---

## Prerequisites

### 1. Operating System

* Linux (Ubuntu 20.04+ recommended)

### 2. System Packages

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx docker.io
```

* `git`: To clone and manage repositories
* `python3`, `python3-venv`, `pip`: For Python environment
* `nginx`: Reverse proxy for deployed applications and dashboard
* `docker.io`: Container runtime

### 3. Python Packages

Inside your project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` includes:

```
Flask>=2.3
python-dotenv>=1.0
streamlit>=1.25
```

---

### 4. Firewall / Network

* Ensure ports `9000` (Flask webhook) and `8501` (Streamlit dashboard) are open **only on private network or VPN**
* Optional UFW configuration:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 9000
sudo ufw allow from 192.168.1.0/24 to any port 8501
sudo ufw enable
```

---

### 5. User Permissions

* Docker: Add your service user to `docker` group:

```bash
sudo usermod -aG docker deploymgr
```

* Nginx: Must be able to read `/etc/nginx/sites-available` and `/etc/nginx/sites-enabled`

---

## Directory Structure

```
deployment-manager/
├─ app.py                  # Flask webhook API
├─ dashboard.py            # Streamlit admin dashboard
├─ config.py               # Config loader/editor (JSON-based)
├─ repo.py                 # Git operations
├─ docker_ops.py           # Docker build/run/stop operations
├─ nginx.py                # Nginx configuration utilities
├─ config.json             # Deployment configuration storage
├─ requirements.txt        # Python dependencies
├─ .env                    # Environment variables
├─ README.md               # Project documentation
├─ .git/                   # Git repository
└─ .venv/                  # Python virtual environment
```

> `state.py` is no longer used; configuration and state are managed directly via `config.json`.

---

## Environment Setup

1. Copy `.env.example` to `.env` (or create `.env`):

```bash
cp .env.example .env
```

2. Set the config file path in `.env`:

```
CONFIG_FILE=/opt/deployment-manager/config.json
NGINX_CONFIG_FILE=/etc/nginx/sites-available/deploy.conf
```

3. Activate Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration (`config.json`)

```json
{
  "deployments": [
    {
      "name": "geoguessr-clone-prod",
      "repo": "PeterRiek/geoguessr-clone",
      "branch": "main",
      "port": 9001,
      "route": "/geoguessr",
      "server": "host.riek.me",
      "dockerfile_path": "Dockerfile"
    }
  ]
}
```

* `name`: Unique deployment identifier
* `repo`: GitHub repository (`org/repo`)
* `branch`: Branch to auto-deploy
* `port`: Local port for Docker container
* `route`: URL path for Nginx reverse proxy
* `server`: Nginx `server_name`
* `dockerfile_path`: Path to Dockerfile relative to repo root

> Streamlit dashboard allows live editing and saving of this file.

---

## Running the Services

### Flask Hook

```bash
source .venv/bin/activate
python app.py
```

* Listens on port `9000`
* Accepts GitHub webhook POSTs

### Streamlit Dashboard

```bash
source .venv/bin/activate
streamlit run dashboard.py \
  --server.address=127.0.0.1 \
  --server.port=8501 \
  --server.headless=true
```

---

## Systemd Setup

### Flask Webhook (`/etc/systemd/system/deployment-hook.service`)

```ini
[Unit]
Description=Deployment Manager Webhook API
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=deploymgr
WorkingDirectory=/opt/deployment-manager
Environment="CONFIG_FILE=/opt/deployment-manager/config.json"
ExecStart=/opt/deployment-manager/.venv/bin/python app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Streamlit Dashboard (`/etc/systemd/system/deployment-dashboard.service`)

```ini
[Unit]
Description=Deployment Manager Dashboard
After=network.target deployment-hook.service
Requires=deployment-hook.service

[Service]
Type=simple
User=deploymgr
WorkingDirectory=/opt/deployment-manager
Environment="CONFIG_FILE=/opt/deployment-manager/config.json"
ExecStart=/opt/deployment-manager/.venv/bin/streamlit run dashboard.py \
  --server.address=127.0.0.1 \
  --server.port=8501 \
  --server.headless=true \
  --server.enableCORS=false
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable deployment-hook deployment-dashboard
sudo systemctl start deployment-hook deployment-dashboard
```

---

## Security Considerations

* **Dashboard should never be public** — bind to `127.0.0.1` or a private IP
* Use **VPN or private network** for access
* Apply **firewall rules** or **Nginx access control**
* Run services as a **dedicated non-root user** (`deploymgr`)
* Only use Docker images from trusted sources
* Backup `config.json` regularly

---

## Using the Dashboard

* Access via `http://<private-ip>:8501/` (or reverse-proxied `/deploy/`)
* View all deployments, status, and last deploy time
* Add, edit, or delete deployments
* Click **Save All Changes** to persist configuration

> Changes are immediately reflected in the webhook deployment process.

---

## Deployment Workflow

1. Add a deployment via the dashboard or manually in `config.json`
2. Configure GitHub webhook pointing to `http://<server>:9000/hook`
3. Push to the configured branch → webhook triggers deployment
4. Docker container is built, old container stopped, Nginx updated automatically
5. Dashboard reflects new deployment state

---

## Troubleshooting

### Check Logs

```bash
journalctl -u deployment-hook -f
journalctl -u deployment-dashboard -f
```

### Docker Issues

* List containers:

```bash
docker ps -a
```

* Remove failed containers:

```bash
docker rm <container-name>
```

### Nginx Test

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Streamlit Not Loading

* Ensure bound IP matches private network
* Firewall allows port 8501
* Check journal logs

---

## Notes

* Always use HTTPS when exposing Nginx externally
* Backup `config.json` before major changes
* Use consistent branch naming to avoid accidental production deployment
