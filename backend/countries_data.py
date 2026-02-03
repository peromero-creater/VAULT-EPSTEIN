"""
Comprehensive Country Data for Globe Visualization
Includes coordinates, names, and metadata for 50+ countries
"""

COUNTRY_DATA = {
    # North America
    'US': {'lat': 37.0902, 'lng': -95.7129, 'name': 'UNITED STATES', 'region': 'North America'},
    'CA': {'lat': 56.1304, 'lng': -106.3468, 'name': 'CANADA', 'region': 'North America'},
    'MX': {'lat': 23.6345, 'lng': -102.5528, 'name': 'MEXICO', 'region': 'North America'},
    
    # Caribbean & Central America
    'VI': {'lat': 18.3358, 'lng': -64.8963, 'name': 'US VIRGIN ISLANDS', 'region': 'Caribbean'},
    'BS': {'lat': 25.0343, 'lng': -77.3963, 'name': 'BAHAMAS', 'region': 'Caribbean'},
    'PR': {'lat': 18.2208, 'lng': -66.5901, 'name': 'PUERTO RICO', 'region': 'Caribbean'},
    'PA': {'lat': 8.5380, 'lng': -80.7821, 'name': 'PANAMA', 'region': 'Central America'},
    
    # South America
    'BR': {'lat': -14.2350, 'lng': -51.9253, 'name': 'BRAZIL', 'region': 'South America'},
    'AR': {'lat': -38.4161, 'lng': -63.6167, 'name': 'ARGENTINA', 'region': 'South America'},
    'CO': {'lat': 4.5709, 'lng': -74.2973, 'name': 'COLOMBIA', 'region': 'South America'},
    
    # Western Europe
    'GB': {'lat': 55.3781, 'lng': -3.4360, 'name': 'UNITED KINGDOM', 'region': 'Europe'},
    'FR': {'lat': 46.2276, 'lng': 2.2137, 'name': 'FRANCE', 'region': 'Europe'},
    'DE': {'lat': 51.1657, 'lng': 10.4515, 'name': 'GERMANY', 'region': 'Europe'},
    'ES': {'lat': 40.4637, 'lng': -3.7492, 'name': 'SPAIN', 'region': 'Europe'},
    'IT': {'lat': 41.8719, 'lng': 12.5674, 'name': 'ITALY', 'region': 'Europe'},
    'CH': {'lat': 46.8182, 'lng': 8.2275, 'name': 'SWITZERLAND', 'region': 'Europe'},
    'NL': {'lat': 52.1326, 'lng': 5.2913, 'name': 'NETHERLANDS', 'region': 'Europe'},
    'BE': {'lat': 50.5039, 'lng': 4.4699, 'name': 'BELGIUM', 'region': 'Europe'},
    'AT': {'lat': 47.5162, 'lng': 14.5501, 'name': 'AUSTRIA', 'region': 'Europe'},
    
    # Eastern Europe
    'RU': {'lat': 61.5240, 'lng': 105.3188, 'name': 'RUSSIA', 'region': 'Europe'},
    'UA': {'lat': 48.3794, 'lng': 31.1656, 'name': 'UKRAINE', 'region': 'Europe'},
    'PL': {'lat': 51.9194, 'lng': 19.1451, 'name': 'POLAND', 'region': 'Europe'},
    'CZ': {'lat': 49.8175, 'lng': 15.4730, 'name': 'CZECH REPUBLIC', 'region': 'Europe'},
    
    # Scandinavia
    'SE': {'lat': 60.1282, 'lng': 18.6435, 'name': 'SWEDEN', 'region': 'Europe'},
    'NO': {'lat': 60.4720, 'lng': 8.4689, 'name': 'NORWAY', 'region': 'Europe'},
    'DK': {'lat': 56.2639, 'lng': 9.5018, 'name': 'DENMARK', 'region': 'Europe'},
    'FI': {'lat': 61.9241, 'lng': 25.7482, 'name': 'FINLAND', 'region': 'Europe'},
    
    # Middle East
    'IL': {'lat': 31.0461, 'lng': 34.8516, 'name': 'ISRAEL', 'region': 'Middle East'},
    'SA': {'lat': 23.8859, 'lng': 45.0792, 'name': 'SAUDI ARABIA', 'region': 'Middle East'},
    'AE': {'lat': 23.4241, 'lng': 53.8478, 'name': 'UNITED ARAB EMIRATES', 'region': 'Middle East'},
    'TR': {'lat': 38.9637, 'lng': 35.2433, 'name': 'TURKEY', 'region': 'Middle East'},
    'EG': {'lat': 26.8206, 'lng': 30.8025, 'name': 'EGYPT', 'region': 'Middle East'},
    
    # Asia
    'CN': {'lat': 35.8617, 'lng': 104.1954, 'name': 'CHINA', 'region': 'Asia'},
    'JP': {'lat': 36.2048, 'lng': 138.2529, 'name': 'JAPAN', 'region': 'Asia'},
    'IN': {'lat': 20.5937, 'lng': 78.9629, 'name': 'INDIA', 'region': 'Asia'},
    'TH': {'lat': 15.8700, 'lng': 100.9925, 'name': 'THAILAND', 'region': 'Asia'},
    'SG': {'lat': 1.3521, 'lng': 103.8198, 'name': 'SINGAPORE', 'region': 'Asia'},
    'HK': {'lat': 22.3193, 'lng': 114.1694, 'name': 'HONG KONG', 'region': 'Asia'},
    'KR': {'lat': 35.9078, 'lng': 127.7669, 'name': 'SOUTH KOREA', 'region': 'Asia'},
    
    # Oceania
    'AU': {'lat': -25.2744, 'lng': 133.7751, 'name': 'AUSTRALIA', 'region': 'Oceania'},
    'NZ': {'lat': -40.9006, 'lng': 174.8860, 'name': 'NEW ZEALAND', 'region': 'Oceania'},
    
    # Africa
    'ZA': {'lat': -30.5595, 'lng': 22.9375, 'name': 'SOUTH AFRICA', 'region': 'Africa'},
    'MA': {'lat': 31.7917, 'lng': -7.0926, 'name': 'MOROCCO', 'region': 'Africa'},
    'KE': {'lat': -0.0236, 'lng': 37.9062, 'name': 'KENYA', 'region': 'Africa'},
    
    # Additional territories
    'MC': {'lat': 43.7384, 'lng': 7.4246, 'name': 'MONACO', 'region': 'Europe'},
    'LI': {'lat': 47.1660, 'lng': 9.5554, 'name': 'LIECHTENSTEIN', 'region': 'Europe'},
}

def get_country_info(country_code: str) -> dict:
    """Get country information by code"""
    return COUNTRY_DATA.get(country_code.upper(), {
        'lat': 0,
        'lng': 0,
        'name': country_code.upper(),
        'region': 'Unknown'
    })

def get_all_country_codes() -> list:
    """Get list of all supported country codes"""
    return list(COUNTRY_DATA.keys())

def search_countries(query: str) -> list:
    """Search countries by name or code"""
    query = query.upper()
    results = []
    
    for code, info in COUNTRY_DATA.items():
        if query in code or query in info['name']:
            results.append({
                'code': code,
                **info
            })
    
    return results
