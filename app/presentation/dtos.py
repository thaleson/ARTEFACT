"""Pydantic request and response models for the chat API."""

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Validate a customer message and optional order context."""

    message: str = Field(min_length=1)
    order_id: int | None = Field(default=None, gt=0)
    customer_email: str | None = None
    customer_phone: str | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        """Reject blank messages after trimming surrounding whitespace.

        Args:
            value (str): Raw message field.

        Returns:
            str: Trimmed non-empty message.

        Raises:
            ValueError: If the message contains only whitespace.
        """
        normalized = value.strip()
        if not normalized:
            raise ValueError("message cannot be blank")
        return normalized


class SourceResponse(BaseModel):
    """Expose a non-sensitive source reference used by the answer."""

    source_type: str
    reference: str


class ChatResponse(BaseModel):
    """Expose the customer reply, runtime mode, and source references."""

    reply: str
    mode: str
    sources: list[SourceResponse]
