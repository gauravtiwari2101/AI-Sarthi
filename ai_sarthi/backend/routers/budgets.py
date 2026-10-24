"""Budgets Router"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from database.models import get_db, FinancialRecord, District
from engine.calculator import (
    get_statewide_total, get_programme_breakdown,
    compute_year_over_year_growth, get_top_programmes
)

router = APIRouter()


@router.get("/statewide")
def statewide_budget(
    year: str = Query(..., description="Fiscal year e.g. 2022-23"),
    stage: str = Query("PROPOSED_PIP", description="Financial stage"),
    pool: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get statewide NHM budget total for a year."""
    result = get_statewide_total(db, year, stage, pool)
    return result


@router.get("/programmes")
def programme_breakdown(
    year: str = Query(..., description="Fiscal year"),
    stage: str = Query("PROPOSED_PIP"),
    db: Session = Depends(get_db),
):
    """Get programme-wise budget breakdown."""
    breakdown = get_programme_breakdown(db, year, stage)
    if not breakdown:
        return {
            "year": year,
            "stage": stage,
            "programmes": [],
            "note": f"No data found for {year}/{stage}",
        }

    total = sum(p["amount_lakh"] for p in breakdown)
    return {
        "year": year,
        "stage": stage,
        "total_lakh": round(total, 2),
        "total_crore": round(total / 100, 4),
        "programme_count": len(breakdown),
        "programmes": breakdown,
    }


@router.get("/growth")
def year_on_year_growth(
    year1: str = Query(..., description="Earlier fiscal year e.g. 2022-23"),
    year2: str = Query(..., description="Later fiscal year e.g. 2023-24"),
    stage: str = Query("PROPOSED_PIP"),
    db: Session = Depends(get_db),
):
    """Compute year-over-year budget growth."""
    return compute_year_over_year_growth(db, year1, year2, stage)


@router.get("/top-programmes")
def top_programmes(
    year: str = Query(...),
    n: int = Query(10, ge=1, le=50),
    stage: str = Query("PROPOSED_PIP"),
    db: Session = Depends(get_db),
):
    """Get top N programmes by budget."""
    return {
        "year": year,
        "stage": stage,
        "top_n": n,
        "programmes": get_top_programmes(db, year, n, stage),
    }


@router.get("/compare")
def compare_years(
    years: str = Query(..., description="Comma-separated years e.g. 2022-23,2023-24"),
    stage: str = Query("PROPOSED_PIP"),
    db: Session = Depends(get_db),
):
    """Compare budgets across multiple years."""
    year_list = [y.strip() for y in years.split(",")]
    results = {}
    for yr in year_list:
        results[yr] = get_statewide_total(db, yr, stage)

    # Compute growth rates
    growths = []
    for i in range(len(year_list) - 1):
        g = compute_year_over_year_growth(db, year_list[i], year_list[i+1], stage)
        growths.append(g)

    return {
        "years": year_list,
        "stage": stage,
        "annual_totals": results,
        "growth_rates": growths,
        "note": f"All figures are {stage} stage. Compare only compatible stages.",
    }


@router.get("/available-years")
def available_years(db: Session = Depends(get_db)):
    """Get list of available fiscal years in the database."""
    years = db.query(distinct(FinancialRecord.financial_year)).filter(
        FinancialRecord.financial_year.isnot(None)
    ).order_by(FinancialRecord.financial_year).all()

    stages = db.query(distinct(FinancialRecord.financial_stage)).filter(
        FinancialRecord.financial_stage.isnot(None)
    ).all()

    return {
        "available_years": [y[0] for y in years],
        "available_stages": [s[0] for s in stages],
        "total_records": db.query(FinancialRecord).count(),
    }
