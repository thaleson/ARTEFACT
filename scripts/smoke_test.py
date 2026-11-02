"""Run acceptance checks against the real challenge data and policy PDF."""

from app.application.contracts import ChatInput
from app.config import Settings
from app.container import build_container


def main() -> None:
    """Build the application and verify representative customer scenarios."""
    settings = Settings.from_environment()
    container = build_container(settings)
    try:
        responses = {
            "catalog": container.agent.respond(
                ChatInput("Quais violões estão disponíveis por até R$ 1.000?")
            ),
            "product": container.agent.respond(
                ChatInput("Quanto custa o Takamine GD20?")
            ),
            "order": container.agent.respond(
                ChatInput(
                    "Qual o status do pedido 8, meu e-mail é "
                    "anacarol.ferreira@coldmail.com"
                )
            ),
            "return": container.agent.respond(
                ChatInput("Me arrependi da compra online, posso devolver?")
            ),
        }
        assert "Encontrei 12" in responses["catalog"].reply
        assert "R$ 2.199,00" in responses["product"].reply
        assert "está enviado" in responses["order"].reply
        assert "dias corridos" in responses["return"].reply
    finally:
        container.close()
    print("Smoke test passed")


if __name__ == "__main__":
    main()
