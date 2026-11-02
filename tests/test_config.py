from pathlib import Path

from app.config import Settings


def test_settings_resolve_relative_paths_and_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", "fixtures")
    monkeypatch.setenv("DATABASE_PATH", "runtime.db")
    monkeypatch.setenv("AGENT_MODE", "LLM")
    monkeypatch.setenv("LLM_API_KEY", "secret")

    settings = Settings.from_environment(tmp_path)

    assert settings.data_dir == tmp_path / "fixtures"
    assert settings.database_path == tmp_path / "runtime.db"
    assert settings.agent_mode == "llm"
    assert settings.llm_api_key == "secret"


def test_settings_use_current_groq_model_by_default(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)

    settings = Settings.from_environment(tmp_path)

    assert settings.llm_model == "openai/gpt-oss-120b"
