import subprocess

def build_image(image_name: str, context: str, dockerfile_path: str):
    subprocess.run([
        "docker", "build",
        "-f", dockerfile_path,
        "-t", image_name,
        context
    ], check=True)

def stop_container(container_name: str):
    subprocess.run(["docker", "stop", container_name], check=False)
    subprocess.run(["docker", "rm", container_name], check=False)

def run_container(image_name: str, container_name: str, port: int):
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "-p", f"{port}:80",
        image_name
    ], check=True)
