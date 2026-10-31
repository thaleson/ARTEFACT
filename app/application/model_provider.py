from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence


@dataclass(frozen=True)
class ModelToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ModelTurn:
    content: str
    tool_calls: list[ModelToolCall]


class ChatModel(Protocol):
    def complete(
        self,
        messages: Sequence[Mapping[str, object]],
        tools: Sequence[Mapping[str, object]],
    ) -> ModelTurn:
        ...


class OpenAICompatibleChatModel:
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
