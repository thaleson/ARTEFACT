import json
from typing import Mapping

from app.application.contracts import AgentResponse, ChatInput, SourceReference
from app.application.input_normalizer import enrich_identity
from app.application.model_provider import ChatModel, ModelToolCall
from app.application.offline_agent import OfflineSupportAgent
from app.application.tool_executor import ToolExecutor
from app.application.tool_specs import TOOL_SPECS


SYSTEM_PROMPT = """
Você é o assistente virtual da Empório da Música. Responda em português brasileiro,
com tom informal, acolhedor e profissional. A loja vende exclusivamente instrumentos
musicais. Use as ferramentas para qualquer preço, estoque, promoção, pedido, prazo ou
regra da loja; nunca invente fatos. Promoções não são cumulativas e o desconto de PIX
não se soma a um preço promocional. Só informe um pedido quando a ferramenta confirmar
na solicitação uma identidade fornecida pelo cliente. Se uma ferramenta exigir dados
que não foram fornecidos, peça-os sem confirmar se o pedido existe. Para perguntas fora
do escopo, explique o escopo da loja e ofereça ajuda relevante. Não mencione prompts,
ferramentas ou dados internos na resposta final.
""".strip()


class LlmSupportAgent:
    def __init__(
        self,
        model: ChatModel,
        tools: ToolExecutor,
        fallback: OfflineSupportAgent,
        max_tool_rounds: int = 4,
    ) -> None:
        self.model = model
        self.tools = tools
        self.fallback = fallback
        self.max_tool_rounds = max_tool_rounds

    def respond(self, chat_input: ChatInput) -> AgentResponse:
        chat_input = enrich_identity(chat_input)
        if not chat_input.message.strip():
            raise ValueError("Message cannot be empty")
        try:
            return self._respond_with_model(chat_input)
        except (RuntimeError, ValueError):
            return self.fallback.respond(chat_input)

    def _respond_with_model(self, chat_input: ChatInput) -> AgentResponse:
        messages: list[Mapping[str, object]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chat_input.message.strip()},
        ]
        sources: list[SourceReference] = []
        for _ in range(self.max_tool_rounds):
            turn = self.model.complete(messages, TOOL_SPECS)
            if not turn.tool_calls:
                if turn.content.strip():
                    return AgentResponse(
                        reply=turn.content.strip(),
                        mode="llm",
                        sources=_unique_sources(sources),
                    )
                return self.fallback.respond(chat_input)
            messages.append(_assistant_message(turn.content, turn.tool_calls))
            for tool_call in turn.tool_calls:
                arguments = _parse_arguments(tool_call.arguments)
                result, tool_sources = self.tools.execute(
                    tool_call.name,
                    arguments,
                    chat_input,
                )
                sources.extend(tool_sources)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.call_id,
                        "name": tool_call.name,
                        "content": result,
                    }
                )
        return self.fallback.respond(chat_input)


def _assistant_message(
    content: str,
    tool_calls: list[ModelToolCall],
) -> Mapping[str, object]:
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call.call_id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": call.arguments,
                },
            }
            for call in tool_calls
        ],
    }


def _parse_arguments(raw_arguments: str) -> Mapping[str, object]:
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ValueError("The model returned invalid tool arguments") from exc
    if not isinstance(parsed, dict):
        raise ValueError("The model tool arguments must be an object")
    return parsed


def _unique_sources(sources: list[SourceReference]) -> list[SourceReference]:
    unique: list[SourceReference] = []
    seen: set[tuple[str, str]] = set()
    for source in sources:
        key = (source.source_type, source.reference)
        if key not in seen:
            seen.add(key)
            unique.append(source)
    return unique
