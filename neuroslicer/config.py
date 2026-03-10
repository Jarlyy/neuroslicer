from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HFConfig:
    token: str | None
    model_id: str = "openai/gpt-oss-120b"
    router_base_url: str = "https://router.huggingface.co"
    endpoint_override: str | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    @classmethod
    def from_env(cls) -> "HFConfig":
        return cls(
            token=os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            model_id=os.getenv("HF_MODEL_ID", "openai/gpt-oss-120b"),
            router_base_url=os.getenv("HF_ROUTER_BASE_URL", "https://router.huggingface.co"),
            endpoint_override=os.getenv("HF_ENDPOINT"),
        )

    def endpoint(self) -> str:
        if self.endpoint_override:
            return self.endpoint_override
        return f"{self.router_base_url}/hf-inference/models/{self.model_id}"
