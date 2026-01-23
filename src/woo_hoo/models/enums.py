"""Controlled vocabularies and enums for DIWOO metadata.

These enums correspond to the waardelijsten (value lists) from the DIWOO XSD schema
and TOOI (Thesaurus en Ontologie voor Officiële Informatievoorziening).
"""

from __future__ import annotations

from enum import Enum


class InformatieCategorie(str, Enum):
    """The 17 Woo information categories from Artikel 3.3 Wet open overheid.

    Each category maps to a TOOI URI at:
    https://identifier.overheid.nl/tooi/def/thes/kern/{value}
    """

    # Lid 1 - Verplicht actief openbaar te maken (geen uitzonderingen)
    WETTEN_AVV = "c_4191a648"  # 3.3.1a: wetten en algemeen verbindende voorschriften
    OVERIGE_BESLUITEN_AS = "c_237d1cf1"  # 3.3.1b: overige besluiten van algemene strekking
    ONTWERPEN_REGELGEVING = "c_fdee54ae"  # 3.3.1c: ontwerpen van regelgeving met adviesaanvraag
    ORGANISATIE_WERKWIJZE = "c_9f5cc14e"  # 3.3.1d: organisatie en werkwijze
    BEREIKBAARHEID = "c_e8bf4b9e"  # 3.3.1e: bereikbaarheidsgegevens

    # Lid 2 - Verplicht actief openbaar te maken (met uitzonderingen)
    INGEKOMEN_STUKKEN = "c_a3a6e5cf"  # 3.3.2a: bij vertegenwoordigende organen ingekomen stukken
    VERGADERSTUKKEN_SG = "c_7ebb6ba0"  # 3.3.2b: vergaderstukken Staten-Generaal
    VERGADERSTUKKEN_DECENTRAAL = "c_92a74153"  # 3.3.2c: vergaderstukken decentrale overheden
    AGENDAS_BESLUITENLIJSTEN = "c_5540d806"  # 3.3.2d: agenda's en besluitenlijsten bestuurscolleges
    ADVIEZEN = "c_5ba23c01"  # 3.3.2e: adviezen
    CONVENANTEN = "c_9fe65c9f"  # 3.3.2f: convenanten
    JAARPLANNEN_JAARVERSLAGEN = "c_9b4ab167"  # 3.3.2g: jaarplannen en jaarverslagen
    SUBSIDIES_ANDERS = "c_8ac47458"  # 3.3.2h: subsidieverplichtingen anders dan met beschikking
    WOO_VERZOEKEN = "c_4edc7ff0"  # 3.3.2i: Woo-verzoeken en -besluiten
    ONDERZOEKSRAPPORTEN = "c_28fb3d66"  # 3.3.2j: onderzoeksrapporten
    BESCHIKKINGEN = "c_0b6bd881"  # 3.3.2k: beschikkingen
    KLACHTOORDELEN = "c_b2f30ab9"  # 3.3.2l: klachtoordelen

    @property
    def label(self) -> str:
        """Human-readable Dutch label for this category."""
        return INFORMATIECATEGORIE_LABELS[self]

    @property
    def tooi_uri(self) -> str:
        """Full TOOI URI for this category."""
        return f"https://identifier.overheid.nl/tooi/def/thes/kern/{self.value}"

    @property
    def artikel(self) -> str:
        """Article reference in Woo (e.g., '3.3.1a')."""
        return INFORMATIECATEGORIE_ARTIKELEN[self]


INFORMATIECATEGORIE_LABELS: dict[InformatieCategorie, str] = {
    InformatieCategorie.WETTEN_AVV: "Wetten en algemeen verbindende voorschriften",
    InformatieCategorie.OVERIGE_BESLUITEN_AS: "Overige besluiten van algemene strekking",
    InformatieCategorie.ONTWERPEN_REGELGEVING: "Ontwerpen van regelgeving met adviesaanvraag",
    InformatieCategorie.ORGANISATIE_WERKWIJZE: "Organisatie en werkwijze",
    InformatieCategorie.BEREIKBAARHEID: "Bereikbaarheidsgegevens",
    InformatieCategorie.INGEKOMEN_STUKKEN: "Bij vertegenwoordigende organen ingekomen stukken",
    InformatieCategorie.VERGADERSTUKKEN_SG: "Vergaderstukken Staten-Generaal",
    InformatieCategorie.VERGADERSTUKKEN_DECENTRAAL: "Vergaderstukken decentrale overheden",
    InformatieCategorie.AGENDAS_BESLUITENLIJSTEN: "Agenda's en besluitenlijsten bestuurscolleges",
    InformatieCategorie.ADVIEZEN: "Adviezen",
    InformatieCategorie.CONVENANTEN: "Convenanten",
    InformatieCategorie.JAARPLANNEN_JAARVERSLAGEN: "Jaarplannen en jaarverslagen",
    InformatieCategorie.SUBSIDIES_ANDERS: "Subsidieverplichtingen anders dan met beschikking",
    InformatieCategorie.WOO_VERZOEKEN: "Woo-verzoeken en -besluiten",
    InformatieCategorie.ONDERZOEKSRAPPORTEN: "Onderzoeksrapporten",
    InformatieCategorie.BESCHIKKINGEN: "Beschikkingen",
    InformatieCategorie.KLACHTOORDELEN: "Klachtoordelen",
}

INFORMATIECATEGORIE_ARTIKELEN: dict[InformatieCategorie, str] = {
    InformatieCategorie.WETTEN_AVV: "3.3.1a",
    InformatieCategorie.OVERIGE_BESLUITEN_AS: "3.3.1b",
    InformatieCategorie.ONTWERPEN_REGELGEVING: "3.3.1c",
    InformatieCategorie.ORGANISATIE_WERKWIJZE: "3.3.1d",
    InformatieCategorie.BEREIKBAARHEID: "3.3.1e",
    InformatieCategorie.INGEKOMEN_STUKKEN: "3.3.2a",
    InformatieCategorie.VERGADERSTUKKEN_SG: "3.3.2b",
    InformatieCategorie.VERGADERSTUKKEN_DECENTRAAL: "3.3.2c",
    InformatieCategorie.AGENDAS_BESLUITENLIJSTEN: "3.3.2d",
    InformatieCategorie.ADVIEZEN: "3.3.2e",
    InformatieCategorie.CONVENANTEN: "3.3.2f",
    InformatieCategorie.JAARPLANNEN_JAARVERSLAGEN: "3.3.2g",
    InformatieCategorie.SUBSIDIES_ANDERS: "3.3.2h",
    InformatieCategorie.WOO_VERZOEKEN: "3.3.2i",
    InformatieCategorie.ONDERZOEKSRAPPORTEN: "3.3.2j",
    InformatieCategorie.BESCHIKKINGEN: "3.3.2k",
    InformatieCategorie.KLACHTOORDELEN: "3.3.2l",
}


class DocumentSoort(str, Enum):
    """Document types from TOOI documentsoortlijst."""

    BRIEF = "c_brief"
    NOTA = "c_nota"
    RAPPORT = "c_rapport"
    BESLUIT = "c_besluit"
    ADVIES = "c_advies"
    NOTULEN = "c_notulen"
    AGENDA = "c_agenda"
    VERSLAG = "c_verslag"
    CONVENANT = "c_convenant"
    OVEREENKOMST = "c_overeenkomst"
    BELEIDSREGEL = "c_beleidsregel"
    CIRCULAIRE = "c_circulaire"
    BESCHIKKING = "c_beschikking"
    WOO_BESLUIT = "c_woo_besluit"
    ONDERZOEKSRAPPORT = "c_onderzoeksrapport"
    JAARVERSLAG = "c_jaarverslag"
    JAARPLAN = "c_jaarplan"
    KLACHTOORDEEL = "c_klachtoordeel"
    MEMORIE_VAN_TOELICHTING = "c_memorie_van_toelichting"
    AMENDEMENT = "c_amendement"
    MOTIE = "c_motie"

    @property
    def label(self) -> str:
        """Human-readable Dutch label."""
        return DOCUMENTSOORT_LABELS.get(self, self.name.lower().replace("_", " "))

    @property
    def tooi_uri(self) -> str:
        """Full TOOI URI."""
        return f"https://identifier.overheid.nl/tooi/def/thes/kern/{self.value}"


DOCUMENTSOORT_LABELS: dict[DocumentSoort, str] = {
    DocumentSoort.BRIEF: "Brief",
    DocumentSoort.NOTA: "Nota",
    DocumentSoort.RAPPORT: "Rapport",
    DocumentSoort.BESLUIT: "Besluit",
    DocumentSoort.ADVIES: "Advies",
    DocumentSoort.NOTULEN: "Notulen",
    DocumentSoort.AGENDA: "Agenda",
    DocumentSoort.VERSLAG: "Verslag",
    DocumentSoort.CONVENANT: "Convenant",
    DocumentSoort.OVEREENKOMST: "Overeenkomst",
    DocumentSoort.BELEIDSREGEL: "Beleidsregel",
    DocumentSoort.CIRCULAIRE: "Circulaire",
    DocumentSoort.BESCHIKKING: "Beschikking",
    DocumentSoort.WOO_BESLUIT: "Woo-besluit",
    DocumentSoort.ONDERZOEKSRAPPORT: "Onderzoeksrapport",
    DocumentSoort.JAARVERSLAG: "Jaarverslag",
    DocumentSoort.JAARPLAN: "Jaarplan",
    DocumentSoort.KLACHTOORDEEL: "Klachtoordeel",
    DocumentSoort.MEMORIE_VAN_TOELICHTING: "Memorie van toelichting",
    DocumentSoort.AMENDEMENT: "Amendement",
    DocumentSoort.MOTIE: "Motie",
}


class SoortHandeling(str, Enum):
    """Document handling types from TOOI soorthandelinglijst."""

    ONTVANGST = "c_ontvangst"
    VASTSTELLING = "c_vaststelling"
    ONDERTEKENING = "c_ondertekening"
    PUBLICATIE = "c_publicatie"
    INWERKINGTREDING = "c_inwerkingtreding"
    WIJZIGING = "c_wijziging"
    INTREKKING = "c_intrekking"
    REGISTRATIE = "c_registratie"

    @property
    def label(self) -> str:
        """Human-readable Dutch label."""
        return SOORTHANDELING_LABELS.get(self, self.name.lower())

    @property
    def tooi_uri(self) -> str:
        """Full TOOI URI."""
        return f"https://identifier.overheid.nl/tooi/def/thes/kern/{self.value}"


SOORTHANDELING_LABELS: dict[SoortHandeling, str] = {
    SoortHandeling.ONTVANGST: "Ontvangst",
    SoortHandeling.VASTSTELLING: "Vaststelling",
    SoortHandeling.ONDERTEKENING: "Ondertekening",
    SoortHandeling.PUBLICATIE: "Publicatie",
    SoortHandeling.INWERKINGTREDING: "Inwerkingtreding",
    SoortHandeling.WIJZIGING: "Wijziging",
    SoortHandeling.INTREKKING: "Intrekking",
    SoortHandeling.REGISTRATIE: "Registratie",
}


class Taal(str, Enum):
    """Language codes from TOOI taallijst (ISO 639-1)."""

    NL = "c_nl"  # Nederlands
    EN = "c_en"  # Engels
    DE = "c_de"  # Duits
    FR = "c_fr"  # Frans
    FY = "c_fy"  # Fries
    PAP = "c_pap"  # Papiaments

    @property
    def label(self) -> str:
        """Human-readable Dutch label."""
        return TAAL_LABELS.get(self, self.name)

    @property
    def tooi_uri(self) -> str:
        """Full TOOI URI."""
        return f"https://identifier.overheid.nl/tooi/def/thes/kern/{self.value}"


TAAL_LABELS: dict[Taal, str] = {
    Taal.NL: "Nederlands",
    Taal.EN: "Engels",
    Taal.DE: "Duits",
    Taal.FR: "Frans",
    Taal.FY: "Fries",
    Taal.PAP: "Papiaments",
}


class DocumentRelatie(str, Enum):
    """Document relationship types from TOOI documentrelatielijst."""

    VERVANGT = "c_vervangt"
    WORDT_VERVANGEN_DOOR = "c_wordt_vervangen_door"
    WIJZIGT = "c_wijzigt"
    WORDT_GEWIJZIGD_DOOR = "c_wordt_gewijzigd_door"
    INTREKT = "c_intrekt"
    WORDT_INGETROKKEN_DOOR = "c_wordt_ingetrokken_door"
    HEEFT_BIJLAGE = "c_heeft_bijlage"
    IS_BIJLAGE_VAN = "c_is_bijlage_van"

    @property
    def label(self) -> str:
        """Human-readable Dutch label."""
        return self.name.lower().replace("_", " ")

    @property
    def tooi_uri(self) -> str:
        """Full TOOI URI."""
        return f"https://identifier.overheid.nl/tooi/def/thes/kern/{self.value}"


class RedenVerwijderingVervanging(str, Enum):
    """Reasons for document removal/replacement from TOOI."""

    ONJUISTE_INFORMATIE = "c_onjuiste_informatie"
    PRIVACYGEVOELIGE_INFORMATIE = "c_privacygevoelige_informatie"
    TECHNISCHE_FOUT = "c_technische_fout"
    VERVANGING_DOOR_NIEUWE_VERSIE = "c_vervanging_door_nieuwe_versie"

    @property
    def label(self) -> str:
        """Human-readable Dutch label."""
        return self.name.lower().replace("_", " ")

    @property
    def tooi_uri(self) -> str:
        """Full TOOI URI."""
        return f"https://identifier.overheid.nl/tooi/def/thes/kern/{self.value}"
