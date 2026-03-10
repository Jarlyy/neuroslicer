from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import re


TOKEN_PATTERN = re.compile(r"[a-zA-Zа-яА-Я0-9_]+")

RU_EN_SYNONYMS: dict[str, tuple[str, ...]] = {
    "stringing": ("нити", "волосы", "паутинка", "oozing"),
    "layer": ("слой", "слои", "layers"),
    "separation": ("расслоение", "расслаиваются", "delamination"),
    "adhesion": ("адгезия", "прилипание", "липнет", "sticking"),
    "bed": ("стол", "платформа", "plate"),
    "extrusion": ("экструзия", "недоэкструзия", "underextrusion"),
    "warp": ("warping", "коробление", "углы поднимаются"),
    "temperature": ("температура", "temp"),
    "retraction": ("ретракт", "retract"),
}


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
        if not self.entries:
            return []

        query_tokens = _normalize_tokens(_tokenize(user_text))
        if not query_tokens:
            return []

        doc_tokens = [
            _normalize_tokens(
                _tokenize(" ".join([entry.category, *entry.symptoms, *entry.causes, *entry.recommendations]))
            )
            for entry in self.entries
        ]

        idf = _build_idf(doc_tokens)

        scored: list[tuple[float, int, TroubleshootingEntry]] = []
        for idx, entry in enumerate(self.entries):
            score = _bm25_score(query_tokens, doc_tokens[idx], idf, avgdl=_avg_len(doc_tokens))
            overlap_bonus = 0.05 * len(set(query_tokens).intersection(set(doc_tokens[idx])))
            final_score = score + overlap_bonus
            if final_score > 0:
                scored.append((final_score, idx, entry))

        scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
        return [entry for _, _, entry in scored[:top_k]]


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


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _normalize_tokens(tokens: list[str]) -> list[str]:
    expanded: list[str] = []
    synonym_map = _synonym_lookup()
    for token in tokens:
        base = token.strip().lower()
        if not base:
            continue
        expanded.append(base)
        canonical = synonym_map.get(base)
        if canonical and canonical != base:
            expanded.append(canonical)
    return expanded


def _synonym_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, variants in RU_EN_SYNONYMS.items():
        lookup[canonical] = canonical
        for variant in variants:
            lookup[variant.lower()] = canonical
    return lookup


def _build_idf(doc_tokens: list[list[str]]) -> dict[str, float]:
    n_docs = len(doc_tokens)
    df: dict[str, int] = {}
    for tokens in doc_tokens:
        for token in set(tokens):
            df[token] = df.get(token, 0) + 1

    idf: dict[str, float] = {}
    for token, doc_freq in df.items():
        idf[token] = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
    return idf


def _avg_len(doc_tokens: list[list[str]]) -> float:
    return sum(len(tokens) for tokens in doc_tokens) / max(1, len(doc_tokens))


def _bm25_score(query_tokens: list[str], doc_tokens: list[str], idf: dict[str, float], avgdl: float) -> float:
    k1 = 1.5
    b = 0.75
    score = 0.0
    doc_len = max(1, len(doc_tokens))

    tf: dict[str, int] = {}
    for token in doc_tokens:
        tf[token] = tf.get(token, 0) + 1

    for token in set(query_tokens):
        freq = tf.get(token, 0)
        if freq == 0:
            continue
        numer = freq * (k1 + 1)
        denom = freq + k1 * (1 - b + b * doc_len / max(1.0, avgdl))
        score += idf.get(token, 0.0) * (numer / denom)

    return score
