import os
from pathlib import Path

import yaml


class Config:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "config.yaml")
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def app(self) -> dict:
        return self._config.get("app", {})

    @property
    def auth_config(self) -> dict:
        return self._config.get("auth", {})

    @property
    def processing(self) -> dict:
        return self._config.get("processing", {})

    @property
    def host(self) -> str:
        return self.app.get("host", "0.0.0.0")

    @property
    def port(self) -> int:
        return int(self.app.get("port", 8000))

    @property
    def reload(self) -> bool:
        return self.app.get("reload", False)

    @property
    def allowed_email_domain(self) -> str:
        return self.auth_config.get("allowed_email_domain", "@tp.com.vn")

    @property
    def google_client_id(self) -> str:
        return os.getenv("GOOGLE_CLIENT_ID", "")

    @property
    def google_client_secret(self) -> str:
        return os.getenv("GOOGLE_CLIENT_SECRET", "")

    @property
    def session_secret(self) -> str:
        value = os.getenv("SESSION_SECRET", "").strip()
        if not value:
            raise RuntimeError("SESSION_SECRET environment variable must be set")
        return value

    @property
    def allowed_email_domain_normalized(self) -> str:
        domain = (self.allowed_email_domain or "").strip().lower()
        if domain and not domain.startswith("@"):
            domain = "@" + domain
        return domain

    @property
    def auth_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    def is_email_allowed(self, email: str | None) -> bool:
        if not self.auth_enabled:
            return True
        domain = self.allowed_email_domain_normalized
        if not domain:
            return False
        if not email:
            return False
        return email.strip().lower().endswith(domain)

    @property
    def max_length(self) -> int:
        return self.processing.get("max_length", 32)

    @property
    def lock_timeout(self) -> int:
        return self.processing.get("lock_timeout", 60)

    @property
    def inference_threads(self) -> int:
        return self.processing.get("inference_threads", 10)

    @property
    def batch_max_threads(self) -> int:
        return self.processing.get("batch_max_threads", 32)

    @property
    def batch_max_urls(self) -> int:
        return self.processing.get("batch_max_urls", 50)


config = Config()
