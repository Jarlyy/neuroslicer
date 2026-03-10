from neuroslicer.config import HFConfig
from neuroslicer.diagnostics import DiagnosticEngine
from neuroslicer.knowledge_base import KnowledgeBase


def test_diagnose_with_seed_data():
    kb = KnowledgeBase.from_json("data/troubleshooting_seed.json")
    engine = DiagnosticEngine(kb)
    result = engine.diagnose("first layer not sticking", use_hf=False)
    assert result.defect_type in {"Poor Bed Adhesion", "Layer Separation", "Stringing"}
    assert result.recommendations
    assert isinstance(result.profile_changes, list)


def test_diagnose_builds_profile_changes_when_profile_given():
    kb = KnowledgeBase.from_json("data/troubleshooting_seed.json")
    engine = DiagnosticEngine(kb)
    result = engine.diagnose(
        "layers split and weak part",
        use_hf=False,
        profile_parameters={"nozzle_temperature": "200", "print_speed": "60", "fan_speed_first_layer": "50"},
    )
    assert result.defect_type == "Layer Separation"
    assert any(change.parameter == "nozzle_temperature" for change in result.profile_changes)


def test_diagnose_uses_llm_json_when_available(monkeypatch):
    kb = KnowledgeBase.from_json("data/troubleshooting_seed.json")
    engine = DiagnosticEngine(kb, hf_config=HFConfig(token="hf_dummy"))

    fake_payload = [{"generated_text": '{"defect_type":"Stringing","causes":["temp high"],"recommendations":["reduce temp"],"confidence":0.91,"parameter_changes":[{"parameter":"nozzle_temperature","new_value":"195","reason":"reduce oozing"}]}' }]

    from neuroslicer import diagnostics as d

    monkeypatch.setattr(d.HFClient, "analyze", lambda self, prompt: fake_payload)

    result = engine.diagnose("many hairs between parts", use_hf=True)
    assert result.defect_type == "Stringing"
    assert result.confidence > 0.8
    assert result.profile_changes
    assert result.profile_changes[0].parameter == "nozzle_temperature"
