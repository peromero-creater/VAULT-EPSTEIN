try:
    import pycountry
except ImportError:
    pycountry = None

# ISO-3166 Alpha-2 mapping (explicit priorities)
COUNTRY_MAP = {
    "USA": "US", "UNITED STATES": "US", "U.S.": "US", "AMERICA": "US", "US": "US",
    "UK": "GB", "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB", "ENGLAND": "GB",
    "TURKEY": "TR", "TÜRKİYE": "TR", "TURKIYE": "TR",
    "CHINA": "CN", "PRC": "CN",
    "RUSSIA": "RU", "RUSSIAN FEDERATION": "RU",
    "ISRAEL": "IL",
    "PALESTINE": "PS",
    "UKRAINE": "UA",
    "GERMANY": "DE",
    "FRANCE": "FR",
    "ITALY": "IT",
    "SPAIN": "ES",
    "CANADA": "CA",
    "MEXICO": "MX",
    "COLOMBIA": "CO",
    "ARGENTINA": "AR",
    "BRAZIL": "BR",
    "SAUDI ARABIA": "SA",
    "UAE": "AE",
    "QATAR": "QA",
    "JAPAN": "JP",
    "SOUTH KOREA": "KR",
    "INDIA": "IN",
    "AUSTRALIA": "AU",
    "BAHAMAS": "BS",
    "US VIRGIN ISLANDS": "VI",
    "VIRGIN ISLANDS": "VI",
    "LITTLE ST. JAMES": "VI",
}

def normalize_country(text: str) -> str:
    """Maps a location name to an ISO-3166 Alpha-2 code."""
    cleaned = text.upper().strip()
    
    # 1. Manual map check (High accuracy)
    if cleaned in COUNTRY_MAP:
        return COUNTRY_MAP[cleaned]
    
    # 2. Pycountry fallback (Broad coverage)
    if pycountry:
        try:
            # Check by name
            country = pycountry.countries.get(name=text.title())
            if country:
                return country.alpha_2
            
            # Fuzzy/Search
            results = pycountry.countries.search_fuzzy(text)
            if results:
                return results[0].alpha_2
        except:
            pass
            
    return None
