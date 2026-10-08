from core.llm import make_llm


def test_make_llm_defaults_to_openrouter_deepseek(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    llm = make_llm()

    assert llm.openai_api_base == "https://openrouter.ai/api/v1"
    assert llm.model_name == "deepseek/deepseek-v4.1-flash"


def test_make_llm_reads_provider_from_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    llm = make_llm()

    assert llm.openai_api_base == "https://api.openai.com/v1"
    assert llm.model_name == "gpt-4o-mini"
    assert llm.openai_api_key is not None
    assert llm.openai_api_key.get_secret_value() == "dummy"


def test_make_llm_model_argument_overrides_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    assert make_llm("other/model").model_name == "other/model"
