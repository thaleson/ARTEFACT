"""Environment-backed configuration for the Streamlit client."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FrontendSettings:
    """Store the backend URL used by the demonstration client."""

    backend_url: str

    @classmethod
    def from_environment(cls) -> "FrontendSettings":
        """Build frontend settings from the backend URL environment variable.

        Returns:
            FrontendSettings: Resolved Streamlit client settings.
        """
        return cls(
            backend_url=os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
        )
