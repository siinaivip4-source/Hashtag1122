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
