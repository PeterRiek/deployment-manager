from pathlib import Path
import subprocess

def build_image(image_name: str, context: str, dockerfile_path: str):
    dockerfile = Path(dockerfile_path)
    ctx = Path(context)

    if not dockerfile.is_file():
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")
    if not ctx.is_dir():
        raise FileNotFoundError(f"Build context not found: {ctx}")

    subprocess.run(
        [
            "docker", "build",
            "-f", str(dockerfile),
            "-t", image_name,
            str(ctx)
        ],
        check=True,
        capture_output=True,
        text=True
    )

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
