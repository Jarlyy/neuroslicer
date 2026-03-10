from neuroslicer.diagnostics import DiagnosticEngine
from neuroslicer.knowledge_base import KnowledgeBase


def test_diagnose_with_seed_data():
    kb = KnowledgeBase.from_json("data/troubleshooting_seed.json")
    engine = DiagnosticEngine(kb)
    result = engine.diagnose("first layer not sticking")
    assert result.defect_type in {"Poor Bed Adhesion", "Layer Separation", "Stringing"}
    assert result.recommendations
    assert isinstance(result.profile_changes, list)


def test_diagnose_builds_profile_changes_when_profile_given():
    kb = KnowledgeBase.from_json("data/troubleshooting_seed.json")
    engine = DiagnosticEngine(kb)
    result = engine.diagnose(
        "layers split and weak part",
        profile_parameters={"nozzle_temperature": "200", "print_speed": "60", "fan_speed_first_layer": "50"},
    )
    assert result.defect_type == "Layer Separation"
    assert any(change.parameter == "nozzle_temperature" for change in result.profile_changes)
