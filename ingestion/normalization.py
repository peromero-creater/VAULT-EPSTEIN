import pycountry # I'll add this to requirements if needed, or use a static map

# ISO-3166 Alpha-2 mapping (simplified)
COUNTRY_MAP = {
    "USA": "US", "UNITED STATES": "US", "U.S.": "US", "AMERICA": "US",
    "UK": "GB", "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB",
    "TURKEY": "TR", "TÜRKİYE": "TR", "TURKIYE": "TR",
    "CHINA": "CN", "PRC": "CN",
    "RUSSIA": "RU", "RUSSIAN FEDERATION": "RU",
    "ISRAEL": "IL",
    "PALESTINE": "PS",
    "UKRAINE": "UA",
    "GERMANY": "DE",
    "FRANCE": "FR",
    # ... can be expanded
}

def normalize_country(text: str) -> str:
    """Maps a location name to an ISO-3166 Alpha-2 code."""
    cleaned = text.upper().strip()
    if cleaned in COUNTRY_MAP:
        return COUNTRY_MAP[cleaned]
    
    # Simple fallback or fuzzy match could go here
    return None
