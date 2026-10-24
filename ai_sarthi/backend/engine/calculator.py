"""
AI Sarthi — Financial Calculation Engine
Deterministic, mathematically validated financial analysis tools.
"""
import math
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


@dataclass
class BudgetSummary:
    district: str
    financial_year: str
    financial_stage: str
    total_amount_lakh: float
    record_count: int
    programmes: list[dict]
    source_documents: list[str]
    scope: str
    notes: str = ""


@dataclass
class AllocationScenario:
    scenario_name: str  # "low", "base", "high", "needs_based"
    total_budget_lakh: float
    district_allocations: dict[str, float]  # district_name -> amount_lakh
    methodology: str
    assumptions: list[str]
    per_capita_allocations: dict[str, float]  # district -> per-capita ₹
    district_shares_pct: dict[str, float]     # district -> % share
    label: str  # "ILLUSTRATIVE" or "HISTORICAL"


def get_statewide_total(
    db: Session,
    financial_year: str,
    financial_stage: str = "PROPOSED_PIP",
    pool: Optional[str] = None,
) -> dict:
    """
    Get validated statewide NHM budget total for a given year and stage.
    Only uses records with scope=STATEWIDE.
    """
    from database.models import FinancialRecord

    query = db.query(func.sum(FinancialRecord.amount_lakh)).filter(
        FinancialRecord.financial_year == financial_year,
        FinancialRecord.financial_stage == financial_stage,
        FinancialRecord.scope == "STATEWIDE",
        FinancialRecord.amount_lakh > 0,
    )
    if pool:
        query = query.filter(FinancialRecord.pool == pool)

    total = query.scalar() or 0.0

    # Get record count and sources
    count_query = db.query(func.count(FinancialRecord.id)).filter(
        FinancialRecord.financial_year == financial_year,
        FinancialRecord.financial_stage == financial_stage,
        FinancialRecord.scope == "STATEWIDE",
    )
    count = count_query.scalar() or 0

    return {
        "financial_year": financial_year,
        "financial_stage": financial_stage,
        "total_amount_lakh": round(total, 4),
        "total_amount_crore": round(total / 100, 4),
        "record_count": count,
        "scope": "STATEWIDE",
        "pool_filter": pool,
        "note": "Statewide NHM proposed PIP budget, not individual district allocation",
    }


def get_programme_breakdown(
    db: Session,
    financial_year: str,
    financial_stage: str = "PROPOSED_PIP",
    scope: str = "STATEWIDE",
) -> list[dict]:
    """
    Get programme-wise budget breakdown for a year.
    Returns sorted list with amounts and percentage shares.
    """
    from database.models import FinancialRecord

    results = db.query(
        FinancialRecord.programme,
        FinancialRecord.pool,
        func.sum(FinancialRecord.amount_lakh).label("total_lakh"),
        func.count(FinancialRecord.id).label("count"),
    ).filter(
        FinancialRecord.financial_year == financial_year,
        FinancialRecord.financial_stage == financial_stage,
        FinancialRecord.scope == scope,
        FinancialRecord.amount_lakh > 0,
    ).group_by(
        FinancialRecord.programme, FinancialRecord.pool
    ).order_by(func.sum(FinancialRecord.amount_lakh).desc()).all()

    if not results:
        return []

    grand_total = sum(r.total_lakh for r in results)

    breakdown = []
    for r in results:
        amount = round(r.total_lakh, 4)
        pct = round(100 * amount / grand_total, 2) if grand_total > 0 else 0.0
        breakdown.append({
            "programme": r.programme or "Unknown",
            "pool": r.pool,
            "amount_lakh": amount,
            "amount_crore": round(amount / 100, 4),
            "share_pct": pct,
            "record_count": r.count,
        })

    return breakdown


def compute_year_over_year_growth(
    db: Session,
    financial_year1: str,
    financial_year2: str,
    financial_stage: str = "PROPOSED_PIP",
    scope: str = "STATEWIDE",
) -> dict:
    """
    Compute year-over-year growth between two comparable fiscal years.
    Only valid when financial_stage and scope match.
    """
    from database.models import FinancialRecord

    def get_total(year):
        total = db.query(func.sum(FinancialRecord.amount_lakh)).filter(
            FinancialRecord.financial_year == year,
            FinancialRecord.financial_stage == financial_stage,
            FinancialRecord.scope == scope,
            FinancialRecord.amount_lakh > 0,
        ).scalar() or 0.0
        return total

    total1 = get_total(financial_year1)
    total2 = get_total(financial_year2)

    if total1 <= 0:
        return {
            "error": f"No data for {financial_year1} with stage={financial_stage}",
            "year1": financial_year1,
            "year2": financial_year2,
        }

    growth_abs = total2 - total1
    growth_pct = round(100 * growth_abs / total1, 2)

    return {
        "year1": financial_year1,
        "year2": financial_year2,
        "financial_stage": financial_stage,
        "scope": scope,
        "amount_year1_lakh": round(total1, 4),
        "amount_year2_lakh": round(total2, 4),
        "growth_lakh": round(growth_abs, 4),
        "growth_pct": growth_pct,
        "direction": "increase" if growth_abs > 0 else "decrease" if growth_abs < 0 else "no_change",
        "comparable": True,
        "note": f"Comparison uses {financial_stage} stage only. Stages must match for valid comparison.",
    }


def get_top_programmes(
    db: Session,
    financial_year: str,
    n: int = 10,
    financial_stage: str = "PROPOSED_PIP",
) -> list[dict]:
    """Return top N programmes by budget allocation."""
    from database.models import FinancialRecord

    results = db.query(
        FinancialRecord.programme,
        func.sum(FinancialRecord.amount_lakh).label("total"),
    ).filter(
        FinancialRecord.financial_year == financial_year,
        FinancialRecord.financial_stage == financial_stage,
        FinancialRecord.scope == "STATEWIDE",
        FinancialRecord.amount_lakh > 0,
    ).group_by(FinancialRecord.programme).order_by(
        func.sum(FinancialRecord.amount_lakh).desc()
    ).limit(n).all()

    grand = db.query(func.sum(FinancialRecord.amount_lakh)).filter(
        FinancialRecord.financial_year == financial_year,
        FinancialRecord.financial_stage == financial_stage,
        FinancialRecord.scope == "STATEWIDE",
    ).scalar() or 1.0

    return [
        {
            "rank": i + 1,
            "programme": r.programme or "Unknown",
            "amount_lakh": round(r.total, 4),
            "amount_crore": round(r.total / 100, 4),
            "share_pct": round(100 * r.total / grand, 2),
        }
        for i, r in enumerate(results)
    ]


def calculate_needs_based_allocation(
    total_budget_lakh: float,
    districts: list[str],
    population_weights: dict[str, float],
    vulnerability_weights: dict[str, float],
    pop_weight: float = 0.4,
    vuln_weight: float = 0.6,
) -> AllocationScenario:
    """
    Calculate needs-based district allocation using composite weights.

    Formula: district_share = w_pop * (pop_i / total_pop) + w_vuln * (vuln_i / total_vuln)
    where vuln_i = vulnerability_index for district i.

    Args:
        total_budget_lakh: Total budget envelope in ₹ lakh
        districts: List of district names
        population_weights: {district: population_lakh}
        vulnerability_weights: {district: vulnerability_index (0-1)}
        pop_weight: Weight for population factor (default 0.4)
        vuln_weight: Weight for vulnerability factor (default 0.6)

    Returns:
        AllocationScenario with justified allocations
    """
    if abs(pop_weight + vuln_weight - 1.0) > 0.01:
        raise ValueError(f"Weights must sum to 1.0, got {pop_weight + vuln_weight}")

    if total_budget_lakh <= 0:
        raise ValueError("Total budget must be positive")

    # Filter to requested districts
    valid_districts = [d for d in districts if d in population_weights and d in vulnerability_weights]
    if not valid_districts:
        raise ValueError("No valid districts with population and vulnerability data")

    # Compute raw scores
    total_pop = sum(population_weights[d] for d in valid_districts)
    total_vuln = sum(vulnerability_weights[d] for d in valid_districts)

    if total_pop <= 0 or total_vuln <= 0:
        raise ValueError("Population and vulnerability totals must be positive")

    # Composite score per district
    composite_scores = {}
    for d in valid_districts:
        pop_share = population_weights[d] / total_pop
        vuln_share = vulnerability_weights[d] / total_vuln
        composite_scores[d] = pop_weight * pop_share + vuln_weight * vuln_share

    # Normalize to sum = 1
    total_score = sum(composite_scores.values())
    normalized = {d: s / total_score for d, s in composite_scores.items()}

    # Calculate allocations
    allocations = {}
    per_capita = {}
    for d in valid_districts:
        alloc_lakh = round(normalized[d] * total_budget_lakh, 2)
        allocations[d] = alloc_lakh
        pop = population_weights[d]
        per_capita[d] = round((alloc_lakh * 100000) / (pop * 100000), 2)  # ₹ per person

    # Shares
    shares = {d: round(100 * allocations[d] / total_budget_lakh, 2) for d in valid_districts}

    # Verify budget adds up and reconcile residual rounding error on largest district
    total_allocated = sum(allocations.values())
    residual_lakh = round(total_budget_lakh - total_allocated, 2)
    if residual_lakh != 0 and valid_districts:
        largest_d = max(allocations.keys(), key=lambda d: allocations[d])
        allocations[largest_d] = round(allocations[largest_d] + residual_lakh, 2)
        shares[largest_d] = round(100 * allocations[largest_d] / total_budget_lakh, 2)

    total_allocated = sum(allocations.values())

    return AllocationScenario(
        scenario_name="needs_based",
        total_budget_lakh=total_budget_lakh,
        district_allocations=allocations,
        methodology=(
            f"Needs-based allocation using composite score: "
            f"{pop_weight*100:.0f}% population weight + {vuln_weight*100:.0f}% vulnerability weight. "
            f"District share = w_pop × (pop_i/Σpop) + w_vuln × (vuln_i/Σvuln)"
        ),
        assumptions=[
            f"Total budget envelope: ₹{total_budget_lakh:,.2f} lakh",
            f"Population weight: {pop_weight*100:.0f}%",
            f"Vulnerability weight: {vuln_weight*100:.0f}%",
            f"Population data: District estimates (lakh)",
            f"Vulnerability index: Composite health indicator (0-1)",
            f"Districts included: {len(valid_districts)}",
            "THIS IS AN ILLUSTRATIVE PLANNING SCENARIO, NOT AN OFFICIAL GOVERNMENT ALLOCATION",
        ],
        per_capita_allocations=per_capita,
        district_shares_pct=shares,
        label="ILLUSTRATIVE",
    )


def generate_budget_scenarios(
    total_budget_lakh: float,
    districts: list[str],
    population_weights: dict[str, float],
    vulnerability_weights: dict[str, float],
) -> dict[str, AllocationScenario]:
    """
    Generate Low/Base/High budget scenarios.
    - Low: 85% of budget, equal weights
    - Base: 100% budget, needs-based (pop=40%, vuln=60%)
    - High: 115% budget, vulnerability-heavy (pop=25%, vuln=75%)
    """
    scenarios = {}

    # Low scenario: 85% budget, population-heavy
    scenarios["low"] = calculate_needs_based_allocation(
        total_budget_lakh=total_budget_lakh * 0.85,
        districts=districts,
        population_weights=population_weights,
        vulnerability_weights=vulnerability_weights,
        pop_weight=0.6,
        vuln_weight=0.4,
    )
    scenarios["low"].scenario_name = "low"

    # Base scenario: full budget, balanced
    scenarios["base"] = calculate_needs_based_allocation(
        total_budget_lakh=total_budget_lakh,
        districts=districts,
        population_weights=population_weights,
        vulnerability_weights=vulnerability_weights,
        pop_weight=0.4,
        vuln_weight=0.6,
    )

    # High scenario: 115% budget, vulnerability-heavy
    scenarios["high"] = calculate_needs_based_allocation(
        total_budget_lakh=total_budget_lakh * 1.15,
        districts=districts,
        population_weights=population_weights,
        vulnerability_weights=vulnerability_weights,
        pop_weight=0.25,
        vuln_weight=0.75,
    )
    scenarios["high"].scenario_name = "high"

    return scenarios


def format_inr(amount_lakh: float, precision: int = 2) -> str:
    """Format ₹ amount in lakh/crore with appropriate unit."""
    if amount_lakh >= 100:
        crore = amount_lakh / 100
        return f"₹{crore:,.{precision}f} crore (₹{amount_lakh:,.{precision}f} lakh)"
    return f"₹{amount_lakh:,.{precision}f} lakh"


def sensitivity_analysis(
    base_allocation: dict[str, float],
    parameter: str,
    range_pct: float = 20.0,
) -> dict:
    """
    Simple sensitivity analysis: how allocation changes when
    total budget varies by ±range_pct%.
    """
    multipliers = [
        (f"-{range_pct:.0f}%", (100 - range_pct) / 100),
        ("-10%", 0.9),
        ("Base", 1.0),
        ("+10%", 1.1),
        (f"+{range_pct:.0f}%", (100 + range_pct) / 100),
    ]

    result = {}
    for label, mult in multipliers:
        result[label] = {
            d: round(amt * mult, 2)
            for d, amt in base_allocation.items()
        }

    return {
        "parameter": parameter,
        "range_pct": range_pct,
        "scenarios": result,
        "note": "Linear sensitivity; actual allocation may use non-linear needs weighting",
    }
