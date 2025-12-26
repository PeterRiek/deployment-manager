import os
import subprocess

def update_nginx(server: str, name: str, port: int, route: str):
    nginx_file = f"/etc/nginx/sites-available/{name}.conf"
    location_block = f"""
server {{
    listen 80;
    server_name {server};

    location {route} {{
        proxy_pass http://localhost:{port}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    with open(nginx_file, "w") as f:
        f.write(location_block)

    symlink = f"/etc/nginx/sites-enabled/{name}.conf"
    if not os.path.exists(symlink):
        os.symlink(nginx_file, symlink)

    subprocess.run(["nginx", "-t"], check=True)
    subprocess.run(["systemctl", "reload", "nginx"], check=True)
