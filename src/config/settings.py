"""Central application configuration loaded from project-root config.json."""
import json
import os
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(os.getenv("EWALLET_CONFIG", PROJECT_ROOT / "config.json"))

@lru_cache(maxsize=1)
def get_settings():
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Configuration file not found: {CONFIG_PATH}. Copy config.example.json to config.json.")
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    # Environment overrides support deployment secrets without editing the file.
    db = data.setdefault("database", {})
    for key, env in (("host", "DB_HOST"), ("port", "DB_PORT"), ("user", "DB_USER"), ("password", "DB_PASSWORD"), ("name", "DB_NAME")):
        if os.getenv(env): db[key] = int(os.environ[env]) if key == "port" else os.environ[env]
    sec = data.setdefault("security", {})
    if os.getenv("EWALLET_TOKEN_SECRET"): sec["token_secret"] = os.environ["EWALLET_TOKEN_SECRET"]
    data["admin_accounts"] = [str(x).strip() for x in data.get("admin_accounts", []) if str(x).strip()]
    required_db = ("host", "user", "password", "name")
    missing = [key for key in required_db if not db.get(key) or str(db[key]).startswith("CHANGE_ME")]
    if missing:
        raise RuntimeError("Set database fields in config.json before starting the API: " + ", ".join(missing))
    if not sec.get("token_secret") or str(sec["token_secret"]).startswith("CHANGE_THIS"):
        raise RuntimeError("Set a unique, long security.token_secret in config.json before starting the API.")
    return data
