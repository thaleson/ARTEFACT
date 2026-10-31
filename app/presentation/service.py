"""Application service boundary for chat requests."""

from typing import Protocol

from app.application.contracts import AgentResponse, ChatInput
from app.presentation.dtos import ChatRequest


class Agent(Protocol):
    """Define the response interface required by the HTTP service."""

    def respond(self, chat_input: ChatInput) -> AgentResponse:
        """Generate an application response for one chat input.

        Args:
            chat_input (ChatInput): Customer message and optional context.

        Returns:
            AgentResponse: Application-level answer.
        """
        ...


class ChatService:
    """Convert HTTP DTOs into application chat contracts.

    Attributes:
        agent (Agent): Injected support agent.
    """

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def respond(self, request: ChatRequest) -> AgentResponse:
        """Invoke the injected agent for a validated request.

        Args:
            request (ChatRequest): Validated HTTP request.

        Returns:
            AgentResponse: Application-level agent response.
        """
        return self.agent.respond(
            ChatInput(
                message=request.message,
                order_id=request.order_id,
                customer_email=request.customer_email,
                customer_phone=request.customer_phone,
            )
        )
