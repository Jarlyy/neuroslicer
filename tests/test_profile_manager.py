import json
from pathlib import Path

from neuroslicer.profile_manager import ProfileAdvisor, ProfileManager


def test_profile_json_load_apply_and_save(tmp_path: Path):
    profile_path = tmp_path / "profile.json"
    out_path = tmp_path / "profile_out.json"
    profile_path.write_text(
        json.dumps({"nozzle_temperature": "200", "print_speed": "60", "fan_speed_first_layer": "40"}),
        encoding="utf-8",
    )

    manager = ProfileManager.load(profile_path)
    changes = ProfileAdvisor().suggest_changes("Layer Separation", manager.parameters)
    applied = manager.apply_changes(changes)
    manager.save(out_path)

    saved = json.loads(out_path.read_text(encoding="utf-8"))
    assert applied
    assert saved["nozzle_temperature"] == "210"
    assert saved["fan_speed_first_layer"] == "0"
