import subprocess
import os

def check_repo(directory: str, repo_url: str) -> bool:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).stdout.strip()
        print("[check_repo]", res)
        url = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=directory, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        ).stdout.strip()
        print("[check_repo]", url)
        return url == repo_url
    except subprocess.CalledProcessError:
        print("[check_repo] CalledProcessError")
        return False

def clone_repo(directory: str, repo_url: str, branch: str):
    os.makedirs(directory, exist_ok=True)
    subprocess.run(
        ["git", "clone", "-b", branch, repo_url, directory],
        check=True
    )

def pull_latest(directory: str, branch: str):
    subprocess.run(["git", "-C", directory, "fetch"], check=True)
    subprocess.run(["git", "-C", directory, "reset", "--hard", f"origin/{branch}"], check=True)
