"""
Legacy single-file deployment script. Superseded by deploy.py which uploads
the entire project. Kept for reference. Reads creds from env / .deploy.env.
"""
import os
import sys
import paramiko
from pathlib import Path

# Load creds from .deploy.env if present
_env = Path(__file__).resolve().parent.parent.parent / ".deploy.env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

HOST = os.environ.get("ASTROBOT_HOST", "")
PORT = int(os.environ.get("ASTROBOT_PORT", "22"))
USERNAME = os.environ.get("ASTROBOT_USER", "")
PASSWORD = os.environ.get("ASTROBOT_PASSWORD", "")
REMOTE_ROOT = os.environ.get("ASTROBOT_REMOTE_ROOT", f"/home/{USERNAME}/astrobot")
LOCAL_ROOT = Path(__file__).resolve().parent.parent.parent

if not (HOST and USERNAME and PASSWORD):
    print("Missing ASTROBOT_HOST / ASTROBOT_USER / ASTROBOT_PASSWORD. Edit .deploy.env.")
    sys.exit(1)

FILES = [
    {"local": str(LOCAL_ROOT / "frontend" / "index.html"), "remote": f"{REMOTE_ROOT}/frontend/index.html"},
    {"local": str(LOCAL_ROOT / "frontend" / "style.css"),  "remote": f"{REMOTE_ROOT}/frontend/style.css"},
]

DOCKER_CMD = f"cd {REMOTE_ROOT}/docker && docker compose up -d --build"

VERIFY_CMD = "docker ps | grep astrobot"


def run_command(ssh_client, cmd, description=""):
    print(f"\n--- {description or cmd[:80]} ---")
    stdin, stdout, stderr = ssh_client.exec_command(cmd, get_pty=True, timeout=300)
    # Stream output line by line
    for line in iter(stdout.readline, ""):
        print(line, end="", flush=True)
    exit_code = stdout.channel.recv_exit_status()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if err:
        print(f"STDERR: {err}")
    print(f"[exit code: {exit_code}]")
    return exit_code, err


def main():
    print(f"Connecting to {HOST}:{PORT} as {USERNAME} ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
        print("SSH connection established.")
    except Exception as e:
        print(f"ERROR: Could not connect — {e}")
        sys.exit(1)

    # ── Upload files via SFTP ──────────────────────────────────────────────
    print("\n=== Uploading files via SFTP ===")
    try:
        sftp = ssh.open_sftp()
        for f in FILES:
            print(f"  Uploading {f['local']}  ->  {f['remote']}")
            sftp.put(f["local"], f["remote"])
            print("  Done.")
        sftp.close()
        print("All files uploaded successfully.")
    except Exception as e:
        print(f"ERROR during SFTP upload: {e}")
        ssh.close()
        sys.exit(1)

    # ── Docker rebuild & run ───────────────────────────────────────────────
    print("\n=== Running Docker build & run ===")
    exit_code, _ = run_command(ssh, DOCKER_CMD, "docker build + run")
    if exit_code not in (0, None):
        print(f"WARNING: Docker command exited with code {exit_code}.")

    # ── Verify container is running ────────────────────────────────────────
    print("\n=== Verifying container is running ===")
    exit_code, _ = run_command(ssh, VERIFY_CMD, "docker ps | grep astrobot")
    if exit_code == 0:
        print("\nSUCCESS: astrobot container is running.")
    else:
        print("\nWARNING: 'astrobot' not found in docker ps output — container may not be running.")

    ssh.close()
    print("\nSSH connection closed.")


if __name__ == "__main__":
    main()
