from pathlib import Path

from neuroslicer.knowledge_base import KnowledgeBase


def test_best_matches_from_seed_json():
    kb = KnowledgeBase.from_json("data/troubleshooting_seed.json")
    matches = kb.best_matches("деталь ломается между слоями", top_k=2)
    assert matches
    assert matches[0].category == "Layer Separation"


def test_markdown_loader(tmp_path: Path):
    md = tmp_path / "case.md"
    md.write_text(
        "# Stringing\n\n## Symptoms\n- hairs\n\n## Causes\n- high temp\n\n## Solutions\n- lower temp\n",
        encoding="utf-8",
    )
    kb = KnowledgeBase.from_markdown_dir(tmp_path)
    assert len(kb.entries) == 1
    assert kb.entries[0].category == "Stringing"
