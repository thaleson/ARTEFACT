"""HTTP controller responsible for service orchestration and error mapping."""

from fastapi import HTTPException

from app.presentation.dtos import ChatRequest, ChatResponse, SourceResponse
from app.presentation.service import ChatService


class ChatController:
    """Translate validated chat requests into HTTP response DTOs.

    Attributes:
        service (ChatService): Service responsible for agent invocation.
    """

    def __init__(self, service: ChatService) -> None:
        self.service = service

    def respond(self, request: ChatRequest) -> ChatResponse:
        """Handle one chat request and map application errors to HTTP errors.

        Args:
            request (ChatRequest): Validated request body.

        Returns:
            ChatResponse: Serialized agent response with source references.

        Raises:
            HTTPException: For validation, infrastructure, or unexpected failures.
        """
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
