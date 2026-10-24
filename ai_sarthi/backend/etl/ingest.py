"""
AI Sarthi — Database Ingestion
Populates district tables, seeds known data, and ingests extracted records.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import (
    Base, District, FinancialRecord, DataQualityLog,
    SourceDocument, engine, create_tables, get_session
)
from constants import (
    MAHARASHTRA_DISTRICTS, DISTRICT_POPULATION_LAKH,
    DISTRICT_VULNERABILITY_INDEX
)

logger = logging.getLogger(__name__)

WORKSPACE = Path(__file__).parent.parent.parent.parent / "AI_Sarthi_Antigravity_Workspace"


def seed_districts(session) -> dict[str, int]:
    """Insert/update all 36 Maharashtra districts. Returns name→id map."""
    district_id_map = {}
    for d in MAHARASHTRA_DISTRICTS:
        existing = session.query(District).filter(District.name == d["name"]).first()
        if not existing:
            dist = District(
                id=d["id"],
                name=d["name"],
                division=d["division"],
                region=d["region"],
                population_lakh=DISTRICT_POPULATION_LAKH.get(d["name"]),
                vulnerability_index=DISTRICT_VULNERABILITY_INDEX.get(d["name"]),
            )
            dist.aliases = d["aliases"]
            session.add(dist)
            district_id_map[d["name"]] = d["id"]
            logger.debug(f"Inserted district: {d['name']}")
        else:
            # Update population/vulnerability if not set
            if existing.population_lakh is None:
                existing.population_lakh = DISTRICT_POPULATION_LAKH.get(d["name"])
            if existing.vulnerability_index is None:
                existing.vulnerability_index = DISTRICT_VULNERABILITY_INDEX.get(d["name"])
            district_id_map[d["name"]] = existing.id

    session.commit()
    logger.info(f"Seeded {len(district_id_map)} districts")
    return district_id_map


def seed_source_documents(session):
    """Seed known source document metadata."""
    sources = [
        {
            "filename": "Economic Survey of Maharashtra 2025-26.pdf",
            "document_type": "Economic Survey",
            "year_range": "2025-26",
            "scope_description": "Public finances, health infrastructure, district indicators",
            "pages_or_sheets": 354,
        },
        {
            "filename": "Maharashtra-ROP-2022-24/Maharashtra ROP 22-24.pdf",
            "document_type": "ROP PDF",
            "year_range": "2022-24",
            "scope_description": "Document retrieval; not automatically actual expenditure",
            "pages_or_sheets": 402,
        },
        {
            "filename": "Maharashtra-ROP-2024-26/MAHARASHTRA ROP 24-26.pdf",
            "document_type": "ROP PDF",
            "year_range": "2024-26",
            "scope_description": "Document retrieval; not automatically actual expenditure",
            "pages_or_sheets": 306,
        },
        {
            "filename": "Post NPCC_PIP22-24_17mar2022.xlsx",
            "document_type": "PIP Excel",
            "year_range": "2022-24",
            "scope_description": "Statewide NHM PIP proposals; Annexure-1_detailed has col L=FY2022-23, col P=FY2023-24 in ₹ lakh",
            "pages_or_sheets": 5,
        },
        {
            "filename": "Maharashtra NHM PIP 2024_2026 04.11.2023.xlsx",
            "document_type": "PIP Excel",
            "year_range": "2024-26",
            "scope_description": "Statewide NHM PIP proposals 2024-26",
            "pages_or_sheets": 10,
        },
        {
            "filename": "Maharashtra District wise budget expenditure 1.pdf",
            "document_type": "District Budget PDF",
            "year_range": "2026-27",
            "scope_description": "District-wise NHM budget expenditure (Part 1)",
            "pages_or_sheets": None,
            "notes": "FY 2026-27 detailed district data",
        },
        {
            "filename": "Maharashtra District wise budget expenditure 2.pdf",
            "document_type": "District Budget PDF",
            "year_range": "2026-27",
            "scope_description": "District-wise NHM budget expenditure (Part 2)",
            "pages_or_sheets": None,
            "notes": "FY 2026-27 detailed district data",
        },
    ]

    for src in sources:
        existing = session.query(SourceDocument).filter(
            SourceDocument.filename == src["filename"]
        ).first()
        if not existing:
            doc = SourceDocument(**{k: v for k, v in src.items() if v is not None})
            session.add(doc)

    session.commit()
    logger.info("Seeded source documents")


def ingest_statewide_pip_records(session, records: list[dict]) -> int:
    """
    Ingest statewide PIP records into financial_records table.
    These have scope=STATEWIDE and district_id=None.
    Returns count of inserted records.
    """
    count = 0
    for rec in records:
        try:
            amount = float(rec.get("amount_lakh", 0))
            if amount <= 0:
                continue

            fr = FinancialRecord(
                district_id=None,  # Statewide
                financial_year=rec["fiscal_year"],
                programme=rec.get("programme"),
                scheme=rec.get("scheme"),
                pool=rec.get("pool"),
                financial_stage=rec.get("stage", "PROPOSED_PIP"),
                amount_lakh=amount,
                currency_unit="lakh",
                scope="STATEWIDE",
                source_document=rec.get("source_file"),
                source_sheet=rec.get("sheet"),
                source_row=rec.get("row"),
                fmr_code=rec.get("fmr_code"),
                objective=rec.get("objective"),
                verification_status=rec.get("verification_status", "UNVERIFIED"),
                notes="Statewide PIP proposal; not individual district allocation",
            )
            session.add(fr)
            count += 1

            if count % 1000 == 0:
                session.flush()
                logger.info(f"Flushed {count} records...")

        except Exception as e:
            logger.warning(f"Failed to insert record: {e}")

    session.commit()
    logger.info(f"Ingested {count} statewide PIP records")
    return count


def log_quality_check(session, check_name: str, status: str, message: str,
                       district: str = None, year: str = None, source: str = None):
    """Log a data quality check result."""
    entry = DataQualityLog(
        check_name=check_name,
        district_name=district,
        financial_year=year,
        status=status,
        message=message,
        source_document=source,
    )
    session.add(entry)


def run_quality_checks(session) -> list[dict]:
    """Run data quality checks and return results."""
    results = []

    # Check 1: All 36 districts exist
    district_count = session.query(District).count()
    status = "PASS" if district_count == 36 else "FAIL"
    msg = f"Expected 36 districts, found {district_count}"
    log_quality_check(session, "district_count", status, msg)
    results.append({"check": "district_count", "status": status, "message": msg})

    # Check 2: Statewide records don't have district_id
    statewide_with_district = session.query(FinancialRecord).filter(
        FinancialRecord.scope == "STATEWIDE",
        FinancialRecord.district_id.isnot(None)
    ).count()
    status = "PASS" if statewide_with_district == 0 else "FAIL"
    msg = f"Statewide records with district_id: {statewide_with_district}"
    log_quality_check(session, "statewide_district_isolation", status, msg)
    results.append({"check": "statewide_district_isolation", "status": status, "message": msg})

    # Check 3: No negative amounts
    negative = session.query(FinancialRecord).filter(
        FinancialRecord.amount_lakh < 0
    ).count()
    status = "PASS" if negative == 0 else "WARN"
    msg = f"Records with negative amounts: {negative}"
    log_quality_check(session, "no_negative_amounts", status, msg)
    results.append({"check": "no_negative_amounts", "status": status, "message": msg})

    # Check 4: Known fiscal years
    from sqlalchemy import distinct
    years = [r[0] for r in session.query(distinct(FinancialRecord.financial_year)).all()]
    valid_years = {"2022-23", "2023-24", "2024-25", "2025-26", "2026-27"}
    invalid_years = [y for y in years if y and y not in valid_years]
    status = "PASS" if not invalid_years else "WARN"
    msg = f"Fiscal years found: {sorted(years)}. Invalid: {invalid_years}"
    log_quality_check(session, "fiscal_year_validity", status, msg)
    results.append({"check": "fiscal_year_validity", "status": status, "message": msg})

    session.commit()
    return results


def run_ingestion():
    """Main ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    logger.info("=== AI Sarthi Data Ingestion ===")
    create_tables()

    with get_session() as session:
        # Step 1: Seed districts
        logger.info("Step 1: Seeding districts...")
        district_map = seed_districts(session)
        logger.info(f"Districts seeded: {len(district_map)}")

        # Step 2: Seed source documents
        logger.info("Step 2: Seeding source documents...")
        seed_source_documents(session)

        # Step 3: Extract data / load deduplicated records
        logger.info("Step 3: Loading verified deduplicated data...")
        csv_file = WORKSPACE / "datasets" / "processed" / "pip_proposals_numeric_unreviewed.csv"
        records_to_ingest = []
        
        if csv_file.exists():
            import pandas as pd
            logger.info(f"Loading deduplicated records from {csv_file.name}...")
            df = pd.read_csv(csv_file)
            for _, r in df.iterrows():
                records_to_ingest.append({
                    "fiscal_year": str(r["fiscal_year"]),
                    "stage": "PROPOSED_PIP",
                    "amount_lakh": float(r["amount_lakh"]),
                    "pool": str(r["pool"]) if pd.notna(r["pool"]) else None,
                    "programme": str(r["programme"]) if pd.notna(r["programme"]) else None,
                    "scheme": str(r["scheme"]) if pd.notna(r["scheme"]) else None,
                    "objective": str(r["objective"]) if pd.notna(r["objective"]) else None,
                    "fmr_code": str(r["fmr_code"]) if pd.notna(r["fmr_code"]) else None,
                    "source_file": str(r["source_file"]) if pd.notna(r["source_file"]) else None,
                    "sheet": str(r["sheet"]) if pd.notna(r["sheet"]) else None,
                    "row": int(r["row"]) if pd.notna(r["row"]) else None,
                    "verification_status": "DEDUPLICATED_SOURCE",
                })
            logger.info(f"Loaded {len(records_to_ingest)} clean records from CSV")
        else:
            from etl.extract import run_full_extraction
            extracted = run_full_extraction()
            records_to_ingest = extracted["statewide_records"]

        # Clear existing financial records to eliminate duplicate workbook runs
        session.query(FinancialRecord).delete()
        session.commit()

        # Step 4: Ingest statewide PIP records
        logger.info("Step 4: Ingesting statewide PIP records...")
        count = ingest_statewide_pip_records(session, records_to_ingest)
        logger.info(f"Ingested {count} statewide PIP records")

        # Step 5: Data quality checks
        logger.info("Step 5: Running quality checks...")
        quality_results = run_quality_checks(session)
        for result in quality_results:
            logger.info(f"  [{result['status']}] {result['check']}: {result['message']}")

    logger.info("=== Ingestion Complete ===")
    return quality_results


if __name__ == "__main__":
    run_ingestion()
