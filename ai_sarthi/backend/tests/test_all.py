"""
AI Sarthi — Backend Test Suite
Tests financial calculations, district lookups, API endpoints, and data quality.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient


# ==================== CONSTANTS & DISTRICT TESTS ====================

class TestDistricts:
    def test_all_36_districts_defined(self):
        from constants import MAHARASHTRA_DISTRICTS
        assert len(MAHARASHTRA_DISTRICTS) == 36, f"Expected 36 districts, got {len(MAHARASHTRA_DISTRICTS)}"

    def test_district_ids_unique(self):
        from constants import MAHARASHTRA_DISTRICTS
        ids = [d["id"] for d in MAHARASHTRA_DISTRICTS]
        assert len(ids) == len(set(ids)), "Duplicate district IDs found"

    def test_district_names_unique(self):
        from constants import MAHARASHTRA_DISTRICTS
        names = [d["name"] for d in MAHARASHTRA_DISTRICTS]
        assert len(names) == len(set(names)), "Duplicate district names"

    def test_alias_normalization_aurangabad(self):
        from constants import normalize_district_name
        assert normalize_district_name("Aurangabad") == "Aurangabad"
        assert normalize_district_name("Chhatrapati Sambhajinagar") == "Aurangabad"
        assert normalize_district_name("Sambhajinagar") == "Aurangabad"

    def test_alias_normalization_osmanabad(self):
        from constants import normalize_district_name
        assert normalize_district_name("Osmanabad") == "Osmanabad"
        assert normalize_district_name("Dharashiv") == "Osmanabad"

    def test_alias_normalization_ahmednagar(self):
        from constants import normalize_district_name
        result = normalize_district_name("Ahilyanagar")
        assert result == "Ahmednagar", f"Expected Ahmednagar, got {result}"

    def test_alias_normalization_case_insensitive(self):
        from constants import normalize_district_name
        assert normalize_district_name("PUNE") == "Pune"
        assert normalize_district_name("pune") == "Pune"
        assert normalize_district_name("NASHIK") == "Nashik"

    def test_unknown_district_returns_none(self):
        from constants import normalize_district_name
        assert normalize_district_name("NonExistentDistrict") is None
        assert normalize_district_name("") is None
        assert normalize_district_name(None) is None

    def test_all_districts_have_population(self):
        from constants import MAHARASHTRA_DISTRICTS, DISTRICT_POPULATION_LAKH
        missing = [d["name"] for d in MAHARASHTRA_DISTRICTS if d["name"] not in DISTRICT_POPULATION_LAKH]
        assert not missing, f"Missing population for: {missing}"

    def test_all_districts_have_vulnerability_index(self):
        from constants import MAHARASHTRA_DISTRICTS, DISTRICT_VULNERABILITY_INDEX
        missing = [d["name"] for d in MAHARASHTRA_DISTRICTS if d["name"] not in DISTRICT_VULNERABILITY_INDEX]
        assert not missing, f"Missing vulnerability index for: {missing}"

    def test_vulnerability_index_range(self):
        from constants import DISTRICT_VULNERABILITY_INDEX
        for district, idx in DISTRICT_VULNERABILITY_INDEX.items():
            assert 0.0 <= idx <= 1.0, f"{district}: vulnerability {idx} out of [0,1] range"

    def test_population_positive(self):
        from constants import DISTRICT_POPULATION_LAKH
        for district, pop in DISTRICT_POPULATION_LAKH.items():
            assert pop > 0, f"{district}: population {pop} must be positive"

    def test_specific_known_districts(self):
        from constants import normalize_district_name
        known = [
            "Nagpur", "Pune", "Mumbai City", "Mumbai Suburban", "Nashik",
            "Nanded", "Gadchiroli", "Sindhudurg", "Thane", "Solapur",
        ]
        for d in known:
            assert normalize_district_name(d) == d, f"Failed for {d}"


# ==================== FINANCIAL CALCULATION TESTS ====================

class TestCalculations:
    def test_needs_based_allocation_sums_to_total(self):
        from engine.calculator import calculate_needs_based_allocation
        from constants import MAHARASHTRA_DISTRICTS, DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX

        districts = [d["name"] for d in MAHARASHTRA_DISTRICTS]
        total = 10000.0  # ₹100 crore

        scenario = calculate_needs_based_allocation(
            total_budget_lakh=total,
            districts=districts,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
        )

        allocated = sum(scenario.district_allocations.values())
        assert abs(allocated - total) < 1.0, f"Allocation sum {allocated:.2f} ≠ total {total:.2f}"

    def test_needs_based_shares_sum_to_100(self):
        from engine.calculator import calculate_needs_based_allocation
        from constants import MAHARASHTRA_DISTRICTS, DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX

        districts = [d["name"] for d in MAHARASHTRA_DISTRICTS]
        scenario = calculate_needs_based_allocation(
            total_budget_lakh=50000.0,
            districts=districts,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
        )
        total_pct = sum(scenario.district_shares_pct.values())
        assert abs(total_pct - 100.0) < 0.5, f"Shares sum to {total_pct:.2f}%, expected ~100%"

    def test_high_vulnerability_gets_more_with_vuln_weight(self):
        from engine.calculator import calculate_needs_based_allocation
        from constants import DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX

        districts = ["Gadchiroli", "Pune"]  # High vs low vulnerability

        scenario = calculate_needs_based_allocation(
            total_budget_lakh=1000.0,
            districts=districts,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
            pop_weight=0.0,  # Pure vulnerability weighting
            vuln_weight=1.0,
        )
        # Gadchiroli (vuln=0.92) should get more than Pune (vuln=0.35)
        assert scenario.district_allocations["Gadchiroli"] > scenario.district_allocations["Pune"], \
            "Higher vulnerability district should get more with vuln-only weighting"

    def test_equal_weights_proportional_to_population(self):
        from engine.calculator import calculate_needs_based_allocation
        from constants import DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX

        districts = ["Thane", "Sindhudurg"]  # Very different populations
        scenario = calculate_needs_based_allocation(
            total_budget_lakh=1000.0,
            districts=districts,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights={"Thane": 0.5, "Sindhudurg": 0.5},  # Equal vulnerability
            pop_weight=1.0,
            vuln_weight=0.0,
        )
        # Thane (110 lakh) should get far more than Sindhudurg (8.5 lakh) with pop-only
        assert scenario.district_allocations["Thane"] > scenario.district_allocations["Sindhudurg"] * 5

    def test_allocation_scenario_label(self):
        from engine.calculator import calculate_needs_based_allocation
        from constants import DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX
        districts = ["Pune", "Nagpur"]
        scenario = calculate_needs_based_allocation(
            total_budget_lakh=1000.0,
            districts=districts,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
        )
        assert scenario.label == "ILLUSTRATIVE"

    def test_invalid_weight_raises(self):
        from engine.calculator import calculate_needs_based_allocation
        from constants import DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX
        with pytest.raises(ValueError):
            calculate_needs_based_allocation(
                total_budget_lakh=1000.0,
                districts=["Pune"],
                population_weights=DISTRICT_POPULATION_LAKH,
                vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
                pop_weight=0.7,
                vuln_weight=0.7,  # Sums to 1.4 — invalid
            )

    def test_negative_budget_raises(self):
        from engine.calculator import calculate_needs_based_allocation
        from constants import DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX
        with pytest.raises(ValueError):
            calculate_needs_based_allocation(
                total_budget_lakh=-100.0,
                districts=["Pune"],
                population_weights=DISTRICT_POPULATION_LAKH,
                vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
            )

    def test_scenario_generation(self):
        from engine.calculator import generate_budget_scenarios
        from constants import MAHARASHTRA_DISTRICTS, DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX

        districts = [d["name"] for d in MAHARASHTRA_DISTRICTS]
        scenarios = generate_budget_scenarios(
            total_budget_lakh=10000.0,
            districts=districts,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
        )
        assert "low" in scenarios
        assert "base" in scenarios
        assert "high" in scenarios
        assert scenarios["low"].total_budget_lakh < scenarios["base"].total_budget_lakh
        assert scenarios["base"].total_budget_lakh < scenarios["high"].total_budget_lakh

    def test_format_inr_crore(self):
        from engine.calculator import format_inr
        result = format_inr(15000.0)
        assert "crore" in result.lower()
        assert "150" in result

    def test_format_inr_lakh(self):
        from engine.calculator import format_inr
        result = format_inr(50.0)
        assert "lakh" in result.lower()


# ==================== DATABASE TESTS ====================

class TestDatabase:
    def test_create_tables(self):
        from database.models import create_tables, engine
        from sqlalchemy import inspect
        create_tables()
        insp = inspect(engine)
        tables = insp.get_table_names()
        assert "districts" in tables
        assert "financial_records" in tables
        assert "data_quality_log" in tables

    def test_seed_districts(self):
        from database.models import create_tables, get_session, District
        from etl.ingest import seed_districts
        create_tables()
        with get_session() as sess:
            seed_districts(sess)
            count = sess.query(District).count()
        assert count == 36, f"Expected 36 districts, got {count}"

    def test_district_aliases_stored(self):
        from database.models import create_tables, get_session, District
        from etl.ingest import seed_districts
        create_tables()
        with get_session() as sess:
            seed_districts(sess)
            aurangabad = sess.query(District).filter(District.name == "Aurangabad").first()
            assert aurangabad is not None
            aliases = aurangabad.aliases
            assert "Chhatrapati Sambhajinagar" in aliases


# ==================== API TESTS ====================

@pytest.fixture(scope="module")
def client():
    """Create test client for FastAPI app."""
    from main import app
    from database.models import create_tables
    from etl.ingest import run_ingestion
    create_tables()
    # Seed minimal data for tests
    with TestClient(app) as c:
        yield c


class TestAPIEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "AI Sarthi"

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_districts_list(self, client):
        r = client.get("/api/districts")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 36
        names = [d["name"] for d in data["districts"]]
        assert "Nagpur" in names
        assert "Gadchiroli" in names
        assert "Mumbai City" in names

    def test_district_profile(self, client):
        r = client.get("/api/districts/1/profile")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Ahmednagar"

    def test_district_not_found(self, client):
        r = client.get("/api/districts/999/profile")
        assert r.status_code == 404

    def test_district_search_by_alias(self, client):
        r = client.get("/api/districts/search/Dharashiv")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Osmanabad"

    def test_available_years(self, client):
        r = client.get("/api/budgets/available-years")
        assert r.status_code == 200

    def test_data_quality_report(self, client):
        r = client.get("/api/reports/data-quality")
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        assert "known_limitations" in data

    def test_system_status(self, client):
        r = client.get("/api/system/status")
        assert r.status_code == 200
        data = r.json()
        assert "gpu" in data
        assert "slm" in data

    def test_allocation_recommend(self, client):
        r = client.post("/api/allocations/recommend", json={
            "total_budget_crore": 100.0,
            "population_weight": 0.4,
            "vulnerability_weight": 0.6,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["label"] == "ILLUSTRATIVE_SCENARIO"
        assert "disclaimer" in data
        assert "illustrative" in data["disclaimer"].lower()
        allocations = data["allocations_lakh"]
        assert len(allocations) == 36
        total = sum(allocations.values())
        assert abs(total - 10000.0) < 1.0

    def test_allocation_scenarios(self, client):
        r = client.post("/api/allocations/scenarios", json={
            "total_budget_crore": 500.0,
            "population_weight": 0.4,
            "vulnerability_weight": 0.6,
        })
        assert r.status_code == 200
        data = r.json()
        assert "scenarios" in data
        assert "low" in data["scenarios"]
        assert "base" in data["scenarios"]
        assert "high" in data["scenarios"]

    def test_chat_budget_query(self, client):
        r = client.post("/api/chat", json={
            "question": "What was Maharashtra's NHM budget in 2022-23?",
        })
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "model_mode" in data

    def test_chat_allocation_question(self, client):
        r = client.post("/api/chat", json={
            "question": "Recommend allocation of ₹100 crore across districts",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("disclaimer") is not None or data.get("calculations") is not None

    def test_sources_list(self, client):
        r = client.get("/api/reports/sources")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 5  # Known source documents


# ==================== FISCAL YEAR TESTS ====================

class TestFiscalYearParsing:
    def test_extract_fiscal_year(self):
        from routers.chat import extract_fiscal_year
        assert extract_fiscal_year("budget in 2022-23") == "2022-23"
        assert extract_fiscal_year("FY 2023-24 data") == "2023-24"
        assert extract_fiscal_year("year 2024") is not None
        assert extract_fiscal_year("no year here") is None

    def test_extract_district(self):
        from routers.chat import extract_district
        assert extract_district("budget for Nanded district") == "Nanded"
        assert extract_district("Dharashiv healthcare") == "Osmanabad"
        assert extract_district("how much for Gadchiroli") == "Gadchiroli"

    def test_extract_budget_amount_crore(self):
        from routers.chat import extract_budget_amount
        assert extract_budget_amount("allocate 100 crore") == 10000.0

    def test_extract_budget_amount_lakh(self):
        from routers.chat import extract_budget_amount
        assert extract_budget_amount("budget of 500 lakh") == 500.0

    def test_intent_classification(self):
        from routers.chat import classify_intent
        assert classify_intent("recommend allocation") == "allocation_recommendation"
        assert classify_intent("compare 2022-23 vs 2023-24") == "comparison"
        assert classify_intent("what is the trend") == "trend_analysis"
        assert classify_intent("how much budget") == "budget_query"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
