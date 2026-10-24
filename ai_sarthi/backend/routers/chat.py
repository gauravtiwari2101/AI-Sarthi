"""AI Chat Router - Main AI Sarthi Interface"""
import re
import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import get_db, FinancialRecord, District
from engine.calculator import (
    get_statewide_total, get_programme_breakdown,
    compute_year_over_year_growth, get_top_programmes,
    calculate_needs_based_allocation, format_inr,
)
from rag.retrieval import retrieve_evidence
from slm.inference import get_slm, build_analytical_response
from constants import (
    MAHARASHTRA_DISTRICTS, normalize_district_name,
    DISTRICT_POPULATION_LAKH, DISTRICT_VULNERABILITY_INDEX,
    FISCAL_YEARS,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    language: str = Field("en", description="en/hi/mixed")
    include_evidence: bool = True
    max_evidence: int = Field(5, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    key_metrics: list = []
    table_data: Optional[dict] = None
    chart_data: Optional[dict] = None
    sources: list = []
    warnings: list = []
    diagnostics: Optional[dict] = None
    suggested_followups: list = []
    disclaimer: Optional[str] = None
    model_mode: str = "deterministic"
    sql_data: Optional[dict] = None
    calculations: Optional[dict] = None
    evidence: list = []


FISCAL_YEAR_PATTERN = re.compile(r'20(\d\d)-(\d\d)')
CRORE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*crore', re.I)
LAKH_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*lakh', re.I)


def extract_fiscal_year(text: str) -> Optional[str]:
    """Extract fiscal year from question text."""
    m = FISCAL_YEAR_PATTERN.search(text)
    if m:
        return f"20{m.group(1)}-{m.group(2)}"
    # Year mentions like "2022", "2023"
    for yr in ["2025", "2024", "2023", "2022"]:
        if yr in text:
            return f"{yr}-{str(int(yr)+1)[2:]}"
    return None


def extract_district(text: str) -> Optional[str]:
    """Try to find a Maharashtra district name in the question."""
    text_lower = text.lower()
    # Try exact alias matching
    from constants import _alias_to_canonical
    best = None
    for alias, canonical in _alias_to_canonical.items():
        if alias in text_lower:
            if best is None or len(alias) > len(best[0]):
                best = (alias, canonical)
    return best[1] if best else None


def extract_budget_amount(text: str) -> Optional[float]:
    """Extract budget amount from question (in ₹ lakh)."""
    m = CRORE_PATTERN.search(text)
    if m:
        return float(m.group(1)) * 100  # Convert crore to lakh
    m = LAKH_PATTERN.search(text)
    if m:
        return float(m.group(1))
    return None


def classify_intent(question: str) -> str:
    """Classify user question intent."""
    q = question.lower()

    if any(w in q for w in ["allocat", "distribut", "recommend", "suggest", "next year", "future"]):
        return "allocation_recommendation"
    if any(w in q for w in ["compare", "vs", "versus", "difference between", "more than", "less than"]):
        return "comparison"
    if any(w in q for w in ["trend", "growth", "increas", "decreas", "over year", "historical"]):
        return "trend_analysis"
    if any(w in q for w in ["programme", "program", "scheme", "maternal", "child", "immunis", "asha"]):
        return "programme_analysis"
    if any(w in q for w in ["how much", "budget", "fund", "amount", "total", "spend"]):
        return "budget_query"
    if any(w in q for w in ["which district", "top", "best", "worst", "highest", "lowest"]):
        return "ranking_query"
    return "general"


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main AI Sarthi chat interface.
    Routes question to appropriate tools and generates evidence-backed response.
    """
    question = request.question.strip()
    logger.info(f"Chat question: {question[:100]}")

    # Extract entities
    district_name = extract_district(question)
    fiscal_year = extract_fiscal_year(question)
    budget_amount = extract_budget_amount(question)
    intent = classify_intent(question)

    logger.info(f"Intent: {intent}, District: {district_name}, Year: {fiscal_year}")

    sql_results = {}
    calculations = {}
    disclaimer = None

    # Route to appropriate tool
    if intent == "budget_query":
        if fiscal_year:
            sql_results = get_statewide_total(db, fiscal_year)
            if district_name:
                # Check if district has specific records
                d = db.query(District).filter(District.name == district_name).first()
                if d:
                    district_records = db.query(
                        func.sum(FinancialRecord.amount_lakh)
                    ).filter(
                        FinancialRecord.district_id == d.id,
                        FinancialRecord.financial_year == fiscal_year,
                    ).scalar()
                    sql_results["district"] = district_name
                    sql_results["district_specific_lakh"] = district_records
                    if not district_records:
                        sql_results["district_note"] = (
                            f"No district-specific budget record for {district_name} in {fiscal_year}. "
                            "The available data is statewide NHM proposed budgets."
                        )
        else:
            # Latest year
            fiscal_year = "2023-24"
            sql_results = get_statewide_total(db, fiscal_year)

    elif intent == "trend_analysis":
        years = FISCAL_YEARS
        trend = {}
        for yr in years:
            t = get_statewide_total(db, yr)
            if t["total_amount_lakh"] > 0:
                trend[yr] = t["total_amount_lakh"]
        calculations["trend_by_year"] = trend
        if district_name:
            calculations["note"] = f"Trend data shown is statewide NHM. District-level trend for {district_name} requires ROP district sheets."

    elif intent == "programme_analysis":
        yr = fiscal_year or "2022-23"
        breakdown = get_programme_breakdown(db, yr)
        sql_results = {"year": yr, "programme_breakdown": breakdown}

    elif intent == "allocation_recommendation":
        total_lakh = budget_amount or 50000.0  # Default 500 crore
        districts_list = [d["name"] for d in MAHARASHTRA_DISTRICTS]

        try:
            scenario = calculate_needs_based_allocation(
                total_budget_lakh=total_lakh,
                districts=districts_list,
                population_weights=DISTRICT_POPULATION_LAKH,
                vulnerability_weights=DISTRICT_VULNERABILITY_INDEX,
            )
            top_10 = sorted(
                scenario.district_allocations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            calculations = {
                "scenario": scenario.scenario_name,
                "total_budget_lakh": scenario.total_budget_lakh,
                "total_budget_crore": round(scenario.total_budget_lakh / 100, 2),
                "methodology": scenario.methodology,
                "top_10_allocations_lakh": dict(top_10),
            }
            if district_name and district_name in scenario.district_allocations:
                calculations["requested_district"] = district_name
                calculations["district_allocation_lakh"] = scenario.district_allocations[district_name]
                calculations["district_share_pct"] = scenario.district_shares_pct[district_name]

            disclaimer = "⚠️ ILLUSTRATIVE SCENARIO ONLY — Not an official government allocation. Based on population and health vulnerability indicators."

        except Exception as e:
            logger.error(f"Allocation error: {e}")
            calculations["error"] = str(e)

    elif intent == "comparison":
        # Year comparison
        yr1, yr2 = "2022-23", "2023-24"
        years_in_q = FISCAL_YEAR_PATTERN.findall(question)
        if len(years_in_q) >= 2:
            yr1 = f"20{years_in_q[0][0]}-{years_in_q[0][1]}"
            yr2 = f"20{years_in_q[1][0]}-{years_in_q[1][1]}"
        calculations = compute_year_over_year_growth(db, yr1, yr2)

    elif intent == "ranking_query":
        yr = fiscal_year or "2022-23"
        top_progs = get_top_programmes(db, yr, n=10)
        sql_results = {"year": yr, "top_programmes": top_progs}

    # RAG evidence retrieval
    evidence = []
    # Evidence retrieval
    evidence = []
    if request.include_evidence:
        try:
            evidence = retrieve_evidence(question, k=request.max_evidence)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")

    # Generate clean, question-focused executive response
    try:
        from slm.response_engine import synthesize_intelligent_response
        from slm.inference import check_gpu
        gpu_info = check_gpu()
        
        synth_data = synthesize_intelligent_response(
            question=question,
            db=db,
            rag_evidence=evidence,
            gpu_info=gpu_info,
        )
        
        mode = "INTEL_ARC_ACCELERATED" if gpu_info.get("device") == "intel_arc_gpu" else (
            "CUDA_GPU_ACCELERATED" if gpu_info.get("available") else "DETERMINISTIC_SQL_RAG"
        )
        
        followups = _generate_followups(intent, district_name, fiscal_year)

        return ChatResponse(
            answer=synth_data["answer"],
            key_metrics=synth_data.get("key_metrics", []),
            table_data=synth_data.get("table_data"),
            chart_data=synth_data.get("chart_data"),
            sources=synth_data.get("sources", []),
            warnings=synth_data.get("warnings", []),
            diagnostics={
                "intent": intent,
                "identified_district": district_name,
                "target_year": fiscal_year or "2022-23",
                "gpu_detected": gpu_info.get("gpu_name"),
                "device_backend": gpu_info.get("backend", "CPU"),
            },
            suggested_followups=followups,
            disclaimer=synth_data.get("disclaimer"),
            model_mode=mode,
            evidence=evidence[:2],
        )
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        followups = _generate_followups(intent, district_name, fiscal_year)
        return ChatResponse(
            answer=f"Could not synthesize response: {e}",
            model_mode="error",
            suggested_followups=followups,
        )


def _generate_followups(intent: str, district: Optional[str], year: Optional[str]) -> list[str]:
    """Generate contextual follow-up question suggestions."""
    followups = []
    d = district or "Nanded"
    yr = year or "2022-23"

    if intent == "budget_query":
        followups = [
            f"Show programme breakdown for {yr}",
            f"How did the budget change from 2022-23 to 2023-24?",
            f"Which programmes received the most funding in {yr}?",
        ]
    elif intent == "trend_analysis":
        followups = [
            f"Which programme grew the fastest?",
            f"How should additional budget be allocated across districts?",
        ]
    elif intent == "programme_analysis":
        followups = [
            f"What % goes to maternal health?",
            f"Compare immunisation funding across years",
        ]
    elif intent == "allocation_recommendation":
        followups = [
            f"What are the assumptions behind this allocation?",
            f"Show allocation with higher vulnerability weighting",
            f"Which districts are most underfunded?",
        ]
    elif intent == "comparison":
        followups = [
            f"What drove the budget change?",
            f"Show programme-level changes",
        ]
    else:
        followups = [
            "What was Maharashtra's NHM budget in 2022-23?",
            "Which programme received the largest allocation?",
            "How should ₹100 crore be distributed across districts?",
        ]
    return followups[:3]
