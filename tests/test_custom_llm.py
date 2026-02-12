"""Tests for custom LLM provider functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from woo_hoo.config import Settings
from woo_hoo.models.requests import DocumentContent, MetadataGenerationRequest
from woo_hoo.services.openrouter import ChatMessage, OpenRouterClient

SAMPLE_OPENAI_RESPONSE = {
    "id": "test-id",
    "model": "mistral:latest",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "test response"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}

SAMPLE_ANTHROPIC_RESPONSE = {
    "id": "msg_test123",
    "type": "message",
    "role": "assistant",
    "model": "claude-sonnet-4-20250514",
    "content": [{"type": "text", "text": "test anthropic response"}],
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 12, "output_tokens": 8},
}


class TestCustomLLM:
    """Test custom LLM provider functionality."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings with custom LLM configuration."""
        return Settings(
            llm_provider="custom",
            custom_llm_base_url="http://localhost:11434/v1",
            llm_api_key="test-key",
        )

    @pytest.fixture
    def client(self, settings: Settings) -> OpenRouterClient:
        """Create OpenRouterClient with test settings."""
        return OpenRouterClient(settings)

    @pytest.fixture
    def sample_request(self) -> MetadataGenerationRequest:
        """Create a sample metadata generation request."""
        return MetadataGenerationRequest(
            document=DocumentContent(text="Test document content with enough characters to validate"),
            model="mistral:latest",
            api_key="per-request-key",
            custom_base_url="http://custom-llm:8000/v1",
        )

    def test_custom_llm_configuration(self, settings: Settings) -> None:
        """Test that custom LLM settings are properly configured."""
        assert settings.llm_provider == "custom"
        assert settings.custom_llm_base_url == "http://localhost:11434/v1"
        assert settings.llm_api_key == "test-key"

    def test_request_with_per_request_auth(self, sample_request: MetadataGenerationRequest) -> None:
        """Test that request accepts per-request auth fields."""
        assert sample_request.api_key == "per-request-key"
        assert sample_request.custom_base_url == "http://custom-llm:8000/v1"

    @pytest.mark.asyncio
    async def test_custom_chat_completion_headers(self, client: OpenRouterClient) -> None:
        """Test that custom chat completion builds correct headers with bearer auth."""
        messages = [ChatMessage(role="user", content="test")]

        with patch("httpx.AsyncClient") as mock_client_class:
            # httpx Response.json() and raise_for_status() are synchronous
            mock_response = MagicMock()
            mock_response.json.return_value = SAMPLE_OPENAI_RESPONSE
            mock_response.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http

            await client.chat_completion(
                messages=messages,
                model="mistral:latest",
                api_key="test-key",
                custom_base_url="http://localhost:8000/v1",
            )

            # Verify post was called
            mock_http.post.assert_called_once()
            call_args = mock_http.post.call_args
            headers = call_args[1]["headers"]

            assert headers["Content-Type"] == "application/json"
            assert headers["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_custom_chat_completion_no_auth(self) -> None:
        """Test custom chat completion with no authentication (no API key)."""
        no_auth_settings = Settings(
            llm_provider="custom",
            custom_llm_base_url="http://localhost:11434/v1",
            llm_api_key="",
        )
        no_auth_client = OpenRouterClient(no_auth_settings)
        messages = [ChatMessage(role="user", content="test")]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = SAMPLE_OPENAI_RESPONSE
            mock_response.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http

            await no_auth_client.chat_completion(
                messages=messages,
                model="mistral:latest",
                custom_base_url="http://localhost:8000/v1",
            )

            call_args = mock_http.post.call_args
            headers = call_args[1]["headers"]

            assert headers["Content-Type"] == "application/json"
            assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_use_custom_detection(self, client: OpenRouterClient) -> None:
        """Test that custom endpoint detection works correctly."""
        messages = [ChatMessage(role="user", content="test")]

        # Should use custom when custom_base_url is provided
        with patch.object(client, "_custom_chat_completion") as mock_custom:
            await client.chat_completion(
                messages=messages,
                custom_base_url="http://custom:8000/v1",
            )
            mock_custom.assert_called_once()

        # Should use custom when provider is set to custom (settings)
        with patch.object(client, "_custom_chat_completion") as mock_custom:
            await client.chat_completion(messages=messages)
            mock_custom.assert_called_once()

        # Should use OpenRouter when provider is openrouter and no custom URL
        client.settings.llm_provider = "openrouter"
        with patch.object(client, "_openrouter_chat_completion") as mock_openrouter:
            await client.chat_completion(messages=messages)
            mock_openrouter.assert_called_once()

    @pytest.mark.asyncio
    async def test_custom_chat_completion_payload(self, client: OpenRouterClient) -> None:
        """Test that the OpenAI-compatible payload is correctly built."""
        messages = [
            ChatMessage(role="system", content="You are a helper"),
            ChatMessage(role="user", content="Hello"),
        ]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = SAMPLE_OPENAI_RESPONSE
            mock_response.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http

            await client.chat_completion(
                messages=messages,
                model="mistral:latest",
                temperature=0.5,
                max_tokens=2048,
                custom_base_url="http://localhost:8000/v1",
            )

            call_args = mock_http.post.call_args
            # Verify URL
            assert call_args[0][0] == "http://localhost:8000/v1/chat/completions"
            # Verify payload
            payload = call_args[1]["json"]
            assert payload["model"] == "mistral:latest"
            assert payload["temperature"] == 0.5
            assert payload["max_tokens"] == 2048
            assert len(payload["messages"]) == 2
            assert payload["messages"][0]["role"] == "system"
            assert payload["messages"][1]["role"] == "user"

    def test_convert_openai_response(self, client: OpenRouterClient) -> None:
        """Test OpenAI-compatible response conversion."""
        result = client._convert_openai_response(SAMPLE_OPENAI_RESPONSE)

        assert result.id == "test-id"
        assert result.model == "mistral:latest"
        assert len(result.choices) == 1
        assert result.choices[0].message.role == "assistant"
        assert result.choices[0].message.content == "test response"
        assert result.usage is not None
        assert result.usage.total_tokens == 15


class TestAnthropicProvider:
    """Test Anthropic Messages API provider."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings for Anthropic provider."""
        return Settings(
            llm_provider="anthropic",
            llm_api_key="sk-ant-test-key",
            default_model="claude-sonnet-4-20250514",
        )

    @pytest.fixture
    def client(self, settings: Settings) -> OpenRouterClient:
        """Create OpenRouterClient configured for Anthropic."""
        return OpenRouterClient(settings)

    @pytest.mark.asyncio
    async def test_anthropic_routing(self, client: OpenRouterClient) -> None:
        """Test that anthropic provider routes to _anthropic_chat_completion."""
        messages = [ChatMessage(role="user", content="test")]

        with patch.object(client, "_anthropic_chat_completion") as mock_anthropic:
            await client.chat_completion(messages=messages)
            mock_anthropic.assert_called_once()

    @pytest.mark.asyncio
    async def test_anthropic_system_message_extraction(self, client: OpenRouterClient) -> None:
        """Test that system messages are extracted to top-level field."""
        messages = [
            ChatMessage(role="system", content="You are a metadata extractor"),
            ChatMessage(role="user", content="Analyze this document"),
        ]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = SAMPLE_ANTHROPIC_RESPONSE
            mock_response.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http

            await client.chat_completion(messages=messages)

            call_args = mock_http.post.call_args
            payload = call_args[1]["json"]

            # System should be top-level, not in messages
            assert payload["system"] == "You are a metadata extractor"
            assert len(payload["messages"]) == 1
            assert payload["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_anthropic_headers(self, client: OpenRouterClient) -> None:
        """Test that Anthropic-specific headers are sent."""
        messages = [ChatMessage(role="user", content="test")]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = SAMPLE_ANTHROPIC_RESPONSE
            mock_response.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http

            await client.chat_completion(messages=messages)

            call_args = mock_http.post.call_args
            headers = call_args[1]["headers"]

            assert headers["x-api-key"] == "sk-ant-test-key"
            assert headers["anthropic-version"] == "2023-06-01"
            assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_anthropic_endpoint_url(self, client: OpenRouterClient) -> None:
        """Test that the correct Anthropic endpoint is called."""
        messages = [ChatMessage(role="user", content="test")]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = SAMPLE_ANTHROPIC_RESPONSE
            mock_response.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_http

            await client.chat_completion(messages=messages)

            call_args = mock_http.post.call_args
            assert call_args[0][0] == "https://api.anthropic.com/v1/messages"

    def test_convert_anthropic_response(self, client: OpenRouterClient) -> None:
        """Test Anthropic response conversion to internal format."""
        result = client._convert_anthropic_response(SAMPLE_ANTHROPIC_RESPONSE)

        assert result.id == "msg_test123"
        assert result.model == "claude-sonnet-4-20250514"
        assert len(result.choices) == 1
        assert result.choices[0].message.role == "assistant"
        assert result.choices[0].message.content == "test anthropic response"
        assert result.choices[0].finish_reason == "end_turn"
        assert result.usage is not None
        assert result.usage.prompt_tokens == 12
        assert result.usage.completion_tokens == 8
        assert result.usage.total_tokens == 20

    def test_convert_anthropic_response_multiple_blocks(self, client: OpenRouterClient) -> None:
        """Test conversion when Anthropic returns multiple content blocks."""
        data = {
            "id": "msg_multi",
            "model": "claude-sonnet-4-20250514",
            "content": [
                {"type": "text", "text": "First part."},
                {"type": "text", "text": "Second part."},
            ],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 10},
        }
        result = client._convert_anthropic_response(data)

        assert result.choices[0].message.content == "First part.\nSecond part."

    @pytest.mark.asyncio
    async def test_anthropic_requires_api_key(self) -> None:
        """Test that missing API key raises an error."""
        settings = Settings(
            llm_provider="anthropic",
            llm_api_key="",
        )
        client = OpenRouterClient(settings)
        messages = [ChatMessage(role="user", content="test")]

        with pytest.raises(ValueError, match="API key is required for Anthropic provider"):
            await client.chat_completion(messages=messages)
