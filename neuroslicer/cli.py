from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .config import HFConfig
from .diagnostics import DiagnosticEngine
from .knowledge_base import KnowledgeBase
from .profile_manager import ProfileManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NeuroSlicer troubleshooting assistant")
    parser.add_argument("query", help="User defect description")
    parser.add_argument(
        "--kb-json",
        default="data/troubleshooting_seed.json",
        help="Path to JSON knowledge base",
    )
    parser.add_argument(
        "--kb-markdown-dir",
        help="Optional path to markdown troubleshooting repository",
    )
    parser.add_argument("--use-hf", action="store_true", help="Enable HF API request")
    parser.add_argument("--profile-in", help="Input slicer profile path (.json/.ini)")
    parser.add_argument("--profile-out", help="Where to save updated profile")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.kb_markdown_dir:
        kb = KnowledgeBase.from_markdown_dir(args.kb_markdown_dir)
    else:
        kb = KnowledgeBase.from_json(args.kb_json)

    profile = ProfileManager.load(args.profile_in) if args.profile_in else None

    engine = DiagnosticEngine(kb, hf_config=HFConfig.from_env())
    diagnosis = engine.diagnose(
        args.query,
        use_hf=args.use_hf,
        profile_parameters=profile.parameters if profile else None,
    )

    if profile and diagnosis.profile_changes and args.profile_out:
        profile.apply_changes(diagnosis.profile_changes)
        profile.save(args.profile_out)

    print(json.dumps(asdict(diagnosis), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
