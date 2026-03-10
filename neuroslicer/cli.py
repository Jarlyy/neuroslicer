from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .config import HFConfig
from .data_sources import detect_troubleshooting_guide
from .diagnostics import DiagnosticEngine
from .knowledge_base import KnowledgeBase
from .profile_manager import ProfileManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NeuroSlicer troubleshooting assistant")
    parser.add_argument("query", help="User defect description")
    parser.add_argument(
        "--kb-json",
        default="data/troubleshooting_seed.json",
        help="Path to JSON seed knowledge base",
    )
    parser.add_argument(
        "--kb-markdown-dir",
        help="Explicit path to markdown troubleshooting repository",
    )
    parser.add_argument(
        "--no-guide-autodetect",
        action="store_true",
        help="Disable auto-detection of local troubleshooting guide directory",
    )
    parser.add_argument("--use-hf", action="store_true", help="Enable HF API request")
    parser.add_argument("--profile-in", help="Input slicer profile path (.json/.ini)")
    parser.add_argument("--profile-out", help="Where to save updated profile")
    parser.add_argument("--dry-run", action="store_true", help="Do not save patched profile to disk")
    parser.add_argument(
        "--show-kb-source",
        action="store_true",
        help="Print which KB source was selected",
    )
    return parser


def _load_knowledge_base(args: argparse.Namespace) -> tuple[KnowledgeBase, str]:
    if args.kb_markdown_dir:
        return KnowledgeBase.from_markdown_dir(args.kb_markdown_dir), f"markdown:{args.kb_markdown_dir}"

    if not args.no_guide_autodetect:
        guide_dir = detect_troubleshooting_guide()
        if guide_dir is not None:
            return KnowledgeBase.from_markdown_dir(guide_dir), f"markdown:{guide_dir}"

    return KnowledgeBase.from_json(args.kb_json), f"json:{args.kb_json}"


def main() -> None:
    args = build_parser().parse_args()
    kb, kb_source = _load_knowledge_base(args)

    profile = ProfileManager.load(args.profile_in) if args.profile_in else None

    engine = DiagnosticEngine(kb, hf_config=HFConfig.from_env())
    diagnosis = engine.diagnose(
        args.query,
        use_hf=args.use_hf,
        profile_parameters=profile.parameters if profile else None,
    )

    if profile and diagnosis.profile_changes and args.profile_out and not args.dry_run:
        profile.apply_changes(diagnosis.profile_changes)
        profile.save(args.profile_out)

    payload = asdict(diagnosis)
    if args.show_kb_source:
        payload["kb_source"] = kb_source

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
