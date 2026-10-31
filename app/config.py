import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    database_path: Path
    agent_mode: str
    llm_api_key: str | None
    llm_base_url: str
    llm_model: str

    @classmethod
    def from_environment(cls, project_root: Path | None = None) -> "Settings":
        root = project_root or Path(__file__).resolve().parents[1]
        data_dir = _resolve_path(root, os.getenv("DATA_DIR", "data/raw"))
        database_path = _resolve_path(root, os.getenv("DATABASE_PATH", "data/app.db"))
        return cls(
            project_root=root,
            data_dir=data_dir,
            database_path=database_path,
            agent_mode=os.getenv("AGENT_MODE", "offline").lower(),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_base_url=os.getenv(
                "LLM_BASE_URL", "https://api.groq.com/openai/v1"
            ),
            llm_model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        )


def _resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path
