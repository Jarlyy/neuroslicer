from __future__ import annotations

from dataclasses import dataclass

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
        use_hf: bool = False,
        profile_parameters: dict[str, str] | None = None,
    ) -> Diagnosis:
        matches = self.knowledge_base.best_matches(user_text, top_k=3)
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
            prompt = self._build_prompt(user_text, matches)
            _ = HFClient(self.hf_config).analyze(prompt)

        primary = matches[0]
        confidence = min(0.95, 0.45 + 0.15 * len(matches))
        changes = []
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
    def _build_prompt(user_text: str, matches: list[TroubleshootingEntry]) -> str:
        lines = [
            "Ты помощник по 3D-печати. На основе кейсов сформируй диагноз и шаги коррекции.",
            f"Запрос пользователя: {user_text}",
            "Релевантные кейсы:",
        ]
        for idx, item in enumerate(matches, start=1):
            lines.append(f"{idx}. {item.category}")
            if item.causes:
                lines.append("Причины: " + "; ".join(item.causes[:3]))
            if item.recommendations:
                lines.append("Решения: " + "; ".join(item.recommendations[:4]))
        lines.append("Верни кратко: defect_type, causes(до3), recommendations(до5).")
        return "\n".join(lines)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result
