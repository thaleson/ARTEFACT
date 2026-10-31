from app.config import Settings
from app.container import build_container
from app.presentation.api import create_app


settings = Settings.from_environment()
container = build_container(settings)
app = create_app(container.agent)
