# Source Data Audit

This audit records the supplied challenge files without modifying their contents.

## Inventory

| File | Records | Purpose |
| --- | ---: | --- |
| `categories.csv` | 9 | Product categories |
| `customers.csv` | 50 | Customer identities used for order verification |
| `products.csv` | 65 | Catalog, prices, inventory, status, specifications |
| `orders.csv` | 20 | Order status, totals, payment, tracking, delivery |
| `order_items.csv` | 22 | Order-to-product quantities |
| `promotions.csv` | 25 | Product discounts and active flags |
| `store_policies.pdf` | 8 pages | Internal policy and service manual |

## Integrity checks

- All declared foreign-key references resolve.
- No duplicate category, customer, product, order, or promotion identifiers were found.
- Product IDs are not sequential: ID `145` appears between IDs `130` and `131`; this is
  valid and must not be normalized away.
- The operational data contains no promotion start/end date; `is_active` is the usable
  source of truth.

## Business-relevant anomalies

These are source-data observations, not fixes:

- Product `96` is marked `active` but has zero stock. It must not be presented as
  available.
- Product `113` is `discontinued` with zero stock.
- Product `136` is `discontinued` despite a positive stock value. Status takes precedence
  over stock for availability.
- Product `130` is `coming_soon` with positive stock and appears in order items. It must
  not be presented as currently available in the catalog; historical order data remains
  readable after authorization.
- The catalog sum differs from the recorded total for orders `3` and `20`. Recorded
  order totals remain authoritative, and the agent must not expose an unexplained
  recalculation as a correction.
- The policy cover lists the company telephone as `(67) 3341-4444`, while the WhatsApp
  section lists `(67) 3321-4500`. They will be labelled as different channels.
- The policy email appears as `contato@emporiodamusica.com.br` on the cover and with an
  accented domain in a later section. The first version will use the ASCII cover value
  and document the discrepancy.

## Availability query baseline

For the acceptance case “available violões up to R$ 1,000”, the filter is:

```text
category_id = 5
status = active
stock_quantity > 0
price_brl <= 1000
```

The result contains 12 products. Product `96` is excluded because stock is zero, and
product `113` is excluded because it is discontinued.
