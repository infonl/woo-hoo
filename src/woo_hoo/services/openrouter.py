"""OpenRouter API client for LLM access.

Uses the official OpenRouter Python SDK to provide access to EU-based LLM models
(primarily Mistral), enabling data sovereignty compliance for Dutch government use cases.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
from openrouter import OpenRouter
from pydantic import BaseModel

from woo_hoo.config import Settings, get_settings
from woo_hoo.utils.logging import get_logger
from woo_hoo.utils.retry import RetryConfig, with_retry

if TYPE_CHECKING:
    from openrouter.types.chat_completion_response import ChatCompletionResponse as SDKResponse  # pyrefly: ignore

logger = get_logger(__name__)


@dataclass(frozen=True)
class OpenRouterModels:
    """Available OpenRouter models.

    EU-based models are preferred for Dutch government data sovereignty.
    """

    # EU-based models (preferred)
    MISTRAL_LARGE = "mistralai/mistral-large-2411"
    MISTRAL_SMALL = "mistralai/mistral-small-2501"
    MISTRAL_NEMO = "mistralai/mistral-nemo"

    # Fallback options (non-EU)
    CLAUDE_SONNET = "anthropic/claude-sonnet-4"
    GPT_4O = "openai/gpt-4o"


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""

    index: int
    message: ChatMessage
    finish_reason: str | None = None


class ChatCompletionUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenRouter chat completion response."""

    id: str
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage | None = None


class OpenRouterClient:
    """Async client for OpenRouter API using the official SDK.

    Uses the OpenRouter Python SDK with async support for chat completions.
    Includes built-in retry logic for rate limits and transient errors.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the client.

        Args:
            settings: Application settings (uses get_settings() if not provided)
        """
        self.settings = settings or get_settings()
        self._client: OpenRouter | None = None
        self._retry_config = RetryConfig(
            max_attempts=self.settings.llm_max_retries,
            base_delay=1.0,
            max_delay=30.0,
        )

    def _get_client(self) -> OpenRouter:
        """Get or create the OpenRouter SDK client."""
        if self._client is None:
            self._client = OpenRouter(
                api_key=self.settings.llm_api_key,
                timeout_ms=int(self.settings.llm_timeout_seconds * 1000),
            )
        return self._client

    def _convert_response(self, sdk_response: SDKResponse) -> ChatCompletionResponse:
        """Convert SDK response to our internal response model."""
        choices = []
        for choice in sdk_response.choices or []:
            # SDK uses ROLE as class constant, not role as instance attribute
            msg = choice.message
            if msg:
                role = getattr(msg, "ROLE", None) or getattr(msg, "role", "assistant")
                content = msg.content or ""
            else:
                role = "assistant"
                content = ""
            message = ChatMessage(role=role, content=content)
            choices.append(
                ChatCompletionChoice(
                    index=choice.index,
                    message=message,
                    finish_reason=choice.finish_reason,
                )
            )

        usage = None
        if sdk_response.usage:
            usage = ChatCompletionUsage(
                prompt_tokens=sdk_response.usage.prompt_tokens,
                completion_tokens=sdk_response.usage.completion_tokens,
                total_tokens=sdk_response.usage.total_tokens,
            )

        return ChatCompletionResponse(
            id=sdk_response.id,
            model=sdk_response.model,
            choices=choices,
            usage=usage,
        )

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
        # Per-request overrides
        api_key: str | None = None,
        custom_base_url: str | None = None,
    ) -> ChatCompletionResponse:
        """Send a chat completion request.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to settings.default_model)
            temperature: Sampling temperature (defaults to settings.llm_temperature)
            max_tokens: Maximum tokens in response
            response_format: Response format (e.g., {"type": "json_object"})
            api_key: Optional API key override for this request
            custom_base_url: Optional custom base URL override for this request

        Returns:
            Chat completion response

        Raises:
            Exception: On non-retryable errors
            RetryExhaustedError: When all retry attempts fail
        """
        # Determine which provider to use
        use_custom = custom_base_url is not None or (self.settings.llm_provider == "custom" and custom_base_url is None)

        if use_custom:
            return await self._custom_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                api_key=api_key,
                custom_base_url=custom_base_url,
            )

        if self.settings.llm_provider == "anthropic":
            return await self._anthropic_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
            )

        # Default: OpenRouter
        return await self._openrouter_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            api_key=api_key,
        )

    async def _openrouter_chat_completion(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
        api_key: str | None = None,
    ) -> ChatCompletionResponse:
        """Handle OpenRouter chat completion with optional per-request API key."""
        model = model or self.settings.default_model
        temperature = temperature if temperature is not None else self.settings.llm_temperature

        # Format messages for the SDK
        sdk_messages = [{"role": m.role, "content": m.content} for m in messages]

        async def _make_request() -> ChatCompletionResponse:
            start_time = time.perf_counter()

            # Use per-request API key if provided, otherwise use default client
            if api_key:
                client = OpenRouter(
                    api_key=api_key,
                    timeout_ms=int(self.settings.llm_timeout_seconds * 1000),
                )
            else:
                client = self._get_client()

            # Use the async method from the SDK
            sdk_response = await client.chat.send_async(
                model=model,
                messages=sdk_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                "OpenRouter request completed",
                model=model,
                elapsed_ms=elapsed_ms,
            )

            return self._convert_response(sdk_response)

        return await with_retry(_make_request, self._retry_config)

    async def _custom_chat_completion(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
        api_key: str | None = None,
        custom_base_url: str | None = None,
    ) -> ChatCompletionResponse:
        """Handle custom LLM provider chat completion."""
        model = model or self.settings.default_model
        temperature = temperature if temperature is not None else self.settings.llm_temperature

        # Resolve effective values
        base_url = custom_base_url or self.settings.custom_llm_base_url
        effective_api_key = api_key or self.settings.llm_api_key

        if not base_url:
            raise ValueError("Custom base URL is required for custom LLM provider")

        # Build headers - if API key is set, use standard Bearer auth
        headers = {"Content-Type": "application/json"}
        if effective_api_key:
            headers["Authorization"] = f"Bearer {effective_api_key}"

        # Build payload (OpenAI-compatible format)
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        async def _make_request() -> ChatCompletionResponse:
            start_time = time.perf_counter()

            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                logger.info(
                    "Custom LLM request completed",
                    model=model,
                    base_url=base_url,
                    elapsed_ms=elapsed_ms,
                )

                # Convert OpenAI-compatible response to our format
                return self._convert_openai_response(data)

        return await with_retry(_make_request, self._retry_config)

    async def _anthropic_chat_completion(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> ChatCompletionResponse:
        """Handle Anthropic Messages API chat completion."""
        model = model or self.settings.default_model
        temperature = temperature if temperature is not None else self.settings.llm_temperature
        effective_api_key = api_key or self.settings.llm_api_key
        base_url = self.settings.anthropic_base_url.rstrip("/")

        if not effective_api_key:
            raise ValueError("API key is required for Anthropic provider (set LLM_API_KEY)")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": effective_api_key,
            "anthropic-version": "2023-06-01",
        }

        # Anthropic uses a top-level 'system' field instead of a system message
        system_text = None
        user_messages = []
        for m in messages:
            if m.role == "system":
                system_text = m.content
            else:
                user_messages.append({"role": m.role, "content": m.content})

        payload: dict[str, Any] = {
            "model": model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_text:
            payload["system"] = system_text

        async def _make_request() -> ChatCompletionResponse:
            start_time = time.perf_counter()

            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{base_url}/v1/messages",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                logger.info(
                    "Anthropic request completed",
                    model=model,
                    elapsed_ms=elapsed_ms,
                )

                return self._convert_anthropic_response(data)

        return await with_retry(_make_request, self._retry_config)

    def _convert_anthropic_response(self, data: dict[str, Any]) -> ChatCompletionResponse:
        """Convert Anthropic Messages API response to our ChatCompletionResponse format.

        Anthropic response format:
            {"id": "msg_...", "content": [{"type": "text", "text": "..."}],
             "usage": {"input_tokens": N, "output_tokens": N}}
        """
        # Extract text from content blocks
        content_blocks = data.get("content", [])
        text_parts = [block["text"] for block in content_blocks if block.get("type") == "text"]
        content = "\n".join(text_parts)

        choices = [
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=content),
                finish_reason=data.get("stop_reason"),
            )
        ]

        usage = None
        usage_data = data.get("usage")
        if usage_data:
            input_tokens = usage_data.get("input_tokens", 0)
            output_tokens = usage_data.get("output_tokens", 0)
            usage = ChatCompletionUsage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )

        return ChatCompletionResponse(
            id=data.get("id", ""),
            model=data.get("model", ""),
            choices=choices,
            usage=usage,
        )

    def _convert_openai_response(self, data: dict[str, Any]) -> ChatCompletionResponse:
        """Convert OpenAI-compatible response to our ChatCompletionResponse format."""
        choices = []
        for choice in data.get("choices", []):
            message_data = choice.get("message", {})
            message = ChatMessage(
                role=message_data.get("role", "assistant"),
                content=message_data.get("content", ""),
            )
            choices.append(
                ChatCompletionChoice(
                    index=choice.get("index", 0),
                    message=message,
                    finish_reason=choice.get("finish_reason"),
                )
            )

        usage_data = data.get("usage")
        usage = None
        if usage_data:
            usage = ChatCompletionUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

        return ChatCompletionResponse(
            id=data.get("id", ""),
            model=data.get("model", ""),
            choices=choices,
            usage=usage,
        )

    async def check_connectivity(self) -> bool:
        """Check if OpenRouter API is reachable.

        Returns:
            True if API is reachable, False otherwise
        """
        try:
            client = self._get_client()
            # Make a minimal request to check connectivity
            await client.chat.send_async(
                model="mistralai/mistral-nemo",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.warning("OpenRouter connectivity check failed", error=str(e))
            return False

    async def close(self) -> None:
        """Close the SDK client."""
        if self._client is not None:
            # The SDK uses context manager internally, but we can reset our reference
            self._client = None

    async def __aenter__(self) -> OpenRouterClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
