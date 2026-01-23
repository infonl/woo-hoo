#!/usr/bin/env python3
"""Test metadata generation with real documents and OpenRouter API.

Prerequisites:
1. Set OPENROUTER_API_KEY in your .env file
2. Run: uv run python scripts/download_samples.py

Usage:
    uv run python scripts/test_generation.py
    uv run python scripts/test_generation.py --file data/samples/cybersecuritybeeld_nederland_2024.pdf
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from woo_hoo.config import get_settings
from woo_hoo.models.requests import DocumentContent, MetadataGenerationRequest, PublisherHint
from woo_hoo.services.document_extractor import extract_text_from_file
from woo_hoo.services.metadata_generator import MetadataGenerator

SAMPLES_DIR = Path(__file__).parent.parent / "data" / "samples"


async def test_single_file(filepath: Path, publisher: str | None = None) -> None:
    """Test metadata generation for a single file."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {filepath.name}")
    print("=" * 60)

    # Check API key
    settings = get_settings()
    if not settings.openrouter_api_key:
        print("ERROR: OPENROUTER_API_KEY not set in environment or .env file")
        print("       Copy .env.example to .env and add your API key")
        return

    # Extract text
    print("\n1. Extracting text from document...")
    try:
        text = extract_text_from_file(filepath)
        print(f"   Extracted {len(text)} characters")
        print(f"   First 200 chars: {text[:200]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # Build request
    print("\n2. Building metadata generation request...")
    publisher_hint = PublisherHint(name=publisher) if publisher else None
    request = MetadataGenerationRequest(
        document=DocumentContent(text=text, filename=filepath.name),
        publisher_hint=publisher_hint,
        include_confidence=True,
    )

    # Generate metadata
    print(f"\n3. Generating metadata with {settings.default_model}...")
    generator = MetadataGenerator()
    try:
        response = await generator.generate(request)
    finally:
        await generator.close()

    # Show results
    print("\n4. Results:")
    if response.success and response.suggestion:
        suggestion = response.suggestion
        metadata = suggestion.metadata

        print(f"\n   Model: {suggestion.model_used}")
        print(f"   Processing time: {suggestion.processing_time_ms}ms")
        print(f"   Overall confidence: {suggestion.confidence.overall:.2f}")

        print(f"\n   Title: {metadata.titelcollectie.officiele_titel}")

        print("\n   Categories:")
        for cat in metadata.classificatiecollectie.informatiecategorieen:
            print(f"      - {cat.categorie.name}: {cat.categorie.label}")

        if metadata.classificatiecollectie.trefwoorden:
            print(f"\n   Keywords: {', '.join(metadata.classificatiecollectie.trefwoorden)}")

        if metadata.omschrijvingen:
            print(f"\n   Description: {metadata.omschrijvingen[0][:200]}...")

        # Save full output
        output_file = filepath.with_suffix(".metadata.json")
        output_data = {
            "source_file": str(filepath),
            "success": response.success,
            "request_id": response.request_id,
            "suggestion": {
                "metadata": metadata.model_dump(mode="json", by_alias=True),
                "confidence": suggestion.confidence.model_dump(),
                "model_used": suggestion.model_used,
                "processing_time_ms": suggestion.processing_time_ms,
            },
        }
        output_file.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
        print(f"\n   Full output saved to: {output_file}")

    else:
        print(f"\n   ERROR: {response.error}")


async def test_all_samples() -> None:
    """Test metadata generation for all sample documents."""
    if not SAMPLES_DIR.exists():
        print(f"Samples directory not found: {SAMPLES_DIR}")
        print("Run: uv run python scripts/download_samples.py")
        return

    pdf_files = list(SAMPLES_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in samples directory")
        print("Run: uv run python scripts/download_samples.py")
        return

    print(f"Found {len(pdf_files)} sample documents")

    for pdf_file in pdf_files:
        await test_single_file(pdf_file)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test metadata generation")
    parser.add_argument("--file", "-f", type=Path, help="Specific file to test")
    parser.add_argument("--publisher", "-p", help="Publisher name hint")
    args = parser.parse_args()

    if args.file:
        if not args.file.exists():
            print(f"File not found: {args.file}")
            return
        asyncio.run(test_single_file(args.file, args.publisher))
    else:
        asyncio.run(test_all_samples())


if __name__ == "__main__":
    main()
