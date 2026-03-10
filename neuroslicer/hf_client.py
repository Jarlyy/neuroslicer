from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
from urllib import request
from urllib.error import HTTPError, URLError

from .config import HFConfig


@dataclass
class HFClient:
    config: HFConfig

    def analyze(self, prompt: str, timeout_s: float = 20.0) -> dict[str, Any]:
        if not self.config.enabled:
            raise RuntimeError("HF token is not configured. Set HF_TOKEN.")

        payload = json.dumps({"inputs": prompt}).encode("utf-8")
        req = request.Request(
            self.config.endpoint(),
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=timeout_s) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HF API error: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"HF API connection error: {exc.reason}") from exc

        return json.loads(body)
