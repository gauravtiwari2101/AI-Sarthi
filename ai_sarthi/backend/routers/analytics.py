"""Analytics Router"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from database.models import get_db, FinancialRecord
from engine.calculator import (
    get_statewide_total, get_programme_breakdown,
    compute_year_over_year_growth, get_top_programmes,
)
from constants import FISCAL_YEARS, MAHARASHTRA_DISTRICTS

router = APIRouter()


@router.get("/trends")
def historical_trends(
    stage: str = Query("PROPOSED_PIP"),
    db: Session = Depends(get_db),
):
    """Get historical budget trends across all available years."""
    trend_data = []
    for yr in FISCAL_YEARS:
        total = get_statewide_total(db, yr, stage)
        if total["total_amount_lakh"] > 0:
            trend_data.append({
                "year": yr,
                "total_lakh": total["total_amount_lakh"],
                "total_crore": total["total_amount_crore"],
                "record_count": total["record_count"],
            })

    # Compute growth rates
    for i in range(1, len(trend_data)):
        prev = trend_data[i-1]["total_lakh"]
        curr = trend_data[i]["total_lakh"]
        if prev > 0:
            trend_data[i]["growth_pct"] = round(100 * (curr - prev) / prev, 2)
        else:
            trend_data[i]["growth_pct"] = None

    return {
        "stage": stage,
        "years": trend_data,
        "note": "Statewide NHM proposed budget trends. Compare only within same stage.",
    }


@router.get("/programmes/summary")
def programme_summary(
    stage: str = Query("PROPOSED_PIP"),
    db: Session = Depends(get_db),
):
    """Multi-year programme budget summary."""
    summary = {}
    for yr in FISCAL_YEARS:
        breakdown = get_programme_breakdown(db, yr, stage)
        if breakdown:
            summary[yr] = {p["programme"]: p["amount_lakh"] for p in breakdown}

    # Compute aggregate
    all_programmes = set()
    for yr_data in summary.values():
        all_programmes.update(yr_data.keys())

    programme_trends = {}
    for prog in all_programmes:
        if prog:
            programme_trends[prog] = {
                yr: summary.get(yr, {}).get(prog, 0)
                for yr in FISCAL_YEARS
                if yr in summary
            }

    # Sort by average allocation
    sorted_programmes = sorted(
        programme_trends.items(),
        key=lambda x: sum(x[1].values()) / max(len(x[1]), 1),
        reverse=True,
    )

    return {
        "stage": stage,
        "programmes": dict(sorted_programmes[:20]),
        "available_years": list(summary.keys()),
        "note": "Statewide NHM proposed budget by programme.",
    }


@router.get("/districts/overview")
def districts_overview(db: Session = Depends(get_db)):
    """Overview of all 36 districts with available data indicator."""
    from database.models import District

    districts = db.query(District).order_by(District.name).all()
    result = []
    for d in districts:
        rec_count = db.query(func.count(FinancialRecord.id)).filter(
            FinancialRecord.district_id == d.id
        ).scalar() or 0

        result.append({
            **d.to_dict(),
            "record_count": rec_count,
            "has_budget_data": rec_count > 0,
            "data_note": (
                "Budget records available" if rec_count > 0
                else "No district-specific records (statewide NHM data only)"
            ),
        })

    return {
        "total_districts": len(result),
        "districts_with_data": sum(1 for d in result if d["has_budget_data"]),
        "districts": result,
    }
