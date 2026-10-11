import base64
import os

from dotenv import load_dotenv


def _decode_password(value):
    if not value:
        return ""
    try:
        return base64.b64decode(value, validate=True).decode("utf-8")
    except Exception:
        return value


def load_config():
    """Load .env (or the file named by ENV_FILE) unless running in Docker/Rundeck."""
    if not (os.getenv("RUNDECK_JOB_ID") or os.getenv("DOCKER_CONTAINER_RUN")):
        load_dotenv(os.getenv("ENV_FILE", ".env"))
    return {
        "env_name": os.getenv("ENV_NAME", ""),
        "host": os.getenv("EPP_HOST", "").strip(),
        "port": os.getenv("EPP_PORT", "700").strip(),
        "user": os.getenv("EPP_USER", ""),
        "pwd": _decode_password(os.getenv("EPP_PWD", "")),
        "registrar_contact": os.getenv("REGISTRAR_CONTACT", ""),
    }
