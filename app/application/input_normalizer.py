"""Extract explicit customer identity values from text messages."""

import re
from dataclasses import replace

from app.application.contracts import ChatInput


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\(\d{2}\)\s*\d{4,5}[-\s]\d{4}")


def enrich_identity(chat_input: ChatInput) -> ChatInput:
    """Fill missing identity fields from explicit content in the message.

    Existing structured fields take precedence over values extracted from text.

    Args:
        chat_input (ChatInput): Original message and optional identity context.

    Returns:
        ChatInput: Original input or a copy enriched with explicit identity values.
    """
    email = chat_input.customer_email or _extract_email(chat_input.message)
    phone = chat_input.customer_phone or _extract_phone(chat_input.message)
    if email == chat_input.customer_email and phone == chat_input.customer_phone:
        return chat_input
    return replace(chat_input, customer_email=email, customer_phone=phone)


def _extract_email(message: str) -> str | None:
    """Extract the first email address explicitly present in a message.

    Args:
        message (str): Customer message to inspect.

    Returns:
        str | None: Matched email address, if present.
    """
    match = EMAIL_PATTERN.search(message)
    return match.group(0) if match else None


def _extract_phone(message: str) -> str | None:
    """Extract the first Brazilian formatted phone number from a message.

    Args:
        message (str): Customer message to inspect.

    Returns:
        str | None: Matched phone number, if present.
    """
    match = PHONE_PATTERN.search(message)
    return match.group(0) if match else None
