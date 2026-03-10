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

    def analyze(self, prompt: str, timeout_s: float = 30.0) -> Any:
        if not self.config.enabled:
            raise RuntimeError("HF token is not configured. Set HF_TOKEN.")

        payload = json.dumps(
            {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 700,
                    "temperature": 0.2,
                    "return_full_text": False,
                },
            }
        ).encode("utf-8")
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

    @staticmethod
    def extract_text(response_payload: Any) -> str:
        if isinstance(response_payload, list) and response_payload:
            first = response_payload[0]
            if isinstance(first, dict):
                if "generated_text" in first:
                    return str(first["generated_text"])
                if "summary_text" in first:
                    return str(first["summary_text"])
        if isinstance(response_payload, dict):
            if "generated_text" in response_payload:
                return str(response_payload["generated_text"])
            if "error" in response_payload:
                raise RuntimeError(f"HF model error: {response_payload['error']}")
        return json.dumps(response_payload, ensure_ascii=False)
