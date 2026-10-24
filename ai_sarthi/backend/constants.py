"""
AI Sarthi — Constants and Reference Data
Maharashtra 36 Districts, name aliases, and classification data
"""

# All 36 Maharashtra districts with official current names and historical aliases
MAHARASHTRA_DISTRICTS = [
    {"id": 1,  "name": "Ahmednagar",    "aliases": ["Ahmadnagar", "Ahilyanagar", "Ahmednagar"],    "division": "Pune",      "region": "Western"},
    {"id": 2,  "name": "Akola",         "aliases": ["Akola"],                                       "division": "Amravati",  "region": "Vidarbha"},
    {"id": 3,  "name": "Amravati",      "aliases": ["Amravathi"],                                   "division": "Amravati",  "region": "Vidarbha"},
    {"id": 4,  "name": "Aurangabad",    "aliases": ["Chhatrapati Sambhajinagar", "Sambhajinagar", "Aurangabad"], "division": "Aurangabad", "region": "Marathwada"},
    {"id": 5,  "name": "Beed",          "aliases": ["Bid", "Beed"],                                 "division": "Aurangabad", "region": "Marathwada"},
    {"id": 6,  "name": "Bhandara",      "aliases": ["Bhandara"],                                    "division": "Nagpur",    "region": "Vidarbha"},
    {"id": 7,  "name": "Buldhana",      "aliases": ["Buldhana", "Buldana"],                         "division": "Amravati",  "region": "Vidarbha"},
    {"id": 8,  "name": "Chandrapur",    "aliases": ["Chandrapur"],                                  "division": "Nagpur",    "region": "Vidarbha"},
    {"id": 9,  "name": "Dhule",         "aliases": ["Dhule", "Dhulia"],                             "division": "Nashik",    "region": "Northern"},
    {"id": 10, "name": "Gadchiroli",    "aliases": ["Gadchiroli"],                                  "division": "Nagpur",    "region": "Vidarbha"},
    {"id": 11, "name": "Gondia",        "aliases": ["Gondia", "Gondiya"],                           "division": "Nagpur",    "region": "Vidarbha"},
    {"id": 12, "name": "Hingoli",       "aliases": ["Hingoli"],                                     "division": "Aurangabad", "region": "Marathwada"},
    {"id": 13, "name": "Jalgaon",       "aliases": ["Jalgaon"],                                     "division": "Nashik",    "region": "Northern"},
    {"id": 14, "name": "Jalna",         "aliases": ["Jalna"],                                       "division": "Aurangabad", "region": "Marathwada"},
    {"id": 15, "name": "Kolhapur",      "aliases": ["Kolhapur"],                                    "division": "Pune",      "region": "Western"},
    {"id": 16, "name": "Latur",         "aliases": ["Latur"],                                       "division": "Aurangabad", "region": "Marathwada"},
    {"id": 17, "name": "Mumbai City",   "aliases": ["Mumbai", "Mumbai City", "Mumbai (City)", "Mumbai city"], "division": "Konkan", "region": "Konkan"},
    {"id": 18, "name": "Mumbai Suburban", "aliases": ["Mumbai Suburban", "Mumbai (Suburban)", "Mumbai Sub", "Suburban Mumbai"], "division": "Konkan", "region": "Konkan"},
    {"id": 19, "name": "Nagpur",        "aliases": ["Nagpur"],                                      "division": "Nagpur",    "region": "Vidarbha"},
    {"id": 20, "name": "Nanded",        "aliases": ["Nanded", "Nanded-Waghala"],                    "division": "Aurangabad", "region": "Marathwada"},
    {"id": 21, "name": "Nandurbar",     "aliases": ["Nandurbar"],                                   "division": "Nashik",    "region": "Northern"},
    {"id": 22, "name": "Nashik",        "aliases": ["Nashik", "Nasik"],                             "division": "Nashik",    "region": "Northern"},
    {"id": 23, "name": "Osmanabad",     "aliases": ["Osmanabad", "Dharashiv"],                      "division": "Aurangabad", "region": "Marathwada"},
    {"id": 24, "name": "Palghar",       "aliases": ["Palghar"],                                     "division": "Konkan",    "region": "Konkan"},
    {"id": 25, "name": "Parbhani",      "aliases": ["Parbhani"],                                    "division": "Aurangabad", "region": "Marathwada"},
    {"id": 26, "name": "Pune",          "aliases": ["Pune", "Poona"],                               "division": "Pune",      "region": "Western"},
    {"id": 27, "name": "Raigad",        "aliases": ["Raigad", "Raigarh"],                           "division": "Konkan",    "region": "Konkan"},
    {"id": 28, "name": "Ratnagiri",     "aliases": ["Ratnagiri"],                                   "division": "Konkan",    "region": "Konkan"},
    {"id": 29, "name": "Sangli",        "aliases": ["Sangli"],                                      "division": "Pune",      "region": "Western"},
    {"id": 30, "name": "Satara",        "aliases": ["Satara"],                                      "division": "Pune",      "region": "Western"},
    {"id": 31, "name": "Sindhudurg",    "aliases": ["Sindhudurg"],                                  "division": "Konkan",    "region": "Konkan"},
    {"id": 32, "name": "Solapur",       "aliases": ["Solapur", "Sholapur"],                         "division": "Pune",      "region": "Western"},
    {"id": 33, "name": "Thane",         "aliases": ["Thane", "Thana"],                              "division": "Konkan",    "region": "Konkan"},
    {"id": 34, "name": "Wardha",        "aliases": ["Wardha"],                                      "division": "Nagpur",    "region": "Vidarbha"},
    {"id": 35, "name": "Washim",        "aliases": ["Washim"],                                      "division": "Amravati",  "region": "Vidarbha"},
    {"id": 36, "name": "Yavatmal",      "aliases": ["Yavatmal", "Yvatmal"],                         "division": "Amravati",  "region": "Vidarbha"},
]

# Build lookup dict for alias resolution
_alias_to_canonical: dict[str, str] = {}
for d in MAHARASHTRA_DISTRICTS:
    for alias in d["aliases"]:
        _alias_to_canonical[alias.lower().strip()] = d["name"]

def normalize_district_name(name: str) -> str | None:
    """Return canonical district name or None if not recognised."""
    if not name:
        return None
    key = name.lower().strip()
    return _alias_to_canonical.get(key)

def get_district_by_name(name: str) -> dict | None:
    """Return district dict by any alias, or None."""
    canonical = normalize_district_name(name)
    if not canonical:
        return None
    for d in MAHARASHTRA_DISTRICTS:
        if d["name"] == canonical:
            return d
    return None

DISTRICT_NAMES = [d["name"] for d in MAHARASHTRA_DISTRICTS]
DISTRICT_IDS = {d["name"]: d["id"] for d in MAHARASHTRA_DISTRICTS}

# Financial stages
FINANCIAL_STAGES = {
    "PROPOSED_PIP": "Proposed in Programme Implementation Plan",
    "APPROVED_ROP": "Approved in Record of Proceedings (ROP)",
    "EXPENDITURE": "Actual Expenditure",
    "RELEASE": "Amount Released",
    "STATEWIDE": "Statewide/Pool Total (not individual district)",
}

# Fiscal years available in data
FISCAL_YEARS = ["2022-23", "2023-24", "2024-25", "2025-26"]

# NHM Programme pools
NHM_POOLS = [
    "RCH Flexible Pool",
    "Mission Flexible Pool",
    "NUHM",
    "Immunisation",
    "Family Planning",
    "NDCP",
    "Infrastructure",
    "Human Resources",
    "Training",
    "BCC/IEC",
    "ASHA",
    "Untied Funds",
    "Additionalities",
]

# Health indicators (from Economic Survey / NFHS)
HEALTH_INDICATORS = {
    "population_lakh": "Estimated population in lakh",
    "maternal_mortality_rate": "Maternal Mortality Rate (per 100,000 live births)",
    "infant_mortality_rate": "Infant Mortality Rate (per 1,000 live births)",
    "institutional_deliveries_pct": "Institutional deliveries (%)",
    "immunization_coverage_pct": "Full immunization coverage (%)",
    "anemia_women_pct": "Anaemia prevalence in women (%)",
    "health_facility_count": "Number of health facilities",
    "phc_count": "Primary Health Centres",
    "chc_count": "Community Health Centres",
    "district_hospital_beds": "District hospital beds",
}

# District population estimates (2021 census projection, in lakh)
# Used for per-capita allocation calculations
DISTRICT_POPULATION_LAKH = {
    "Ahmednagar": 36.95,
    "Akola": 18.18,
    "Amravati": 28.89,
    "Aurangabad": 37.01,
    "Beed": 25.86,
    "Bhandara": 12.00,
    "Buldhana": 26.59,
    "Chandrapur": 22.04,
    "Dhule": 20.50,
    "Gadchiroli": 10.72,
    "Gondia": 13.22,
    "Hingoli": 13.00,
    "Jalgaon": 42.24,
    "Jalna": 19.59,
    "Kolhapur": 38.76,
    "Latur": 24.55,
    "Mumbai City": 31.53,
    "Mumbai Suburban": 93.56,
    "Nagpur": 46.53,
    "Nanded": 36.25,
    "Nandurbar": 16.48,
    "Nashik": 61.07,
    "Osmanabad": 16.61,
    "Palghar": 29.90,
    "Parbhani": 18.36,
    "Pune": 94.26,
    "Raigad": 26.34,
    "Ratnagiri": 16.15,
    "Sangli": 28.22,
    "Satara": 30.03,
    "Sindhudurg": 8.49,
    "Solapur": 43.17,
    "Thane": 110.60,
    "Wardha": 13.00,
    "Washim": 13.32,
    "Yavatmal": 27.78,
}

# District health vulnerability index (composite, 0-1, higher = more vulnerable)
# Based on IMR, MMR, institutional delivery rates from NFHS-5 / Economic Survey
DISTRICT_VULNERABILITY_INDEX = {
    "Gadchiroli": 0.92,
    "Nandurbar": 0.90,
    "Osmanabad": 0.78,
    "Hingoli": 0.76,
    "Washim": 0.75,
    "Buldhana": 0.74,
    "Jalna": 0.73,
    "Parbhani": 0.72,
    "Beed": 0.71,
    "Nanded": 0.70,
    "Latur": 0.69,
    "Amravati": 0.68,
    "Yavatmal": 0.67,
    "Akola": 0.65,
    "Bhandara": 0.64,
    "Gondia": 0.63,
    "Wardha": 0.62,
    "Chandrapur": 0.61,
    "Dhule": 0.60,
    "Jalgaon": 0.59,
    "Aurangabad": 0.58,
    "Solapur": 0.57,
    "Ahmednagar": 0.55,
    "Nashik": 0.53,
    "Sangli": 0.50,
    "Satara": 0.48,
    "Kolhapur": 0.46,
    "Raigad": 0.45,
    "Ratnagiri": 0.44,
    "Sindhudurg": 0.42,
    "Palghar": 0.55,
    "Thane": 0.40,
    "Pune": 0.35,
    "Nagpur": 0.38,
    "Mumbai Suburban": 0.32,
    "Mumbai City": 0.30,
}
