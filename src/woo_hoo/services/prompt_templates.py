"""LLM prompt templates for DIWOO metadata extraction.

These prompts are designed in Dutch to optimize extraction quality
for Dutch government documents.
"""

from __future__ import annotations

from string import Template

from woo_hoo.models.enums import INFORMATIECATEGORIE_LABELS

# Build category list for prompt
CATEGORY_LIST = "\n".join(
    f"- {cat.name}: {label} (artikel {cat.artikel})" for cat, label in INFORMATIECATEGORIE_LABELS.items()
)

SYSTEM_PROMPT = (
    """Je bent een expert in Nederlandse overheidsmetadata en de Wet open overheid (Woo).
Je taak is het analyseren van documentinhoud en het genereren van DIWOO-conforme metadata.

Je hebt kennis van:
- De 17 Woo-informatiecategorieën uit artikel 3.3
- TOOI-waardelijsten voor documentsoorten, thema's en organisaties
- DIWOO XSD-schemastructuur en -vereisten

De 17 Woo-informatiecategorieën zijn:
"""
    + CATEGORY_LIST
    + """

Belangrijke regels:
1. Selecteer ALTIJD minimaal één informatiecategorie uit de 17 Woo-categorieën
2. Genereer een officiële titel die het document accuraat beschrijft
3. Wees conservatief met confidentiescores - alleen hoog (>0.8) bij duidelijk bewijs
4. Alle tekst moet in het Nederlands zijn tenzij het document in een andere taal is
5. Gebruik alleen categorieën die echt van toepassing zijn

Antwoord ALLEEN met valid JSON volgens het gegeven schema. Geen markdown, geen uitleg."""
)

EXTRACTION_PROMPT_TEMPLATE = Template("""Analyseer het volgende documentfragment en genereer DIWOO-conforme metadata.

DOCUMENTINHOUD:
---
$document_text
---
$publisher_hint

Genereer metadata in exact het volgende JSON-formaat:
{
    "officiele_titel": "De officiële titel van het document (verplicht, max 200 tekens)",
    "verkorte_titels": ["Optionele korte titel"] of null,
    "omschrijvingen": ["Korte beschrijving van de inhoud (max 500 tekens)"] of null,
    "informatiecategorieen": [
        {
            "categorie": "NAAM_VAN_CATEGORIE (kies uit de 17 categorieën)",
            "confidence": 0.0 tot 1.0,
            "reasoning": "Korte uitleg waarom deze categorie"
        }
    ],
    "documentsoorten": ["BRIEF", "NOTA", "RAPPORT", "BESLUIT", "ADVIES", "NOTULEN", "AGENDA", "VERSLAG", etc.] of null,
    "trefwoorden": ["Relevante zoektermen in Nederlands"],
    "taal": "NL",
    "creatiedatum": "YYYY-MM-DD indien te bepalen uit document, anders null",
    "confidence_scores": {
        "titel": 0.0 tot 1.0,
        "informatiecategorie": 0.0 tot 1.0,
        "overall": 0.0 tot 1.0
    }
}

Mogelijke informatiecategorieën (kies de juiste naam):
$category_options

Mogelijke documentsoorten:
BRIEF, NOTA, RAPPORT, BESLUIT, ADVIES, NOTULEN, AGENDA, VERSLAG, CONVENANT, OVEREENKOMST, BELEIDSREGEL, CIRCULAIRE, BESCHIKKING, WOO_BESLUIT, ONDERZOEKSRAPPORT, JAARVERSLAG, JAARPLAN, KLACHTOORDEEL, MEMORIE_VAN_TOELICHTING, AMENDEMENT, MOTIE

Tips voor analyse:
- Kijk naar briefhoofden, ondertekeningen en referentienummers
- Let op datumnotaties en tijdsaanduidingen
- Identificeer juridische termen die wijzen op specifieke documentsoorten
- Bij twijfel: lagere confidence score en meerdere mogelijke categorieën""")


def build_extraction_prompt(
    document_text: str,
    publisher_hint: str | None = None,
    max_text_length: int = 15000,
) -> str:
    """Build the extraction prompt with document text.

    Args:
        document_text: Extracted text content from the document
        publisher_hint: Optional hint about the publishing organization
        max_text_length: Maximum text length to include (truncates if longer)

    Returns:
        Formatted prompt string
    """
    # Truncate text if too long
    truncated_text = document_text[:max_text_length]
    if len(document_text) > max_text_length:
        truncated_text += "\n\n[... TEKST AFGEKAPT WEGENS LENGTE ...]"

    # Build publisher hint section
    publisher_section = ""
    if publisher_hint:
        publisher_section = f"\nPUBLISHER: Dit document is afkomstig van: {publisher_hint}\n"

    # Build category options
    category_options = "\n".join(f"{cat.name} = {label}" for cat, label in INFORMATIECATEGORIE_LABELS.items())

    return EXTRACTION_PROMPT_TEMPLATE.substitute(
        document_text=truncated_text,
        publisher_hint=publisher_section,
        category_options=category_options,
    )


def get_system_prompt() -> str:
    """Get the system prompt for metadata extraction.

    Returns:
        System prompt string
    """
    return SYSTEM_PROMPT
