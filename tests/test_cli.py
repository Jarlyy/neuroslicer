from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_cli_dry_run_does_not_create_output_profile(tmp_path: Path):
    in_profile = tmp_path / "in.json"
    out_profile = tmp_path / "out.json"
    in_profile.write_text(
        json.dumps({"nozzle_temperature": "200", "print_speed": "60", "fan_speed_first_layer": "70"}),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "neuroslicer.cli",
        "layers split",
        "--profile-in",
        str(in_profile),
        "--profile-out",
        str(out_profile),
        "--dry-run",
        "--show-kb-source",
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    payload = json.loads(proc.stdout)

    assert "kb_source" in payload
    assert payload["profile_changes"]
    assert not out_profile.exists()
