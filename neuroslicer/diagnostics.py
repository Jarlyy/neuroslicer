from __future__ import annotations

from dataclasses import dataclass
import json
import re

from .config import HFConfig
from .hf_client import HFClient
from .knowledge_base import KnowledgeBase, TroubleshootingEntry
from .profile_manager import ProfileAdvisor, ProfileChange


@dataclass(frozen=True)
class Diagnosis:
    defect_type: str
    possible_causes: list[str]
    recommendations: list[str]
    confidence: float
    sources: list[str]
    profile_changes: list[ProfileChange]


class DiagnosticEngine:
    def __init__(self, knowledge_base: KnowledgeBase, hf_config: HFConfig | None = None):
        self.knowledge_base = knowledge_base
        self.hf_config = hf_config or HFConfig.from_env()
        self.profile_advisor = ProfileAdvisor()

    def diagnose(
        self,
        user_text: str,
        use_hf: bool = True,
        profile_parameters: dict[str, str] | None = None,
    ) -> Diagnosis:
        matches = self.knowledge_base.best_matches(user_text, top_k=5)
        if not matches:
            return Diagnosis(
                defect_type="Unknown",
                possible_causes=["Недостаточно данных в базе знаний"],
                recommendations=["Уточните симптомы: материал, температура, скорость, фото дефекта"],
                confidence=0.1,
                sources=[],
                profile_changes=[],
            )

        if use_hf and self.hf_config.enabled:
            prompt = self._build_prompt(user_text, matches, profile_parameters)
            payload = HFClient(self.hf_config).analyze(prompt)
            generated_text = HFClient.extract_text(payload)
            parsed = _parse_llm_json(generated_text)
            if parsed is not None:
                return _diagnosis_from_llm(parsed, matches)

        # Deterministic fallback
        primary = matches[0]
        confidence = min(0.95, 0.45 + 0.1 * len(matches))
        changes: list[ProfileChange] = []
        if profile_parameters is not None:
            changes = self.profile_advisor.suggest_changes(primary.category, profile_parameters)

        return Diagnosis(
            defect_type=primary.category,
            possible_causes=_dedupe([cause for m in matches for cause in m.causes])[:5],
            recommendations=_dedupe([rec for m in matches for rec in m.recommendations])[:8],
            confidence=confidence,
            sources=[m.source for m in matches],
            profile_changes=changes,
        )

    @staticmethod
    def _build_prompt(
        user_text: str,
        matches: list[TroubleshootingEntry],
        profile_parameters: dict[str, str] | None,
    ) -> str:
        lines = [
            "Ты эксперт по 3D-печати и OrcaSlicer.",
            "Используй ТОЛЬКО кейсы из troubleshooting guide ниже как базу знаний.",
            "Верни ответ СТРОГО в JSON без markdown.",
            "JSON schema:",
            '{"defect_type":"...","causes":["..."],"recommendations":["..."],'
            '"confidence":0.0,"parameter_changes":[{"parameter":"...","new_value":"...","reason":"..."}]}',
            f"Жалоба пользователя: {user_text}",
            "Релевантные кейсы из guide:",
        ]
        for idx, item in enumerate(matches, start=1):
            lines.append(f"[{idx}] category={item.category}")
            if item.symptoms:
                lines.append("symptoms: " + " | ".join(item.symptoms[:5]))
            if item.causes:
                lines.append("causes: " + " | ".join(item.causes[:5]))
            if item.recommendations:
                lines.append("recommendations: " + " | ".join(item.recommendations[:6]))

        if profile_parameters:
            rendered = ", ".join(f"{k}={v}" for k, v in list(profile_parameters.items())[:40])
            lines.append("Текущие параметры профиля: " + rendered)
            lines.append("Если можешь, предложи parameter_changes для этих параметров.")
        else:
            lines.append("Если нет профиля, parameter_changes можно вернуть пустым массивом.")

        return "\n".join(lines)


def _parse_llm_json(generated_text: str) -> dict | None:
    try:
        return json.loads(generated_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", generated_text, flags=re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _diagnosis_from_llm(parsed: dict, matches: list[TroubleshootingEntry]) -> Diagnosis:
    defect_type = str(parsed.get("defect_type") or matches[0].category)
    causes = [str(v) for v in parsed.get("causes", []) if str(v).strip()]
    recommendations = [str(v) for v in parsed.get("recommendations", []) if str(v).strip()]
    confidence = float(parsed.get("confidence", 0.7))

    raw_changes = parsed.get("parameter_changes", [])
    changes: list[ProfileChange] = []
    if isinstance(raw_changes, list):
        for item in raw_changes:
            if not isinstance(item, dict):
                continue
            param = str(item.get("parameter", "")).strip()
            new_value = str(item.get("new_value", "")).strip()
            reason = str(item.get("reason", "AI suggestion")).strip() or "AI suggestion"
            if not param or not new_value:
                continue
            changes.append(ProfileChange(parameter=param, old_value="", new_value=new_value, reason=reason))

    if not causes:
        causes = _dedupe([cause for m in matches for cause in m.causes])[:5]
    if not recommendations:
        recommendations = _dedupe([rec for m in matches for rec in m.recommendations])[:8]

    return Diagnosis(
        defect_type=defect_type,
        possible_causes=causes[:5],
        recommendations=recommendations[:8],
        confidence=max(0.0, min(1.0, confidence)),
        sources=[m.source for m in matches],
        profile_changes=changes,
    )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result
