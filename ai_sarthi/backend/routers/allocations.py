"""Allocations Router"""
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from engine.calculator import (
    calculate_needs_based_allocation,
    generate_budget_scenarios,
    sensitivity_analysis,
    format_inr,
)
from constants import (
    MAHARASHTRA_DISTRICTS, DISTRICT_POPULATION_LAKH,
    DISTRICT_VULNERABILITY_INDEX,
)

router = APIRouter()


class AllocationRequest(BaseModel):
    total_budget_crore: float = Field(..., gt=0, description="Total budget in ₹ crore")
    districts: Optional[List[str]] = Field(None, description="Districts to include (all 36 if None)")
    population_weight: float = Field(0.4, ge=0.0, le=1.0)
    vulnerability_weight: float = Field(0.6, ge=0.0, le=1.0)
    generate_scenarios: bool = True


class OptimizationRequest(BaseModel):
    total_budget_crore: float = Field(..., gt=0)
    priority_districts: Optional[List[str]] = Field(None)
    priority_boost: float = Field(1.3, ge=1.0, le=2.0, description="Boost factor for priority districts")


@router.post("/recommend")
def recommend_allocation(request: AllocationRequest):
    """
    Generate needs-based allocation recommendation.
    ALWAYS labeled as ILLUSTRATIVE — not official.
    """
    if abs(request.population_weight + request.vulnerability_weight - 1.0) > 0.05:
        raise HTTPException(400, "population_weight + vulnerability_weight must equal 1.0")

    districts = request.districts
    if not districts:
        districts = [d["name"] for d in MAHARASHTRA_DISTRICTS]

    # Validate districts
    valid = [d for d in districts if d in DISTRICT_POPULATION_LAKH]
    invalid = [d for d in districts if d not in DISTRICT_POPULATION_LAKH]

    total_lakh = request.total_budget_crore * 100

    try:
        scenario = calculate_needs_based_allocation(
            total_budget_lakh=total_lakh,
            districts=valid,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
            pop_weight=request.population_weight,
            vuln_weight=request.vulnerability_weight,
        )

        # Sort allocations by amount
        sorted_allocations = dict(
            sorted(scenario.district_allocations.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "label": "ILLUSTRATIVE_SCENARIO",
            "disclaimer": "⚠️ This is an illustrative planning scenario based on population and health vulnerability indicators. IT IS NOT AN OFFICIAL GOVERNMENT ALLOCATION.",
            "scenario": scenario.scenario_name,
            "total_budget_crore": request.total_budget_crore,
            "total_budget_lakh": total_lakh,
            "methodology": scenario.methodology,
            "assumptions": scenario.assumptions,
            "districts_included": len(valid),
            "districts_excluded": invalid,
            "allocations_lakh": sorted_allocations,
            "allocations_crore": {d: round(v/100, 4) for d, v in sorted_allocations.items()},
            "per_capita_rupees": scenario.per_capita_allocations,
            "shares_pct": scenario.district_shares_pct,
        }
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/scenarios")
def budget_scenarios(request: AllocationRequest):
    """Generate Low/Base/High allocation scenarios."""
    districts = request.districts or [d["name"] for d in MAHARASHTRA_DISTRICTS]
    valid = [d for d in districts if d in DISTRICT_POPULATION_LAKH]
    total_lakh = request.total_budget_crore * 100

    try:
        scenarios = generate_budget_scenarios(
            total_budget_lakh=total_lakh,
            districts=valid,
            population_weights=DISTRICT_POPULATION_LAKH,
            vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
        )

        result = {}
        # Predefined policy scenario configs
        configs = {
            "needs_priority": (0.4, 0.6, 1.0, "Needs-Priority Model (60% Need / 40% Population)"),
            "balanced": (0.5, 0.5, 1.0, "Balanced Equity Model (50% Need / 50% Population)"),
            "population_centric": (0.7, 0.3, 1.0, "Per-Capita Model (30% Need / 70% Population)"),
            "base": (0.4, 0.6, 1.0, "Base Allocation (100% Budget, 60% Need / 40% Pop)"),
            "low": (0.6, 0.4, 0.85, "Conservative Fiscal Scenario (85% Budget Envelope)"),
            "high": (0.25, 0.75, 1.15, "Accelerated Equity Scenario (115% Budget Envelope)"),
        }

        for sc_name, (pw, vw, mult, desc) in configs.items():
            sc_obj = calculate_needs_based_allocation(
                total_budget_lakh=total_lakh * mult,
                districts=valid,
                population_weights=DISTRICT_POPULATION_LAKH,
                vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
                pop_weight=pw,
                vuln_weight=vw,
            )
            sorted_alloc = dict(
                sorted(sc_obj.district_allocations.items(), key=lambda x: x[1], reverse=True)
            )
            result[sc_name] = {
                "total_budget_lakh": sc_obj.total_budget_lakh,
                "total_budget_crore": round(sc_obj.total_budget_lakh / 100, 2),
                "methodology": sc_obj.methodology,
                "description": desc,
                "top_10_allocations_lakh": dict(list(sorted_alloc.items())[:10]),
                "all_allocations_lakh": sorted_alloc,
                "allocations_crore": {d: round(v / 100, 2) for d, v in sorted_alloc.items()},
                "shares_pct": sc_obj.district_shares_pct,
                "per_capita_rupees": sc_obj.per_capita_allocations,
            }

        return {
            "label": "ILLUSTRATIVE_SCENARIOS",
            "disclaimer": "⚠️ All scenarios are illustrative planning exercises only. Not official government allocations.",
            "base_budget_crore": request.total_budget_crore,
            "scenarios": result,
            "assumptions": [
                "Needs-Priority: 100% budget, 60% vulnerability, 40% population",
                "Balanced: 100% budget, 50% vulnerability, 50% population",
                "Per-Capita: 100% budget, 30% vulnerability, 70% population",
                "Low: 85% budget, 40% vulnerability, 60% population",
                "High: 115% budget, 75% vulnerability, 25% population",
            ],
        }
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/sensitivity")
def allocation_sensitivity(
    base_budget_crore: float,
    district: str,
):
    """Sensitivity analysis for a district's allocation."""
    districts = [d["name"] for d in MAHARASHTRA_DISTRICTS]
    valid = [d for d in districts if d in DISTRICT_POPULATION_LAKH]

    if district not in DISTRICT_POPULATION_LAKH:
        raise HTTPException(404, f"District '{district}' not found")

    total_lakh = base_budget_crore * 100
    scenario = calculate_needs_based_allocation(
        total_budget_lakh=total_lakh,
        districts=valid,
        population_weights=DISTRICT_POPULATION_LAKH,
        vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
    )

    sens = sensitivity_analysis(
        base_allocation=scenario.district_allocations,
        parameter="total_budget",
        range_pct=20.0,
    )

    # Filter to requested district
    district_sens = {
        label: allocations.get(district, 0)
        for label, allocations in sens["scenarios"].items()
    }

    return {
        "district": district,
        "base_budget_crore": base_budget_crore,
        "base_allocation_lakh": scenario.district_allocations.get(district),
        "base_share_pct": scenario.district_shares_pct.get(district),
        "sensitivity_by_budget": district_sens,
        "note": "Illustrative sensitivity analysis. Linear scaling assumption.",
    }
