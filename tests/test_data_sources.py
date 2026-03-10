from __future__ import annotations

import argparse
from pathlib import Path

from neuroslicer.cli import _load_knowledge_base
from neuroslicer.data_sources import detect_troubleshooting_guide


def test_detect_troubleshooting_guide_from_env(monkeypatch, tmp_path: Path):
    guide = tmp_path / "3D-printing-troubleshooting-guide"
    guide.mkdir()
    monkeypatch.setenv("TROUBLESHOOTING_GUIDE_DIR", str(guide))

    detected = detect_troubleshooting_guide(tmp_path)
    assert detected == guide.resolve()


def test_cli_loads_markdown_guide_when_detected(monkeypatch, tmp_path: Path):
    guide = tmp_path / "troubleshooting-guide"
    guide.mkdir()
    (guide / "case.md").write_text(
        "# Layer Separation\n\n## Symptoms\n- layers split\n\n## Causes\n- low temp\n\n## Solutions\n- increase temp\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("TROUBLESHOOTING_GUIDE_DIR", str(guide))

    args = argparse.Namespace(
        kb_markdown_dir=None,
        no_guide_autodetect=False,
        kb_json="data/troubleshooting_seed.json",
    )

    kb = _load_knowledge_base(args)
    assert kb.entries
    assert kb.entries[0].category == "Layer Separation"
