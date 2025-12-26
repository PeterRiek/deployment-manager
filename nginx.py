from pathlib import Path
import subprocess

from config import load_config

def update_nginx_from_config(nginx_conf_path: str):
    """
    Generate a single Nginx config for all deployments (dashboard + webhook + apps)
    and safely symlink it to sites-enabled.
    """

    config = load_config()

    # Collect all server names
    server_name_set = set(dep["server"] for dep in config["deployments"])
    if len(server_name_set) > 1:
        print("Warning: multiple server_names detected. Each server will get its own server block.")

    # Group deployments by server
    servers = {}
    for dep in config["deployments"]:
        servers.setdefault(dep["server"], []).append(dep)

    nginx_lines = []

    for server, deployments in servers.items():
        nginx_lines.append(f"server {{")
        nginx_lines.append(f"    listen 80;")
        nginx_lines.append(f"    server_name {server};")
        nginx_lines.append("")

        # Streamlit dashboard
        nginx_lines.append("    # Streamlit dashboard")
        nginx_lines.append("    location /deploy/ {")
        nginx_lines.append("        proxy_pass http://127.0.0.1:8501/;")
        nginx_lines.append("        proxy_http_version 1.1;")
        nginx_lines.append("        proxy_set_header Upgrade $http_upgrade;")
        nginx_lines.append("        proxy_set_header Connection \"upgrade\";")
        nginx_lines.append("        proxy_set_header Host $host;")
        nginx_lines.append("    }\n")

        # Flask webhook
        nginx_lines.append("    # Flask webhook")
        nginx_lines.append("    location /deploy/hook {")
        nginx_lines.append("        proxy_pass http://127.0.0.1:9000/hook;")
        nginx_lines.append("        proxy_set_header Host $host;")
        nginx_lines.append("        proxy_set_header X-Real-IP $remote_addr;")
        nginx_lines.append("        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
        nginx_lines.append("    }\n")

        # Deployments
        for dep in deployments:
            route = dep["route"].rstrip("/") + "/"
            port = dep["port"]
            nginx_lines.append(f"    # Deployment {dep['name']}")
            nginx_lines.append(f"    location {route} {{")
            nginx_lines.append(f"        proxy_pass http://127.0.0.1:{port}/;")
            nginx_lines.append(f"        proxy_http_version 1.1;")
            nginx_lines.append(f"        proxy_set_header Upgrade $http_upgrade;")
            nginx_lines.append(f"        proxy_set_header Connection \"upgrade\";")
            nginx_lines.append(f"        proxy_set_header Host $host;")
            nginx_lines.append(f"    }}\n")

        nginx_lines.append("}\n")

    # Write config
    Path(nginx_conf_path).write_text("\n".join(nginx_lines))
    print(f"Nginx config written to {nginx_conf_path}")

    # Symlink to sites-enabled
    enabled_path = "/etc/nginx/sites-enabled/" + Path(nginx_conf_path).name
    if Path(enabled_path).exists():
        Path(enabled_path).unlink()
    Path(enabled_path).symlink_to(nginx_conf_path)
    print(f"Symlinked to {enabled_path}")

    # Test and reload nginx
    try:
        subprocess.run(["nginx", "-t"], check=True)
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
        print("Nginx reloaded successfully")
    except subprocess.CalledProcessError:
        print("Error: Nginx test or reload failed")
