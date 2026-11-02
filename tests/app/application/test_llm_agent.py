import json
from unittest.mock import Mock

from app.application.contracts import AgentResponse, ChatInput, SourceReference
from app.application.llm_agent import LlmSupportAgent
from app.application.model_provider import ModelToolCall, ModelTurn


class ModelWithToolThenAnswer:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, messages: object, tools: object) -> ModelTurn:
        self.calls += 1
        if self.calls == 1:
            return ModelTurn(
                content="",
                tool_calls=[
                    ModelToolCall(
                        call_id="call-1",
                        name="search_policies",
                        arguments=json.dumps({"query": "horario funcionamento"}),
                    )
                ],
            )
        return ModelTurn(content="A loja funciona de segunda a sexta.", tool_calls=[])


def make_fallback() -> Mock:
    fallback = Mock()
    fallback.respond.return_value = AgentResponse("fallback", "offline")
    return fallback


def test_llm_agent_executes_tool_and_returns_model_answer() -> None:
    tool_executor = Mock()
    tool_executor.execute.return_value = (
        '{"chunks": [{"page": 2, "content": "09:00 às 18:00"}]}',
        [SourceReference("policy", "page:2")],
    )
    model = ModelWithToolThenAnswer()
    fallback = make_fallback()
    agent = LlmSupportAgent(model, tool_executor, fallback)

    response = agent.respond(ChatInput("Qual o horário?"))

    assert response.reply == "A loja funciona de segunda a sexta."
    assert response.mode == "llm"
    assert model.calls == 2
    tool_executor.execute.assert_called_once()


def test_llm_agent_falls_back_on_provider_error() -> None:
    model = Mock()
    model.complete.side_effect = RuntimeError("provider down")
    fallback = make_fallback()
    agent = LlmSupportAgent(model, Mock(), fallback)

    response = agent.respond(ChatInput("Qual o horário?"))

    assert response.reply == "fallback"
    fallback.respond.assert_called_once()


def test_llm_agent_rejects_unverified_factual_answer() -> None:
    model = Mock()
    model.complete.return_value = ModelTurn(
        content="O Taylor custa R$ 1,00.",
        tool_calls=[],
    )
    fallback = make_fallback()
    agent = LlmSupportAgent(model, Mock(), fallback)

    response = agent.respond(ChatInput("Quanto custa o Taylor 110e?"))

    assert response.reply == "fallback"
    fallback.respond.assert_called_once()


def test_llm_agent_falls_back_for_unrecognized_factual_request() -> None:
    model = Mock()
    model.complete.return_value = ModelTurn(
        content="A capital da França é Paris.",
        tool_calls=[],
    )
    fallback = make_fallback()
    agent = LlmSupportAgent(model, Mock(), fallback)

    response = agent.respond(ChatInput("Qual é a capital da França?"))

    assert response.reply == "fallback"
    fallback.respond.assert_called_once()


def test_llm_agent_rejects_invalid_tool_result() -> None:
    model = Mock()
    model.complete.side_effect = [
        ModelTurn(
            content="",
            tool_calls=[
                ModelToolCall(
                    call_id="invalid-1",
                    name="missing_tool",
                    arguments="{}",
                )
            ],
        ),
        ModelTurn(content="O Takamine custa R$ 1,00.", tool_calls=[]),
    ]
    tool_executor = Mock()
    tool_executor.execute.return_value = ('{"error": "Unknown tool"}', [])
    fallback = make_fallback()
    agent = LlmSupportAgent(model, tool_executor, fallback)

    response = agent.respond(ChatInput("Quanto custa o Takamine GD20?"))

    assert response.reply == "fallback"
    fallback.respond.assert_called_once()
