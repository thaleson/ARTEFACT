from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    order_id: int | None = Field(default=None, gt=0)
    customer_email: str | None = None
    customer_phone: str | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message cannot be blank")
        return normalized


class SourceResponse(BaseModel):
    source_type: str
    reference: str


class ChatResponse(BaseModel):
    reply: str
    mode: str
    sources: list[SourceResponse]
