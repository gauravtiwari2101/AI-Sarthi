"""Districts Router"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import get_db, District, FinancialRecord
from constants import MAHARASHTRA_DISTRICTS, DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX

router = APIRouter()


@router.get("")
def list_districts(db: Session = Depends(get_db)):
    """List all 36 Maharashtra districts with basic info."""
    districts = db.query(District).order_by(District.name).all()
    return {
        "total": len(districts),
        "districts": [d.to_dict() for d in districts],
    }


@router.get("/{district_id}/profile")
def district_profile(district_id: int, db: Session = Depends(get_db)):
    """Get full profile for a district."""
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(404, f"District with id {district_id} not found")

    # Budget summary
    budget_years = db.query(
        FinancialRecord.financial_year,
        FinancialRecord.financial_stage,
        func.sum(FinancialRecord.amount_lakh).label("total"),
        func.count(FinancialRecord.id).label("count"),
    ).filter(
        FinancialRecord.district_id == district_id,
        FinancialRecord.amount_lakh > 0,
    ).group_by(
        FinancialRecord.financial_year, FinancialRecord.financial_stage
    ).order_by(FinancialRecord.financial_year).all()

    profile = district.to_dict()
    profile["budget_history"] = [
        {
            "financial_year": r.financial_year,
            "financial_stage": r.financial_stage,
            "total_lakh": round(r.total, 2),
            "total_crore": round(r.total / 100, 4),
            "record_count": r.count,
        }
        for r in budget_years
    ]
    profile["data_coverage"] = {
        "has_district_records": len(budget_years) > 0,
        "available_years": list(set(r.financial_year for r in budget_years)),
        "note": (
            "District-specific budget records available" if budget_years
            else "No district-specific budget records in current dataset. Statewide NHM data available via /api/budgets."
        ),
    }

    return profile


@router.get("/{district_id}/budget")
def district_budget(
    district_id: int,
    year: str = Query(None, description="Fiscal year e.g. 2022-23"),
    stage: str = Query(None, description="Financial stage: PROPOSED_PIP, APPROVED_ROP"),
    db: Session = Depends(get_db),
):
    """Get budget records for a district."""
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(404, f"District {district_id} not found")

    query = db.query(FinancialRecord).filter(
        FinancialRecord.district_id == district_id,
        FinancialRecord.amount_lakh > 0,
    )
    if year:
        query = query.filter(FinancialRecord.financial_year == year)
    if stage:
        query = query.filter(FinancialRecord.financial_stage == stage)

    records = query.order_by(FinancialRecord.financial_year, FinancialRecord.programme).all()

    return {
        "district": district.to_dict(),
        "filters": {"year": year, "stage": stage},
        "record_count": len(records),
        "records": [r.to_dict() for r in records],
        "note": (
            "These are district-specific financial records. "
            "Statewide NHM data can be queried via /api/budgets/statewide."
        ) if records else (
            "No district-specific budget records found. "
            "The current dataset contains statewide NHM PIP proposals. "
            "District-wise breakdown requires the original ROP district sheets."
        ),
    }


@router.get("/search/{name}")
def search_district(name: str, db: Session = Depends(get_db)):
    """Search district by name or alias."""
    from constants import normalize_district_name
    canonical = normalize_district_name(name)
    if not canonical:
        # Try partial match
        results = db.query(District).filter(
            District.name.ilike(f"%{name}%")
        ).all()
        if not results:
            raise HTTPException(404, f"District '{name}' not found")
        return {"matches": [d.to_dict() for d in results]}

    district = db.query(District).filter(District.name == canonical).first()
    if not district:
        raise HTTPException(404, f"District '{canonical}' not found")
    return district.to_dict()
