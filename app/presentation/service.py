from typing import Protocol

from app.application.contracts import AgentResponse, ChatInput
from app.presentation.dtos import ChatRequest


class Agent(Protocol):
    def respond(self, chat_input: ChatInput) -> AgentResponse:
        ...


class ChatService:
    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def respond(self, request: ChatRequest) -> AgentResponse:
        return self.agent.respond(
            ChatInput(
                message=request.message,
                order_id=request.order_id,
                customer_email=request.customer_email,
                customer_phone=request.customer_phone,
            )
        )
