import re

# Canonical mapping of lowercase variants to canonical venue names
CANONICAL_VENUES = {
    # Chinnaswamy
    "m chinnaswamy stadium": "M Chinnaswamy Stadium",
    "m chinnaswamy stadium bengaluru": "M Chinnaswamy Stadium",
    "m chinnaswamy stadium bangalore": "M Chinnaswamy Stadium",
    "m chinnaswamy stadium bengaluru": "M Chinnaswamy Stadium",
    "m.chinnaswamy stadium": "M Chinnaswamy Stadium",
    "m. chinnaswamy stadium": "M Chinnaswamy Stadium",
    
    # MA Chidambaram
    "ma chidambaram stadium": "MA Chidambaram Stadium, Chepauk",
    "ma chidambaram stadium chepauk": "MA Chidambaram Stadium, Chepauk",
    "ma chidambaram stadium chepauk chennai": "MA Chidambaram Stadium, Chepauk",
    "m a chidambaram stadium": "MA Chidambaram Stadium, Chepauk",
    "m a chidambaram stadium chepauk": "MA Chidambaram Stadium, Chepauk",
    "m.a. chidambaram stadium": "MA Chidambaram Stadium, Chepauk",
    "m.a. chidambaram stadium chepauk": "MA Chidambaram Stadium, Chepauk",
    
    # Rajiv Gandhi
    "rajiv gandhi international stadium": "Rajiv Gandhi International Stadium, Uppal",
    "rajiv gandhi international stadium uppal": "Rajiv Gandhi International Stadium, Uppal",
    "rajiv gandhi international stadium uppal hyderabad": "Rajiv Gandhi International Stadium, Uppal",
    
    # Punjab Cricket Association
    "punjab cricket association is bindra stadium": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "punjab cricket association is bindra stadium mohali": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "punjab cricket association is bindra stadium mohali chandigarh": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "punjab cricket association stadium": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "punjab cricket association stadium mohali": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    
    # Dr DY Patil
    "dr dy patil sports academy": "Dr DY Patil Sports Academy",
    "dr dy patil sports academy mumbai": "Dr DY Patil Sports Academy",
    
    # Dr YS Rajasekhara Reddy
    "dr. y.s. rajasekhara reddy aca-vdca cricket stadium": "Dr YS Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "dr. y.s. rajasekhara reddy aca-vdca cricket stadium visakhapatnam": "Dr YS Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "dr y s rajasekhara reddy aca vdca cricket stadium": "Dr YS Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "dr. y.s. rajasekhara reddy aca-vdca cricket stadium, visakhapatnam": "Dr YS Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    
    # Brabourne
    "brabourne stadium": "Brabourne Stadium",
    "brabourne stadium mumbai": "Brabourne Stadium",
    
    # Wankhede
    "wankhede stadium": "Wankhede Stadium",
    "wankhede stadium mumbai": "Wankhede Stadium",
    
    # Eden Gardens
    "eden gardens": "Eden Gardens",
    "eden gardens kolkata": "Eden Gardens",
    
    # Arun Jaitley
    "arun jaitley stadium": "Arun Jaitley Stadium",
    "arun jaitley stadium delhi": "Arun Jaitley Stadium",
    
    # Feroz Shah Kotla
    "feroz shah kotla": "Feroz Shah Kotla",
    
    # Maharaja Yadavindra Singh
    "maharaja yadavindra singh international cricket stadium mullanpur": "Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur",
    "maharaja yadavindra singh international cricket stadium new chandigarh": "Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur",
    "maharaja yadavindra singh international cricket stadium": "Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur",
    
    # Maharashtra Cricket Association
    "maharashtra cricket association stadium": "Maharashtra Cricket Association Stadium",
    "maharashtra cricket association stadium pune": "Maharashtra Cricket Association Stadium",
    
    # Saurashtra
    "saurashtra cricket association stadium": "Saurashtra Cricket Association Stadium",
    
    # Sawai Mansingh
    "sawai mansingh stadium": "Sawai Mansingh Stadium",
    "sawai mansingh stadium jaipur": "Sawai Mansingh Stadium",
    
    # Shaheed Veer Narayan Singh
    "shaheed veer narayan singh international stadium": "Shaheed Veer Narayan Singh International Stadium",
    "shaheed veer narayan singh international stadium raipur": "Shaheed Veer Narayan Singh International Stadium",
    
    # Sharjah
    "sharjah cricket stadium": "Sharjah Cricket Stadium",
    
    # Dubai
    "dubai international cricket stadium": "Dubai International Cricket Stadium",
    
    # Sheikh Zayed / Zayed Cricket Stadium
    "sheikh zayed stadium": "Sheikh Zayed Stadium",
    "zayed cricket stadium": "Sheikh Zayed Stadium",
    "zayed cricket stadium abu dhabi": "Sheikh Zayed Stadium",
    
    # Himachal Pradesh
    "himachal pradesh cricket association stadium": "Himachal Pradesh Cricket Association Stadium",
    "himachal pradesh cricket association stadium dharamsala": "Himachal Pradesh Cricket Association Stadium",
    
    # Subrata Roy Sahara
    "subrata roy sahara stadium": "Subrata Roy Sahara Stadium",
    
    # Barsapara
    "barsapara cricket stadium guwahati": "Barsapara Cricket Stadium",
    "barsapara cricket stadium": "Barsapara Cricket Stadium",
    
    # Ekana
    "bharat ratna shri atal bihari vajpayee ekana cricket stadium lucknow": "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium",
    "bharat ratna shri atal bihari vajpayee ekana cricket stadium": "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium",
}

# Maps lowercase historical/renamed venues to their canonical physical venue
VENUE_ALIASES = {
    # Feroz Shah Kotla / Arun Jaitley
    "feroz shah kotla": "Arun Jaitley Stadium",
    
    # Sardar Patel / Narendra Modi
    "sardar patel stadium motera": "Narendra Modi Stadium",
    "sardar patel stadium": "Narendra Modi Stadium",
    
    # Punjab Cricket Association
    "punjab cricket association stadium": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "punjab cricket association is bindra stadium": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "pca is bindra stadium": "Punjab Cricket Association IS Bindra Stadium, Mohali",
}


def normalize_venue_name(venue_name: str, city: str = None) -> str:
    """
    Normalize a venue name to a canonical spelling.
    - removes duplicate city suffixes
    - normalizes punctuation (e.g. dots to spaces)
    - collapses multiple spaces
    - trims whitespace
    - applies a canonical mapping
    """
    if not venue_name:
        return ""
        
    # Replace dots with space
    name = venue_name.replace(".", " ")
    
    # Collapse multiple spaces and trim
    name = " ".join(name.split())
    
    # If city is supplied, clean it up and try to strip it case-insensitively from the end
    if city:
        city_clean = city.strip()
        # strip ", city" or " city"
        pattern = re.compile(rf"\s*,\s*{re.escape(city_clean)}\s*$", re.IGNORECASE)
        name = pattern.sub("", name)
        pattern2 = re.compile(rf"\s+{re.escape(city_clean)}\s*$", re.IGNORECASE)
        name = pattern2.sub("", name)
        
    # Standard cleanup of other common city suffixes just in case
    common_cities = [
        "Mumbai", "Delhi", "Kolkata", "Chennai", "Bengaluru", "Bangalore", 
        "Hyderabad", "Rajkot", "Jaipur", "Pune", "Chandigarh", "Mohali", 
        "Visakhapatnam", "Dharamsala", "Raipur", "Ranchi", "Indore", "Kochi", 
        "Kanpur", "Nagpur", "Guwahati", "Lucknow", "Centurion", "Johannesburg", 
        "Cape Town", "Durban", "Port Elizabeth", "East London", "Kimberley", 
        "Bloemfontein", "Abu Dhabi", "Sharjah", "Dubai", "New Chandigarh"
    ]
    for c in common_cities:
        pattern = re.compile(rf"\s*,\s*{re.escape(c)}\s*$", re.IGNORECASE)
        name = pattern.sub("", name)
        pattern2 = re.compile(rf"\s+{re.escape(c)}\s*$", re.IGNORECASE)
        name = pattern2.sub("", name)
        
    # Clean up commas and collapse spaces again
    name = name.replace(",", " ")
    name = " ".join(name.split()).strip()
    
    # Check canonical dictionary
    name_lower = name.lower()
    if name_lower in CANONICAL_VENUES:
        name = CANONICAL_VENUES[name_lower]
        
    # Check historical renames / aliases
    name_lower = name.lower()
    if name_lower in VENUE_ALIASES:
        return VENUE_ALIASES[name_lower]
        
    return name


def normalize_city(venue_name: str, city: str = None) -> str:
    """
    Normalize the city name based on the venue name and input city.
    """
    normalized_venue = normalize_venue_name(venue_name, city)
    normalized_venue_lower = normalized_venue.lower()
    
    # Overrides based on venue
    if "dubai" in normalized_venue_lower:
        return "Dubai"
    if "sharjah" in normalized_venue_lower:
        return "Sharjah"
    if "abu dhabi" in normalized_venue_lower or "zayed" in normalized_venue_lower:
        return "Abu Dhabi"
    if "maharaja yadavindra singh" in normalized_venue_lower or "mullanpur" in normalized_venue_lower:
        return "New Chandigarh"
    if "dy patil" in normalized_venue_lower:
        return "Mumbai"
    if "arun jaitley" in normalized_venue_lower or "feroz shah" in normalized_venue_lower:
        return "Delhi"
    if "narendra modi" in normalized_venue_lower or "sardar patel" in normalized_venue_lower:
        return "Ahmedabad"
    if "punjab cricket" in normalized_venue_lower or "is bindra" in normalized_venue_lower or "pca is bindra" in normalized_venue_lower:
        return "Mohali"
        
    if not city:
        return None
        
    city_clean = city.strip()
    
    city_map = {
        "bengaluru": "Bengaluru",
        "bangalore": "Bengaluru",
    }
    
    city_lower = city_clean.lower()
    if city_lower in city_map:
        return city_map[city_lower]
        
    return city_clean
