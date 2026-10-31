"""Provider abstractions for optional OpenAI-compatible chat models."""

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence


@dataclass(frozen=True)
class ModelToolCall:
    """Represent one function call returned by a chat model."""

    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ModelTurn:
    """Represent model content and any requested tool calls."""

    content: str
    tool_calls: list[ModelToolCall]


class ChatModel(Protocol):
    """Define the completion interface consumed by the LLM agent."""

    def complete(
        self,
        messages: Sequence[Mapping[str, object]],
        tools: Sequence[Mapping[str, object]],
    ) -> ModelTurn:
        """Generate one model turn from conversation messages and tools.

        Args:
            messages (Sequence[Mapping[str, object]]): Conversation messages.
            tools (Sequence[Mapping[str, object]]): Available function definitions.

        Returns:
            ModelTurn: Text content and requested function calls.
        """
        ...


class OpenAICompatibleChatModel:
    """Adapt an OpenAI-compatible chat-completions client to the model protocol.

    Attributes:
        client (object): OpenAI-compatible SDK client.
        model (str): Provider model identifier.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "The openai package is required when LLM mode is enabled"
            ) from exc
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def complete(
        self,
        messages: Sequence[Mapping[str, object]],
        tools: Sequence[Mapping[str, object]],
    ) -> ModelTurn:
        """Request one deterministic-temperature completion from the provider.

        Args:
            messages (Sequence[Mapping[str, object]]): Conversation messages.
            tools (Sequence[Mapping[str, object]]): Available function definitions.

        Returns:
            ModelTurn: Provider text and normalized tool calls.

        Raises:
            RuntimeError: If the configured provider request fails.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=list(messages),
                tools=list(tools),
                tool_choice="auto",
                temperature=0,
            )
        except Exception as exc:
            raise RuntimeError("The configured LLM provider is unavailable") from exc
        message = response.choices[0].message
        tool_calls = [
            ModelToolCall(
                call_id=str(tool_call.id),
                name=str(tool_call.function.name),
                arguments=str(tool_call.function.arguments),
            )
            for tool_call in (message.tool_calls or [])
        ]
        return ModelTurn(content=message.content or "", tool_calls=tool_calls)
