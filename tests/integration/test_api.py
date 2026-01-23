"""End-to-end API tests using httpx TestClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Health endpoint should return healthy status."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "woo-hoo"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """Readiness endpoint should check OpenRouter connectivity."""
        # Mock the connectivity check to avoid real API calls
        with patch(
            "woo_hoo.api.routers.health.OpenRouterClient.check_connectivity",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = await async_client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "openrouter_connected" in data


class TestCategoriesEndpoint:
    """Tests for the categories endpoint."""

    @pytest.mark.asyncio
    async def test_list_categories(self, async_client: AsyncClient):
        """Should return all 17 Woo categories."""
        response = await async_client.get("/api/v1/metadata/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 17

    @pytest.mark.asyncio
    async def test_category_structure(self, async_client: AsyncClient):
        """Each category should have required fields."""
        response = await async_client.get("/api/v1/metadata/categories")

        data = response.json()
        for cat in data["categories"]:
            assert "code" in cat
            assert "label" in cat
            assert "artikel" in cat
            assert "tooi_uri" in cat

    @pytest.mark.asyncio
    async def test_adviezen_category_present(self, async_client: AsyncClient):
        """ADVIEZEN category should be in the list."""
        response = await async_client.get("/api/v1/metadata/categories")

        data = response.json()
        codes = [cat["code"] for cat in data["categories"]]
        assert "ADVIEZEN" in codes


class TestValidateEndpoint:
    """Tests for the metadata validation endpoint."""

    @pytest.mark.asyncio
    async def test_validate_valid_metadata(
        self,
        async_client: AsyncClient,
        minimal_valid_metadata: dict,
    ):
        """Valid metadata should pass validation."""
        response = await async_client.post(
            "/api/v1/metadata/validate",
            json={"metadata": minimal_valid_metadata},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_invalid_metadata(self, async_client: AsyncClient):
        """Invalid metadata should fail validation."""
        invalid_metadata = {
            "publisher": {"label": "Test"},  # Missing required 'resource'
        }

        response = await async_client.post(
            "/api/v1/metadata/validate",
            json={"metadata": invalid_metadata},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


class TestGenerateEndpoint:
    """Tests for the metadata generation endpoint."""

    @pytest.mark.asyncio
    async def test_generate_requires_document(self, async_client: AsyncClient):
        """Generate endpoint should require document content."""
        response = await async_client.post(
            "/api/v1/metadata/generate",
            json={},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_generate_rejects_short_text(self, async_client: AsyncClient):
        """Should reject documents with very short text."""
        response = await async_client.post(
            "/api/v1/metadata/generate",
            json={"document": {"text": "short"}},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_with_mock_llm(
        self,
        async_client: AsyncClient,
        sample_document_text: str,
        sample_publisher_hint: dict,
    ):
        """Test generation with mocked LLM response."""
        import json

        from woo_hoo.services.openrouter import ChatCompletionChoice, ChatCompletionResponse, ChatMessage

        mock_llm_response = {
            "officiele_titel": "Advies inzake wijziging bestemmingsplan Centrum",
            "verkorte_titels": ["Advies bestemmingsplan"],
            "omschrijvingen": ["Advies over wijziging bestemmingsplan"],
            "informatiecategorieen": [
                {
                    "categorie": "ADVIEZEN",
                    "confidence": 0.95,
                    "reasoning": "Document bevat advies aan college",
                }
            ],
            "documentsoorten": ["ADVIES"],
            "trefwoorden": ["bestemmingsplan", "horeca", "centrum"],
            "taal": "NL",
            "creatiedatum": "2024-01-15",
            "confidence_scores": {
                "titel": 0.92,
                "informatiecategorie": 0.95,
                "overall": 0.90,
            },
        }

        # Create a properly typed mock response
        mock_response = ChatCompletionResponse(
            id="test-id",
            model="mistralai/mistral-large-2411",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=json.dumps(mock_llm_response)),
                    finish_reason="stop",
                )
            ],
        )

        # Mock the OpenRouter client
        with patch("woo_hoo.services.metadata_generator.MetadataGenerator._get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.chat_completion = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            response = await async_client.post(
                "/api/v1/metadata/generate",
                json={
                    "document": {"text": sample_document_text},
                    "publisher_hint": sample_publisher_hint,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "suggestion" in data
        assert (
            data["suggestion"]["metadata"]["titelcollectie"]["officieleTitel"]
            == "Advies inzake wijziging bestemmingsplan Centrum"
        )


class TestOpenAPISchema:
    """Tests for OpenAPI schema availability."""

    @pytest.mark.asyncio
    async def test_openapi_schema_available(self, async_client: AsyncClient):
        """OpenAPI schema should be accessible."""
        response = await async_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "woo-hoo"
        assert "paths" in data

    @pytest.mark.asyncio
    async def test_swagger_docs_available(self, async_client: AsyncClient):
        """Swagger UI should be accessible."""
        response = await async_client.get("/docs")

        assert response.status_code == 200
        assert (
            "swagger" in response.text.lower()
            or "redoc" in response.text.lower()
            or "html" in response.headers.get("content-type", "")
        )
