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

def run_container(image_name: str, container_name: str, port: int, variables: dict[str, str] = {}):
    args = [
        "docker", "run", "-d",
        "--name", container_name,
        "-p", f"{port}:80",
    ]
    for k, v in variables.items():
        args.append("-e")
        args.append(f"{k}={v}")
    args.append(image_name)

    subprocess.run(args, check=True)
