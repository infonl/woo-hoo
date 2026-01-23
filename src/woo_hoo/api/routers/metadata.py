"""Metadata generation and validation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from woo_hoo.config import get_settings
from woo_hoo.models.diwoo import DiWooMetadata
from woo_hoo.models.enums import InformatieCategorie
from woo_hoo.models.requests import (
    DocumentContent,
    MetadataGenerationRequest,
    MetadataValidationRequest,
    PublisherHint,
)
from woo_hoo.models.responses import (
    CategoriesResponse,
    CategoryInfo,
    MetadataGenerationResponse,
    MetadataValidationResponse,
)
from woo_hoo.services.document_extractor import DocumentExtractionError, extract_text_from_bytes
from woo_hoo.services.metadata_generator import MetadataGenerator
from woo_hoo.utils.logging import get_logger


def _check_api_key() -> None:
    """Raise HTTPException if OpenRouter API key is not configured."""
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable.",
        )


router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])
logger = get_logger(__name__)


@router.post(
    "/generate",
    response_model=MetadataGenerationResponse,
    summary="Generate DIWOO-compliant metadata",
    description="Analyze document text and generate metadata suggestions compliant with DIWOO XSD schema.",
)
async def generate_metadata(
    request: MetadataGenerationRequest,
) -> MetadataGenerationResponse:
    """Generate DIWOO metadata from document text.

    Args:
        request: Document content and optional publisher hint

    Returns:
        Generated metadata with confidence scores
    """
    _check_api_key()
    generator = MetadataGenerator()
    try:
        return await generator.generate(request)
    finally:
        await generator.close()


@router.post(
    "/generate-from-file",
    response_model=MetadataGenerationResponse,
    summary="Generate metadata from uploaded file",
    description="Upload a PDF or text file and generate DIWOO-compliant metadata.",
)
async def generate_metadata_from_file(
    file: UploadFile = File(..., description="PDF or text file to analyze"),
    publisher_name: str | None = Form(None, description="Publisher organization name"),
    publisher_uri: str | None = Form(None, description="Publisher TOOI URI"),
) -> MetadataGenerationResponse:
    """Generate DIWOO metadata from an uploaded file.

    Supports PDF and text files.

    Args:
        file: Uploaded file
        publisher_name: Optional publisher organization name
        publisher_uri: Optional publisher TOOI URI

    Returns:
        Generated metadata with confidence scores
    """
    _check_api_key()
    # Extract text from file
    try:
        content = await file.read()
        text = extract_text_from_bytes(content, file.filename)
    except DocumentExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from file: {e}",
        ) from e

    # Build request
    publisher_hint = None
    if publisher_name:
        publisher_hint = PublisherHint(
            name=publisher_name,
            tooi_uri=publisher_uri if publisher_uri else None,
        )

    request = MetadataGenerationRequest(
        document=DocumentContent(text=text, filename=file.filename),
        publisher_hint=publisher_hint,
    )

    generator = MetadataGenerator()
    try:
        return await generator.generate(request)
    finally:
        await generator.close()


@router.post(
    "/validate",
    response_model=MetadataValidationResponse,
    summary="Validate metadata against DIWOO schema",
    description="Validate provided metadata against DIWOO XSD schema requirements.",
)
async def validate_metadata(
    request: MetadataValidationRequest,
) -> MetadataValidationResponse:
    """Validate metadata against DIWOO schema.

    Args:
        request: Metadata to validate

    Returns:
        Validation result with any errors
    """
    try:
        validated = DiWooMetadata.model_validate(request.metadata)
        return MetadataValidationResponse(
            valid=True,
            metadata=validated,
        )
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return MetadataValidationResponse(
            valid=False,
            errors=errors,
        )


@router.get(
    "/categories",
    response_model=CategoriesResponse,
    summary="List all Woo information categories",
    description="Get all 17 Woo information categories with their codes, labels, and TOOI URIs.",
)
async def list_categories() -> CategoriesResponse:
    """List all 17 Woo information categories.

    Returns:
        List of categories with their details
    """
    categories = [
        CategoryInfo(
            code=cat.name,
            label=cat.label,
            artikel=cat.artikel,
            tooi_uri=cat.tooi_uri,
        )
        for cat in InformatieCategorie
    ]
    return CategoriesResponse(categories=categories)
