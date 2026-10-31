"""HTTP client for the FastAPI support-agent backend."""

from collections.abc import Mapping

import httpx

from frontend.config import FrontendSettings
from frontend.models import ChatResult, OrderContext, SourceReference


class BackendClient:
    """Call backend health and chat endpoints without owning business logic.

    Attributes:
        settings (FrontendSettings): Backend connection settings.
    """

    def __init__(self, settings: FrontendSettings | None = None) -> None:
        self.settings = settings or FrontendSettings.from_environment()

    def health(self) -> bool:
        """Check whether the backend health endpoint returns HTTP 200.

        Returns:
            bool: Whether the backend is reachable and healthy.
        """
        try:
            response = httpx.get(f"{self.settings.backend_url}/health", timeout=3.0)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    def chat(self, message: str, context: OrderContext) -> ChatResult:
        """Send a customer message and optional order context to the API.

        Args:
            message (str): Customer message to submit.
            context (OrderContext): Optional order-verification fields.

        Returns:
            ChatResult: Parsed backend answer and source references.

        Raises:
            httpx.HTTPError: If the request fails or returns an error status.
            ValueError: If the response does not match the expected JSON shape.
        """
        payload: dict[str, object] = {"message": message}
        if context.order_id is not None:
            payload["order_id"] = context.order_id
        if context.customer_email:
            payload["customer_email"] = context.customer_email
        if context.customer_phone:
            payload["customer_phone"] = context.customer_phone
        with httpx.Client(base_url=self.settings.backend_url, timeout=30.0) as client:
            response = client.post("/chat", json=payload)
            response.raise_for_status()
            raw_result = response.json()
        return _parse_chat_result(raw_result)


def _parse_chat_result(raw_result: object) -> ChatResult:
    """Validate and convert a backend JSON response into a frontend model.

    Args:
        raw_result (object): Decoded backend JSON value.

    Returns:
        ChatResult: Typed response data.

    Raises:
        ValueError: If the payload is missing required fields or has invalid sources.
    """
    if not isinstance(raw_result, Mapping):
        raise ValueError("Backend response must be a JSON object")
    reply = raw_result.get("reply")
    mode = raw_result.get("mode")
    raw_sources = raw_result.get("sources", [])
    if not isinstance(reply, str) or not isinstance(mode, str):
        raise ValueError("Backend response has invalid reply fields")
    if not isinstance(raw_sources, list):
        raise ValueError("Backend response has invalid sources")
    sources = tuple(_parse_source(source) for source in raw_sources)
    return ChatResult(reply=reply, mode=mode, sources=sources)


def _parse_source(raw_source: object) -> SourceReference:
    """Validate one non-sensitive source reference from the API.

    Args:
        raw_source (object): Decoded source object.

    Returns:
        SourceReference: Typed source reference.

    Raises:
        ValueError: If source fields are missing or have invalid types.
    """
    if not isinstance(raw_source, Mapping):
        raise ValueError("Backend source must be an object")
    source_type = raw_source.get("source_type")
    reference = raw_source.get("reference")
    if not isinstance(source_type, str) or not isinstance(reference, str):
        raise ValueError("Backend source has invalid fields")
    return SourceReference(source_type=source_type, reference=reference)
