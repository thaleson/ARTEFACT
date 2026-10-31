# Example 3 — Order privacy and status

**Customer:** Qual o status do pedido 8?

**Assistant:** Por segurança, confirme o e-mail ou telefone cadastrado junto com o
número do pedido para eu consultar o status.

**Customer:** O e-mail é anacarol.ferreira@coldmail.com.

*(In the API, this turn carries `order_id: 8`; the text agent also extracts the explicit
email.)*

**Assistant:** O pedido #8 está enviado. O total registrado é R$ 349,90. O código de
rastreamento é BRJL5544332BR e a previsão registrada é 2026-02-28.
