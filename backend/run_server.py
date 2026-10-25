"""
Resilient Backend Server Launcher for AI Certificate Verification Platform.
Includes automatic zombie process cleanup on target port, watch-reload loop prevention,
and top-level exception guards.
"""

import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# Ensure paths
_backend_dir = Path(__file__).resolve().parent
_root_dir = _backend_dir.parent
sys.path.insert(0, str(_backend_dir))
sys.path.insert(0, str(_root_dir))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("server_launcher")


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently held or bound by testing bindability and connectivity."""
    # Check 1: Active listener responding to connections
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex((host, port)) == 0:
            return True

    # Check 2: Can we bind to it? If not, an orphan/zombie process is holding the socket (e.g. Bound state)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def kill_process_on_port(port: int) -> None:
    """Forcefully terminate orphan/zombie processes holding the specified port."""
    if not is_port_in_use(port):
        return

    logger.info("Port %d is already in use. Cleaning up orphan processes...", port)

    if sys.platform == "win32":
        try:
            my_pid = os.getpid()
            # Use PowerShell to find and kill process on port, excluding self
            cmd = (
                f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
                f"Where-Object {{ $_.OwningProcess -ne {my_pid} -and $_.OwningProcess -ne 0 }} | "
                f"ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=5
            )
            time.sleep(1.0)
        except Exception as e:
            logger.warning("PowerShell port cleanup error: %s", e)

        # Fallback to netstat + taskkill if still in use
        if is_port_in_use(port):
            try:
                res = subprocess.run(
                    f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True
                )
                listening_lines = [
                    conn_line.strip()
                    for conn_line in res.stdout.strip().splitlines()
                    if "LISTENING" in conn_line
                ]
                for conn_line in listening_lines:
                    parts = conn_line.split()
                    pid = parts[-1]
                    if pid and pid != "0":
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                time.sleep(1.0)
            except Exception as e:
                logger.warning("Taskkill fallback warning: %s", e)
    else:
        try:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
            time.sleep(1.0)
        except Exception as e:
            logger.warning("Unix fuser cleanup warning: %s", e)

    if is_port_in_use(port):
        logger.error("Port %d could not be automatically cleared.", port)
    else:
        logger.info("Port %d is clean and ready.", port)


def run():
    target_port = int(os.environ.get("BACKEND_PORT", 8000))
    target_host = os.environ.get("BACKEND_HOST", "0.0.0.0")

    # Clean up orphan processes
    kill_process_on_port(target_port)

    import uvicorn

    logger.info("=" * 60)
    logger.info("Starting Resilient FastAPI Backend on http://%s:%d", target_host, target_port)
    logger.info("Hot-reload watcher constrained to 'app/' directory only.")
    logger.info("Ignored patterns: storage/*, data/*, *.db*, *.log, temp/*, uploads/*")
    logger.info("=" * 60)

    # Watcher configuration:
    # 1. reload_dirs=['app']: Prevents uvicorn from watching storage/, data/, logs/, etc.
    # 2. reload_excludes: Explicit protection against database and upload file events.
    uvicorn.run(
        "app.main:app",
        host=target_host,
        port=target_port,
        reload=True,
        reload_dirs=[str(_backend_dir / "app")],
        reload_excludes=[
            "storage/*",
            "data/*",
            "*.db*",
            "*.db-journal",
            "*.log",
            "temp/*",
            "uploads/*",
            "*.tmp",
            "__pycache__/*",
            ".pytest_cache/*",
        ],
        access_log=True,
        log_level="info",
        timeout_keep_alive=180,
        limit_concurrency=100,
        timeout_graceful_shutdown=15,
    )


if __name__ == "__main__":
    run()
