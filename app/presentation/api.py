"""FastAPI application factory and HTTP routes."""

from fastapi import FastAPI

from app.presentation.controller import ChatController
from app.presentation.dtos import ChatRequest, ChatResponse
from app.presentation.service import Agent, ChatService


def create_app(agent: Agent) -> FastAPI:
    """Create the HTTP application around an injected support agent.

    Args:
        agent (Agent): Application agent used by the chat service.

    Returns:
        FastAPI: Configured health and chat API.
    """
    application = FastAPI(
        title="Empório da Música AI Support Agent",
        version="0.1.0",
    )
    controller = ChatController(ChatService(agent))

    @application.get("/health")
    async def health() -> dict[str, str]:
        """Return a lightweight service health response."""
        return {"status": "ok"}

    @application.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        """Process one validated customer chat request."""
        return controller.respond(request)

    return application
