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
    def model(self) -> dict:
        return self._config.get("model", {})

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
    def default_model_name(self) -> str:
        return self.model.get("default", "vit-gpt2")

    @property
    def available_models(self) -> dict:
        return self.model.get("available", {
            "vit-gpt2": "nlpconnect/vit-gpt2-image-captioning"
        })

    def get_model_path(self, model_key: str) -> str:
        return self.available_models.get(model_key)

    @property
    def max_length(self) -> int:
        return self.processing.get("max_length", 32)

    @property
    def num_beams(self) -> int:
        return self.processing.get("num_beams", 4)

    @property
    def default_num_tags(self) -> int:
        return self.processing.get("default_num_tags", 10)

    @property
    def max_num_tags(self) -> int:
        return self.processing.get("max_num_tags", 50)


config = Config()
