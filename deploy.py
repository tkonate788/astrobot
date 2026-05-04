#!/usr/bin/env python3
"""
AstroBot V2 — Full deployment script.

Packages the whole project (frontend, backend, docker/), uploads it to the
server via SFTP, then rebuilds and restarts the container using docker-compose.

Usage:
    python deploy.py
"""

import os
import sys
import tarfile
import tempfile
from pathlib import Path

import paramiko

# ── Config (read from environment to avoid committing secrets) ─────────
# Set these via env vars or a local `.deploy.env` file (gitignored):
#   ASTROBOT_HOST, ASTROBOT_PORT, ASTROBOT_USER, ASTROBOT_PASSWORD,
#   ASTROBOT_REMOTE_ROOT
HOST = os.environ.get("ASTROBOT_HOST", "")
PORT = int(os.environ.get("ASTROBOT_PORT", "22"))
USERNAME = os.environ.get("ASTROBOT_USER", "")
PASSWORD = os.environ.get("ASTROBOT_PASSWORD", "")

# Try loading from a local .deploy.env if env vars are missing
if not (HOST and USERNAME and PASSWORD):
    env_file = Path(__file__).resolve().parent / ".deploy.env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        HOST = os.environ.get("ASTROBOT_HOST", HOST)
        PORT = int(os.environ.get("ASTROBOT_PORT", str(PORT)))
        USERNAME = os.environ.get("ASTROBOT_USER", USERNAME)
        PASSWORD = os.environ.get("ASTROBOT_PASSWORD", PASSWORD)

if not (HOST and USERNAME and PASSWORD):
    print("ERROR: missing deployment credentials.")
    print("Set ASTROBOT_HOST, ASTROBOT_USER, ASTROBOT_PASSWORD as env vars,")
    print("or create a `.deploy.env` file next to deploy.py with those keys.")
    sys.exit(1)

LOCAL_ROOT = Path(__file__).resolve().parent
REMOTE_ROOT = os.environ.get("ASTROBOT_REMOTE_ROOT", "/home/" + USERNAME + "/astrobot")

# Files/dirs to include in the tarball (relative to LOCAL_ROOT)
INCLUDE = [
    "frontend",
    "backend",
    "admin",
    "docker",
    "README.md",
]

# Directories to exclude (bloat)
EXCLUDE_DIRS = {"node_modules", ".git", ".claude", "__pycache__"}

# Commands to run on the server after upload
REMOTE_CMDS = [
    # Make sure target dir exists
    f"mkdir -p {REMOTE_ROOT}",
    # Extract (overwriting previous files, keeping anything else on the host)
    f"tar -xzf /tmp/astrobot_deploy.tar.gz -C {REMOTE_ROOT}",
    # Clean up archive
    "rm -f /tmp/astrobot_deploy.tar.gz",
    # Stop + remove any previous astrobot containers (safe if absent)
    "docker stop astrobot astrobot-admin 2>/dev/null; docker rm astrobot astrobot-admin 2>/dev/null; true",
    # Rebuild + restart via docker-compose (compose file is in docker/)
    f"cd {REMOTE_ROOT}/docker && docker compose up -d --build",
    # Verify
    "docker ps --filter name=astrobot --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'",
]


# ── Helpers ─────────────────────────────────────────────────────────────
def _excluded(path: Path) -> bool:
    """Return True if any directory component of `path` is in EXCLUDE_DIRS."""
    return any(part in EXCLUDE_DIRS for part in path.parts)


def build_tarball() -> Path:
    """Create a gzipped tarball of the project (selected dirs/files)."""
    tmp = Path(tempfile.mkdtemp()) / "astrobot_deploy.tar.gz"
    print(f"\n[1/4] Building archive -> {tmp}")

    with tarfile.open(tmp, "w:gz") as tar:
        for rel in INCLUDE:
            src = LOCAL_ROOT / rel
            if not src.exists():
                print(f"  WARN: missing {src}, skipping")
                continue
            if src.is_file():
                tar.add(src, arcname=rel)
                print(f"  + {rel}")
                continue
            # Directory: walk and add files, excluding bloat
            for root, dirs, files in os.walk(src):
                # Prune excluded dirs in-place
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                root_path = Path(root)
                for f in files:
                    fp = root_path / f
                    if _excluded(fp.relative_to(LOCAL_ROOT)):
                        continue
                    arc = fp.relative_to(LOCAL_ROOT).as_posix()
                    tar.add(fp, arcname=arc)
    size_kb = tmp.stat().st_size / 1024
    print(f"  Archive ready — {size_kb:.1f} KB")
    return tmp


def ssh_connect() -> paramiko.SSHClient:
    print(f"\n[2/4] Connecting to {USERNAME}@{HOST}:{PORT} ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    print("  Connected.")
    return ssh


def upload(ssh: paramiko.SSHClient, local: Path):
    print(f"\n[3/4] Uploading {local.name} via SFTP ...")
    sftp = ssh.open_sftp()
    sftp.put(str(local), "/tmp/astrobot_deploy.tar.gz")
    sftp.close()
    print("  Upload complete.")


def run_cmd(ssh: paramiko.SSHClient, cmd: str) -> int:
    print(f"\n  $ {cmd}")
    # Use sudo -S with password piped for docker commands that need privileges
    # (Not used here — user 'tidiane' is in docker group per existing setup)
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=600)
    for line in iter(stdout.readline, ""):
        print("  " + line, end="", flush=True)
    code = stdout.channel.recv_exit_status()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if err:
        print("  STDERR: " + err)
    return code


def deploy():
    archive = build_tarball()
    ssh = ssh_connect()
    try:
        upload(ssh, archive)

        print("\n[4/4] Running remote commands ...")
        for cmd in REMOTE_CMDS:
            code = run_cmd(ssh, cmd)
            # docker-compose up returns 0; tolerate non-zero from the stop-if-exists line
            if code != 0 and "stop astrobot" not in cmd:
                print(f"  WARN: exit code {code} on: {cmd}")
        print("\nDone. AstroBot V2 should now be live on http://%s:3000" % HOST)
    finally:
        ssh.close()
        try:
            archive.unlink()
            archive.parent.rmdir()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        deploy()
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
