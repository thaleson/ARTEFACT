from fastapi import HTTPException

from app.presentation.dtos import ChatRequest, ChatResponse, SourceResponse
from app.presentation.service import ChatService


class ChatController:
    def __init__(self, service: ChatService) -> None:
        self.service = service

    def respond(self, request: ChatRequest) -> ChatResponse:
        try:
            response = self.service.respond(request)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail="The support service is temporarily unavailable",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing the message",
            ) from exc
        return ChatResponse(
            reply=response.reply,
            mode=response.mode,
            sources=[
                SourceResponse(
                    source_type=source.source_type,
                    reference=source.reference,
                )
                for source in response.sources
            ],
        )
