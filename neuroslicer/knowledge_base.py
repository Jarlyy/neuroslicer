from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re


@dataclass(frozen=True)
class TroubleshootingEntry:
    category: str
    symptoms: list[str]
    causes: list[str]
    recommendations: list[str]
    source: str


class KnowledgeBase:
    def __init__(self, entries: list[TroubleshootingEntry]):
        self.entries = entries

    @classmethod
    def from_json(cls, path: str | Path) -> "KnowledgeBase":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        entries = [TroubleshootingEntry(**item) for item in raw]
        return cls(entries)

    @classmethod
    def from_markdown_dir(cls, root: str | Path) -> "KnowledgeBase":
        root_path = Path(root)
        entries: list[TroubleshootingEntry] = []
        for md_file in sorted(root_path.rglob("*.md")):
            text = md_file.read_text(encoding="utf-8", errors="ignore")
            category = _extract_title(text) or md_file.stem.replace("_", " ")
            symptoms = _extract_bullets(text, ("symptom", "problem", "issue", "defect"))
            causes = _extract_bullets(text, ("cause", "reason", "why"))
            recommendations = _extract_bullets(text, ("solution", "fix", "recommend", "action"))
            if symptoms or causes or recommendations:
                entries.append(
                    TroubleshootingEntry(
                        category=category,
                        symptoms=symptoms,
                        causes=causes,
                        recommendations=recommendations,
                        source=str(md_file),
                    )
                )
        return cls(entries)

    def best_matches(self, user_text: str, top_k: int = 3) -> list[TroubleshootingEntry]:
        query_tokens = _tokenize(user_text)
        scored: list[tuple[int, TroubleshootingEntry]] = []

        for entry in self.entries:
            haystack = " ".join([entry.category, *entry.symptoms, *entry.causes, *entry.recommendations])
            haystack_tokens = _tokenize(haystack)
            overlap = len(query_tokens.intersection(haystack_tokens))
            if overlap:
                scored.append((overlap, entry))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]


def _extract_title(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _extract_bullets(text: str, section_keywords: tuple[str, ...]) -> list[str]:
    lines = text.splitlines()
    bullets: list[str] = []
    in_section = False

    for line in lines:
        norm = line.strip().lower()
        if norm.startswith("#"):
            in_section = any(keyword in norm for keyword in section_keywords)
            continue

        if in_section and re.match(r"^[-*+]\s+", line.strip()):
            bullets.append(re.sub(r"^[-*+]\s+", "", line.strip()))

    return bullets


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Zа-яА-Я0-9_]+", text.lower()))
