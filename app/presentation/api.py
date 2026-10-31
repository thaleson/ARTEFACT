from fastapi import FastAPI

from app.presentation.controller import ChatController
from app.presentation.dtos import ChatRequest, ChatResponse
from app.presentation.service import Agent, ChatService


def create_app(agent: Agent) -> FastAPI:
    application = FastAPI(
        title="Empório da Música AI Support Agent",
        version="0.1.0",
    )
    controller = ChatController(ChatService(agent))

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        return controller.respond(request)

    return application
