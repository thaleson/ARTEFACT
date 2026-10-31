# Empório da Música AI Support Agent

Python text-support agent for the Artefact AI Engineer technical challenge. The agent
answers in Brazilian Portuguese and uses the supplied catalog, order data, promotions,
and store policy manual as its sources of truth.

## Quick start with Docker

```bash
docker compose up --build
```

The API is then available at `http://localhost:8000`.

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Quanto custa o Takamine GD20?"}'
```

The default `AGENT_MODE=offline` requires no model key or network at runtime. It uses a
deterministic router and the same controlled tools used by the LLM mode, which makes the
acceptance scenarios reproducible.

## Local setup

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m scripts.seed_database
uvicorn app.main:app --reload
```

Run the test suite with:

```bash
pytest --cov=app --cov-report=term-missing
```

After installing the project dependencies, run the real-data smoke test with:

```bash
python -m scripts.smoke_test
```

## LLM mode

The optional provider adapter uses the OpenAI-compatible chat-completions interface.
The default endpoint is configured for Groq, but the endpoint and model are configurable.

```bash
export AGENT_MODE=llm
export LLM_API_KEY='your-key'
export LLM_BASE_URL='https://api.groq.com/openai/v1'
export LLM_MODEL='your-provider-model'
docker compose up --build
```

The model only selects typed tools. It does not execute SQL, read files, authorize
orders, or supply catalog facts from memory. If the provider is unavailable, the
application falls back to the deterministic agent.

## API contract

`POST /chat` accepts:

```json
{
  "message": "Qual o status do meu pedido?",
  "order_id": 8,
  "customer_email": "anacarol.ferreira@coldmail.com"
}
```

`order_id` plus the customer email or phone is required for order details. Requests
without identity verification receive a safe clarification and do not reveal whether an
order exists. In a text-only client, the agent can also extract an explicitly written
email or Brazilian phone number from the same message.

## Architecture

The project follows a small layered design:

- `app/domain`: typed models, ports, and business rules such as availability and
  non-cumulative promotions;
- `app/application`: intent routing, offline/LLM orchestration, tool contracts, and
  response formatting;
- `app/infrastructure`: SQLite database, CSV seeding, PDF extraction, and repositories;
- `app/presentation`: FastAPI DTOs, service, controller, and routes;
- `data/raw`: unchanged challenge source files.

Operational CSVs are loaded into SQLite with parameterized queries. The eight-page PDF is
extracted into page-aware chunks and searched with transparent lexical retrieval. A vector
database was intentionally omitted because the supplied policy corpus is small and static.

## Decisions and safeguards

- An item is available only when `status = active` and `stock_quantity > 0`.
- Only `is_active = 1` promotions are advertised.
- Promotional answers show original price, discount percentage, and calculated price;
  PIX is never stacked on a promotion.
- Recorded order totals are treated as historical truth even when they differ from a
  current catalog sum.
- Customer PII is used only for order verification and is not included in normal replies
  or logs.
- Accessories are outside the store scope and are redirected politely.

The full requirements and source-data findings are documented in:

- [Product Requirements Document](docs/PRD.md)
- [Source Data Audit](docs/DATA_AUDIT.md)

## Limitations

- The first version is stateless; durable conversation history is not implemented.
- The offline router covers the documented support scenarios but is intentionally less
  flexible than an LLM for open-ended language.
- Shipping prices are not calculated because no carrier integration or destination quote
  data was supplied.
- The agent does not place, change, or cancel orders and does not send WhatsApp messages.
- The source manual is version 2.1 from June 2025; policy updates require re-seeding the
  derived policy index.
- The supplied dataset contains documented status and total inconsistencies; the agent
  preserves source values instead of silently correcting them.

## Conversation examples

The required examples are in [`examples/`](examples/):

- [Catalog search](examples/01_catalog_search.md)
- [Product price and promotion](examples/02_product_promotion.md)
- [Order privacy and status](examples/03_order_privacy.md)
- [Online return policy](examples/04_return_policy.md)

## Use of AI assistants

Codex (GPT-based coding assistant) was used during development to inspect the supplied
PDF and CSV files, turn the challenge into a PRD, implement focused modules, generate
tests, and review edge cases. Human decisions remained explicit: the source hierarchy,
order verification rule, offline fallback, policy-channel discrepancy handling, and
acceptance criteria were reviewed against the challenge material. No credentials or
customer data outside the supplied synthetic dataset were provided to the assistant.
