"""JSON schemas exposed to the optional function-calling model."""

from typing import Mapping


TOOL_SPECS: list[Mapping[str, object]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the current catalog and inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "category_id": {"type": "integer"},
                    "max_price": {"type": "number"},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Get one product from the current catalog by ID.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_promotion",
            "description": "Get the active promotion for a product, if one exists.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_verified_order",
            "description": "Get an order only after matching the requester's supplied identity.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "integer"}},
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": "Search the store policy manual for grounded answers.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]
