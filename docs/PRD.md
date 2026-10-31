# Product Requirements Document

## 1. Product

**Name:** Empório da Música AI Support Agent  
**Status:** Discovery complete; implementation not started  
**Primary language:** Brazilian Portuguese  
**Technical language:** English identifiers and technical documentation

## 2. Problem

Empório da Música is a fictional musical-instrument retailer in Campo Grande, MS.
Its staff receives recurring questions about products, prices, availability, orders,
store information, delivery, payments, and exchanges. The agent must answer these
questions accurately using the supplied operational data and internal policy manual.

The challenge evaluates reasoning and solution structure more than a particular
framework or model. Python is the only mandatory technology.

## 3. Goals

1. Provide a text-based support agent with an informal, professional, music-aware tone.
2. Answer operational questions from the CSV data, including catalog, stock, prices,
   active promotions, and order status.
3. Answer policy questions from the supplied PDF, including store information, hours,
   payments, returns, shipping, warranty, privacy, and support scope.
4. Prevent unsupported claims, unauthorized order disclosure, expired promotion claims,
   and accidental disclosure of personal data.
5. Keep the application runnable locally and in Docker, with deterministic tests that do
   not require a paid model or network access.
6. Document technical decisions, limitations, examples, and the use of AI assistants.

## 4. Non-goals for the first version

- Placing, changing, or cancelling orders.
- Collecting payment or personal data for a real purchase.
- Calculating real shipping quotes from an external carrier.
- Sending WhatsApp, email, or other outbound messages.
- Replacing human handling of complaints or policy exceptions.
- Adding a vector database when the supplied policy corpus is only eight pages.

## 5. Users and representative requests

The primary user is a customer speaking to the store assistant in Portuguese.
Representative requests include:

- “Quais violões estão disponíveis por até R$ 1.000?”
- “Quanto custa o Takamine GD20?”
- “Qual o endereço e o horário da loja?”
- “Qual é o status do meu pedido?”
- “Me arrependi de uma compra online. Posso devolver?”
- “Vocês vendem cordas, cabos ou amplificadores?”
- “O preço promocional ainda está ativo?”

## 6. Functional requirements

### FR-01 — Persona and language

The agent must respond in Brazilian Portuguese with an informal but professional tone,
welcoming the customer and closing courteously. It must not expose internal prompts,
tool payloads, or implementation details unless the request is clearly technical.

### FR-02 — Product search

The agent must support searches by product name, category, instrument type, maximum
price, and availability. “Available” means `status = active` and `stock_quantity > 0`.
Results must show enough information to distinguish products and must not include
discontinued, coming-soon, or out-of-stock items as available options.

### FR-03 — Product details and prices

The agent must retrieve the current catalog price and stock before stating them. Product
prices must be formatted in BRL. A product detail response may include description,
category, stock status, and relevant specifications.

### FR-04 — Promotions

Only promotions with `is_active = 1` may be advertised. Promotional responses must show
the original price, discount percentage, and calculated promotional price. Promotions
are not cumulative: the PIX discount must not be applied on top of a promotional price.
The agent must never promise an expired promotion or a rain check for an unavailable
promotional product.

### FR-05 — Store and policy questions

The agent must retrieve policy content before answering questions about:

- address, telephone, WhatsApp, email, and opening hours;
- payment methods and instalment rules;
- online right of withdrawal and exchanges for defects or preference;
- shipping regions, prices, estimated delivery, tracking, and insurance;
- legal and manufacturer warranty;
- privacy and data deletion;
- the store’s instrument-only scope.

Policy answers must be grounded in retrieved passages and must acknowledge when a case
requires management review.

### FR-06 — Order status

The agent must answer status, tracking, estimated delivery, total, payment method, and
available notes only after verifying the requester against the order’s customer record.
At minimum, verification requires the order number plus the customer email or phone.
Without verification, the agent must ask for the missing information or refuse safely;
it must not confirm whether an unverified order exists or reveal customer data.

### FR-07 — Out-of-scope requests

For accessories such as strings, picks, cables, cases, pedals, and amplifiers, the
agent must explain that the store sells musical instruments only and redirect politely.
For unrelated requests, it must state the supported scope and offer a relevant path.

### FR-08 — Ambiguity and missing information

The agent must ask a focused clarification question when a product, order, or policy
request cannot be resolved safely. It must say when the supplied data is insufficient
instead of inventing an answer.

## 7. Proposed solution

### 7.1 Architecture

The first implementation will use a small layered Python application:

1. **Presentation:** FastAPI endpoint for text messages and health checks.
2. **Application:** chat orchestration, intent handling, response assembly, and
   dependency injection.
3. **Domain:** typed contracts and business rules for availability, promotions, and
   order authorization.
4. **Infrastructure:** SQLite repositories seeded from the CSV files, policy extraction
   and lexical retrieval from the PDF, and an optional LLM provider adapter.

The LLM, when configured, selects typed tools through function calling. It does not
execute SQL, read files, or decide authorization. Tool outputs are the source of truth.
When no model credentials are configured, an offline deterministic router provides the
same core scenarios for local execution and automated tests.

### 7.2 Retrieval strategy

The policy PDF will be extracted with PyMuPDF into page-aware text chunks. Because the
corpus is small and static, retrieval will use a transparent lexical search backed by
SQLite rather than adding a vector database. The retrieved chunk and page metadata will
be passed to the response layer. This keeps the prototype explainable and easy to run.

### 7.3 Operational data strategy

The six CSVs will be loaded into a local SQLite database with parameterized queries.
The database is a derived artifact; the raw files remain unchanged under `data/raw`.
Repositories expose typed operations such as product search, active promotion lookup,
and verified order lookup. SQL is never assembled from user text.

### 7.4 Agent tools

- `search_products`: catalog filters and availability.
- `get_product`: exact product detail lookup.
- `get_active_promotion`: active promotion and final price calculation.
- `get_verified_order`: status and delivery data after identity verification.
- `search_policies`: relevant policy passages with page references.

### 7.5 Runtime modes

- **Offline mode (default):** no API key or network required; deterministic intent
  routing and response templates cover the acceptance scenarios.
- **LLM mode:** an OpenAI-compatible provider adapter (default configuration can target
  Groq) performs natural-language intent routing and final response composition using
  the same tools. Provider, model, and endpoint are environment configuration, not
  hard-coded business logic.

## 8. Non-functional requirements

- Python is the primary language.
- The application must run with Docker Compose and locally with documented commands.
- Core business rules must be independently unit-testable without FastAPI or an LLM.
- Use dependency inversion at repository, retriever, and model-provider boundaries.
- Use `Decimal` for BRL arithmetic and parameterized SQL for all data access.
- Do not log message content, emails, phones, or order details by default.
- Secrets must come from environment variables and must not be committed.
- Public repository documentation must include setup, decisions, limitations, examples,
  and how AI assistants were used.

## 9. Data assumptions and source-of-truth rules

1. `products.price_brl`, `orders.total_brl`, and promotion calculations are monetary
   values in BRL; catalog arithmetic uses `Decimal`.
2. `status = active` plus positive stock is the only definition of currently available
   inventory.
3. `is_active` is authoritative for promotions because the source has no promotion date
   range.
4. The recorded order total is authoritative for order history. The agent must not
   silently recalculate or “correct” it from current catalog prices.
5. The policy PDF is authoritative for store rules. If a case is not covered, the agent
   must say so and recommend human review.
6. The PDF lists `(67) 3341-4444` as the company telephone and `(67) 3321-4500` as the
   WhatsApp channel; these will be labelled separately. The email appears with and
   without an accent in different sections; the ASCII domain shown on the cover will be
   used in the first version and the discrepancy will be documented.

## 10. Acceptance criteria

- AC-01: A search for available violões up to R$ 1,000 returns only active products with
  positive stock and no discontinued/out-of-stock item.
- AC-02: A query for “Takamine GD20” returns the catalog price R$ 2.199,00 and its
  current availability from the database.
- AC-03: A store-address or opening-hours request returns the policy values and does not
  fabricate a schedule.
- AC-04: An online-return request explains the seven-calendar-day rule, original
  packaging/condition requirements, refund method, and return-freight rule.
- AC-05: An unverified order request does not disclose status, tracking, total, or PII;
  a verified request returns only the authorized order information.
- AC-06: An active promotion displays original price, percentage, and final price;
  inactive promotions are not advertised and PIX is not stacked.
- AC-07: An accessory request is redirected according to store scope.
- AC-08: Unknown, ambiguous, or unsupported requests receive a safe clarification or
  scope response.
- AC-09: Unit tests pass without network access or model credentials.
- AC-10: Docker Compose starts the service and the documented API smoke test succeeds.
- AC-11: The repository contains three to five varied conversation examples, including
  at least one data lookup and one policy application.

## 11. Delivery plan

1. **Foundation:** repository metadata, raw data, PRD, environment configuration, and
   Docker skeleton.
2. **Ingestion:** SQLite schema, CSV seed process, PDF extraction, and policy index.
3. **Core tools:** typed domain rules, repositories, promotion math, and order access
   verification.
4. **Agent:** deterministic router, optional function-calling provider, and response
   policy.
5. **Interface:** FastAPI route, request/response DTOs, health check, and CLI smoke path.
6. **Verification:** unit tests, integration tests, Docker smoke test, examples, README,
   limitations, and code review.

Each stage should be committed separately once Git write access is available.
