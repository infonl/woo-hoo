"""Core metadata generation service.

Orchestrates LLM-based DIWOO metadata extraction from document content.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import date, datetime

from pydantic import HttpUrl, ValidationError

from woo_hoo.config import Settings, get_settings
from woo_hoo.models.diwoo import (
    ClassificatieCollectie,
    DiWooMetadata,
    DocumentHandeling,
    DocumentSoortMeta,
    InformatieCategorieMeta,
    Organisatie,
    SoortHandelingMeta,
    TaalMeta,
    TitelCollectie,
)
from woo_hoo.models.enums import DocumentSoort, InformatieCategorie, SoortHandeling, Taal
from woo_hoo.models.requests import MetadataGenerationRequest, PublisherHint
from woo_hoo.models.responses import (
    ConfidenceScores,
    FieldConfidence,
    MetadataGenerationResponse,
    MetadataSuggestion,
)
from woo_hoo.services.openrouter import ChatMessage, OpenRouterClient
from woo_hoo.services.prompt_templates import build_extraction_prompt, get_system_prompt
from woo_hoo.utils.logging import get_logger

logger = get_logger(__name__)


class MetadataGenerationError(Exception):
    """Raised when metadata generation fails."""

    pass


class MetadataGenerator:
    """Service for generating DIWOO-compliant metadata using LLMs."""

    def __init__(
        self,
        client: OpenRouterClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the generator.

        Args:
            client: OpenRouter client (creates one if not provided)
            settings: Application settings (uses get_settings() if not provided)
        """
        self.settings = settings or get_settings()
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> OpenRouterClient:
        """Get or create the OpenRouter client."""
        if self._client is None:
            self._client = OpenRouterClient(self.settings)
        return self._client

    async def generate(
        self,
        request: MetadataGenerationRequest,
    ) -> MetadataGenerationResponse:
        """Generate DIWOO metadata for a document.

        Args:
            request: Metadata generation request with document content

        Returns:
            Response with generated metadata or error
        """
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        logger.info(
            "Starting metadata generation",
            request_id=request_id,
            text_length=len(request.document.text),
            has_publisher_hint=request.publisher_hint is not None,
        )

        try:
            client = await self._get_client()

            # Build prompt
            publisher_name = request.publisher_hint.name if request.publisher_hint else None
            prompt = build_extraction_prompt(
                document_text=request.document.text,
                publisher_hint=publisher_name,
                max_text_length=self.settings.max_text_length,
            )

            messages = [
                ChatMessage(role="system", content=get_system_prompt()),
                ChatMessage(role="user", content=prompt),
            ]

            # Call LLM
            model = request.preferred_model or self.settings.default_model
            response = await client.chat_completion(
                messages=messages,
                model=model,
                temperature=self.settings.llm_temperature,
                response_format={"type": "json_object"},
            )

            # Parse LLM response
            raw_content = response.choices[0].message.content
            llm_output = json.loads(raw_content)

            # Transform to DIWOO structure
            metadata = self._transform_to_diwoo(llm_output, request.publisher_hint)

            # Build confidence scores
            confidence = (
                self._extract_confidence(llm_output)
                if request.include_confidence
                else ConfidenceScores(overall=0.7, fields=[])
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            suggestion = MetadataSuggestion(
                metadata=metadata,
                confidence=confidence,
                model_used=model,
                processing_time_ms=elapsed_ms,
            )

            logger.info(
                "Metadata generation completed",
                request_id=request_id,
                elapsed_ms=elapsed_ms,
                overall_confidence=confidence.overall,
            )

            return MetadataGenerationResponse(
                success=True,
                request_id=request_id,
                suggestion=suggestion,
            )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response", request_id=request_id, error=str(e))
            return MetadataGenerationResponse(
                success=False,
                request_id=request_id,
                error=f"LLM returned invalid JSON: {e}",
            )

        except ValidationError as e:
            logger.error("Metadata validation failed", request_id=request_id, error=str(e))
            return MetadataGenerationResponse(
                success=False,
                request_id=request_id,
                error=f"Generated metadata validation failed: {e}",
            )

        except Exception as e:
            logger.exception("Metadata generation failed", request_id=request_id)
            return MetadataGenerationResponse(
                success=False,
                request_id=request_id,
                error=str(e),
            )

    def _transform_to_diwoo(
        self,
        llm_output: dict,
        publisher_hint: PublisherHint | None,
    ) -> DiWooMetadata:
        """Transform LLM output to DIWOO metadata structure.

        Args:
            llm_output: Parsed JSON from LLM
            publisher_hint: Optional publisher information

        Returns:
            DiWooMetadata instance
        """
        # Build publisher
        if publisher_hint:
            publisher = Organisatie(
                resource=publisher_hint.tooi_uri
                or HttpUrl("https://identifier.overheid.nl/tooi/id/organisatie/placeholder"),
                label=publisher_hint.name,
            )
        else:
            publisher = Organisatie(
                resource=HttpUrl("https://identifier.overheid.nl/tooi/id/organisatie/placeholder"),
                label="Onbekende organisatie",
            )

        # Build titel collectie
        titelcollectie = TitelCollectie(
            officiele_titel=llm_output.get("officiele_titel", "Onbekende titel")[:2000],
            verkorte_titels=llm_output.get("verkorte_titels"),
        )

        # Build informatiecategorieen
        informatiecategorieen: list[InformatieCategorieMeta] = []
        for cat_data in llm_output.get("informatiecategorieen", []):
            cat_name = cat_data.get("categorie", "").upper().replace(" ", "_")
            try:
                cat_enum = InformatieCategorie[cat_name]
                informatiecategorieen.append(InformatieCategorieMeta(categorie=cat_enum))
            except KeyError:
                logger.warning("Unknown informatiecategorie from LLM", categorie=cat_name)

        # Ensure at least one category
        if not informatiecategorieen:
            informatiecategorieen = [InformatieCategorieMeta(categorie=InformatieCategorie.OVERIGE_BESLUITEN_AS)]

        # Build documentsoorten
        documentsoorten: list[DocumentSoortMeta] | None = None
        raw_soorten = llm_output.get("documentsoorten")
        if raw_soorten:
            documentsoorten = []
            for soort_name in raw_soorten:
                try:
                    soort_enum = DocumentSoort[soort_name.upper().replace(" ", "_")]
                    documentsoorten.append(DocumentSoortMeta(soort=soort_enum))
                except KeyError:
                    logger.warning("Unknown documentsoort from LLM", soort=soort_name)

        # Build classificatie collectie
        classificatiecollectie = ClassificatieCollectie(
            informatiecategorieen=informatiecategorieen,
            documentsoorten=documentsoorten if documentsoorten else None,
            trefwoorden=llm_output.get("trefwoorden"),
        )

        # Build document handeling
        documenthandelingen = [
            DocumentHandeling(
                soort_handeling=SoortHandelingMeta(handeling=SoortHandeling.REGISTRATIE),
                at_time=datetime.now(),
                was_associated_with=publisher,
            )
        ]

        # Parse creatiedatum
        creatiedatum: date | None = None
        raw_date = llm_output.get("creatiedatum")
        if raw_date:
            try:
                creatiedatum = date.fromisoformat(raw_date)
            except ValueError:
                logger.warning("Could not parse creatiedatum", value=raw_date)

        # Build language
        taal_str = llm_output.get("taal", "NL").upper()
        try:
            taal_enum = Taal[taal_str]
        except KeyError:
            taal_enum = Taal.NL
        language = TaalMeta(taal=taal_enum)

        return DiWooMetadata(
            publisher=publisher,
            titelcollectie=titelcollectie,
            classificatiecollectie=classificatiecollectie,
            documenthandelingen=documenthandelingen,
            omschrijvingen=llm_output.get("omschrijvingen"),
            creatiedatum=creatiedatum,
            language=language,
        )

    def _extract_confidence(self, llm_output: dict) -> ConfidenceScores:
        """Extract confidence scores from LLM output.

        Args:
            llm_output: Parsed JSON from LLM

        Returns:
            ConfidenceScores instance
        """
        raw_scores = llm_output.get("confidence_scores", {})
        overall = raw_scores.get("overall", 0.7)

        fields: list[FieldConfidence] = []
        for field_name, score in raw_scores.items():
            if field_name != "overall" and isinstance(score, (int, float)):
                fields.append(FieldConfidence(field_name=field_name, confidence=float(score)))

        # Add reasoning from informatiecategorieen
        for cat_data in llm_output.get("informatiecategorieen", []):
            if "reasoning" in cat_data:
                fields.append(
                    FieldConfidence(
                        field_name=f"informatiecategorie_{cat_data.get('categorie', 'unknown')}",
                        confidence=cat_data.get("confidence", 0.7),
                        reasoning=cat_data.get("reasoning"),
                    )
                )

        return ConfidenceScores(overall=overall, fields=fields)

    async def close(self) -> None:
        """Close the OpenRouter client if we own it."""
        if self._owns_client and self._client:
            await self._client.close()
