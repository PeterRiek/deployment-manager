from flask import Flask, request
from dotenv import load_dotenv
import os

load_dotenv()

from config import get_deployment
from repo import check_repo, clone_repo, pull_latest
from docker_ops import build_image, stop_container, run_container
from nginx import update_nginx

app = Flask(__name__)

@app.route("/hook", methods=["POST"])
def hook():
    data = request.json
    repo = data["repository"]["full_name"]
    branch = data["ref"].split('/')[-1]

    deployment = get_deployment(repo, branch)
    if not deployment:
        return "No matching deployment", 200

    name = deployment["name"]
    directory = f"/opt/apps/{name}"
    repo_url = f"https://github.com/{repo}.git"
    port = deployment["port"]
    route = deployment["route"]
    server = deployment["server"]
    dockerfile_path = os.path.join(directory, deployment.get("dockerfile", "Dockerfile"))

    if not os.path.isdir(directory):
        clone_repo(directory, repo_url, branch)
    elif not check_repo(directory, repo_url):
        return f"Deployment conflict for {repo_url}", 400

    pull_latest(directory, branch)
    image_name = f"{repo.replace('/', '_')}:{branch}"

    build_image(image_name, directory, dockerfile_path)
    stop_container(name)
    run_container(image_name, name, port)
    update_nginx(server, name, port, route)

    return "Deployment successful", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
