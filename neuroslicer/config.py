from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HFConfig:
    token: str | None
    model_id: str = "openai/gpt-oss-120b"
    base_url: str = "https://api-inference.huggingface.co/models"

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    @classmethod
    def from_env(cls) -> "HFConfig":
        return cls(
            token=os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            model_id=os.getenv("HF_MODEL_ID", "openai/gpt-oss-120b"),
        )

    def endpoint(self) -> str:
        return f"{self.base_url}/{self.model_id}"
