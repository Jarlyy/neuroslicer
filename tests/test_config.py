from neuroslicer.config import HFConfig


def test_default_router_endpoint():
    cfg = HFConfig(token="x", model_id="openai/gpt-oss-120b")
    assert cfg.endpoint() == "https://router.huggingface.co/hf-inference/models/openai/gpt-oss-120b"


def test_endpoint_override():
    cfg = HFConfig(token="x", model_id="openai/gpt-oss-120b", endpoint_override="https://custom.endpoint")
    assert cfg.endpoint() == "https://custom.endpoint"
