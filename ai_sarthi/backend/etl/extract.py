"""
AI Sarthi — ETL: Data Extraction Pipeline
Extracts financial data from PIP Excel files, PDFs, and processed CSVs.
"""
import zipfile
import io
import os
import re
import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

WORKSPACE = Path(__file__).parent.parent.parent.parent / "AI_Sarthi_Antigravity_Workspace"
ARCHIVES_DIR = WORKSPACE / "datasets" / "archives"
PROCESSED_DIR = WORKSPACE / "datasets" / "processed"
PDFS_DIR = WORKSPACE / "datasets" / "pdfs"


def find_excel_files_in_zip(zip_path: Path) -> list[tuple[str, bytes]]:
    """Recursively find all Excel files inside a ZIP (including nested ZIPs)."""
    results = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for name in z.namelist():
                lower = name.lower()
                if lower.endswith(('.xlsx', '.xls')):
                    try:
                        data = z.read(name)
                        results.append((name, data))
                        logger.info(f"Found Excel: {name}")
                    except Exception as e:
                        logger.warning(f"Could not read {name}: {e}")
                elif lower.endswith('.zip'):
                    try:
                        inner_data = z.read(name)
                        inner_zip = io.BytesIO(inner_data)
                        try:
                            with zipfile.ZipFile(inner_zip, 'r') as z2:
                                for inner_name in z2.namelist():
                                    if inner_name.lower().endswith(('.xlsx', '.xls')):
                                        try:
                                            data = z2.read(inner_name)
                                            full_name = f"{name}/{inner_name}"
                                            results.append((full_name, data))
                                            logger.info(f"Found nested Excel: {full_name}")
                                        except Exception as e:
                                            logger.warning(f"Cannot read nested {inner_name}: {e}")
                        except zipfile.BadZipFile:
                            pass
                    except Exception as e:
                        logger.warning(f"Cannot open nested ZIP {name}: {e}")
    except Exception as e:
        logger.error(f"Cannot open {zip_path}: {e}")
    return results


def detect_annexure1_detailed_headers(df_raw: pd.DataFrame) -> dict:
    """
    Detect which rows/columns contain the actual financial data headers
    in an Annexure-1_detailed sheet.
    Returns dict with header_row, col_fy1, col_fy1_label, col_fy2, col_fy2_label, fiscal_years.
    """
    # Search first 10 rows for the header row with 'Budget required'
    header_row = None
    for i in range(min(10, len(df_raw))):
        row_vals = [str(v).strip().lower() for v in df_raw.iloc[i].tolist() if pd.notna(v)]
        joined = " ".join(row_vals)
        if "budget required" in joined or "rs. in lakhs" in joined.replace(".", ""):
            header_row = i
            break

    if header_row is None:
        return {}

    # Find the row after header_row that has fiscal year label sub-headers
    sub_header_row = header_row + 1 if header_row + 1 < len(df_raw) else header_row

    # Build column mapping by scanning header + sub-header rows
    col_map = {}
    sub_row = df_raw.iloc[sub_header_row] if sub_header_row < len(df_raw) else df_raw.iloc[header_row]

    for col_idx, val in enumerate(sub_row):
        if pd.isna(val):
            continue
        val_str = str(val).lower().strip()
        if "budget required" in val_str or "rs. in lakhs" in val_str:
            col_map[col_idx] = val_str

    # Also scan the header row
    header_row_data = df_raw.iloc[header_row]
    for col_idx, val in enumerate(header_row_data):
        if pd.isna(val):
            continue
        val_str = str(val).lower().strip()
        if "budget required" in val_str:
            col_map[col_idx] = val_str

    # Extract year-specific columns with validation
    fy_cols = {}
    for col_idx, label in col_map.items():
        m = re.search(r'(\d{4})-(\d{2})', label)
        if m:
            yr1 = int(m.group(1))
            yr2 = int(m.group(2))
            # Validate: second part should be yr1+1 mod 100
            if yr2 == (yr1 + 1) % 100:
                year = f"{m.group(1)}-{m.group(2)}"
                fy_cols[year] = col_idx

    return {
        "header_row": header_row,
        "sub_header_row": sub_header_row,
        "fy_cols": fy_cols,
        "col_map": col_map,
    }


def extract_pip_annexure1_detailed(
    excel_data: bytes,
    source_file: str,
    sheet_name: str = "Annexure-1_detailed",
) -> list[dict]:
    """
    Extract financial rows from Annexure-1_detailed sheet.
    Returns list of raw record dicts with provenance.
    These are STATEWIDE proposed PIP amounts (not district-level).
    """
    records = []
    try:
        xl = pd.read_excel(io.BytesIO(excel_data), sheet_name=sheet_name, header=None)
    except Exception as e:
        logger.warning(f"Cannot read sheet {sheet_name} from {source_file}: {e}")
        return records

    # Detect header structure
    n_rows, n_cols = xl.shape
    logger.info(f"Annexure-1_detailed: {n_rows} rows x {n_cols} cols in {source_file}")

    # Row 0: Title; Row 1: repeat; Row 2: main headers; Row 3: sub-headers; Row 4+: data
    # PIP 2022-24: col 11=Budget 2022-23, col 15=Budget 2023-24 (₹ lakh)
    # PIP 2024-26: col 8=Budget 2024-25, col varies for 2025-26

    # Verify column structure from row 3 (sub-headers)
    if n_rows < 4:
        logger.warning(f"Too few rows in {sheet_name}")
        return records

    sub_header = xl.iloc[3].tolist()
    logger.debug(f"Sub-header row: {sub_header}")

    # Identify fiscal year columns dynamically
    fy_col_map = {}
    for i, cell in enumerate(sub_header):
        if pd.isna(cell):
            continue
        cell_str = str(cell).lower()
        m = re.search(r'(\d{4})-(\d{2})', cell_str)
        if m and ("budget" in cell_str or "rs" in cell_str or "lakh" in cell_str):
            fy = f"{m.group(1)}-{m.group(2)}"
            fy_col_map[fy] = i

    # Fallback to expected positions if auto-detection fails
    if not fy_col_map:
        # Determine period from source filename
        fname_lower = source_file.lower()
        if '2024' in fname_lower and '2026' in fname_lower:
            # PIP 2024-26: scan for amount columns around col 8-18
            if n_cols > 8:
                fy_col_map = {"2024-25": 8}
            if n_cols > 15:
                fy_col_map["2025-26"] = 15
        elif n_cols > 15:
            fy_col_map = {"2022-23": 11, "2023-24": 15}
        elif n_cols > 11:
            fy_col_map = {"2022-23": 11}

    logger.info(f"Detected FY columns: {fy_col_map}")

    # Extract data rows (starting from row 4)
    current_pool = None
    current_programme = None

    for row_idx in range(4, n_rows):
        row = xl.iloc[row_idx].tolist()

        # Update pool/programme from column 0 and 2
        if pd.notna(row[0]) and str(row[0]).strip():
            pool_val = str(row[0]).strip()
            if not any(c.isdigit() for c in pool_val[:3]):  # Not a number
                current_pool = pool_val

        if len(row) > 2 and pd.notna(row[2]) and str(row[2]).strip():
            prog_val = str(row[2]).strip()
            if len(prog_val) > 2 and not prog_val.replace('.', '').replace(',', '').isdigit():
                current_programme = prog_val

        # Extract FMR code (col 1) and scheme (col 4)
        fmr_code = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else None
        scheme = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else None
        objective = str(row[5]).strip() if len(row) > 5 and pd.notna(row[5]) else None

        # Skip header/summary rows
        if not fmr_code or fmr_code.lower() in ('fmr code', 'nan', 'none', ''):
            continue
        if not scheme or scheme.lower() in ('scheme/ activity', 'nan', 'none', ''):
            continue

        for fy, col_idx in fy_col_map.items():
            if col_idx >= len(row):
                continue
            amount_raw = row[col_idx]
            if pd.isna(amount_raw):
                continue
            try:
                amount = float(amount_raw)
            except (ValueError, TypeError):
                continue

            if amount <= 0:
                continue

            records.append({
                "fiscal_year": fy,
                "stage": "PROPOSED_PIP",
                "amount_lakh": amount,
                "pool": current_pool,
                "programme": current_programme,
                "scheme": scheme,
                "objective": objective,
                "fmr_code": fmr_code,
                "district": None,  # STATEWIDE - not district level
                "scope": "STATEWIDE",
                "source_file": source_file,
                "sheet": sheet_name,
                "row": row_idx + 1,  # 1-indexed
                "col": col_idx + 1,
                "provenance": "excel_cell_direct",
                "verification_status": "UNVERIFIED",
            })

    logger.info(f"Extracted {len(records)} records from {source_file}/{sheet_name}")
    return records


def extract_budget_pdfs() -> list[dict]:
    """
    Extract text and financial data from district budget PDFs.
    Returns page-level records for RAG use.
    """
    records = []
    pdf_files = list(PDFS_DIR.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDFs to process")

    for pdf_path in pdf_files:
        logger.info(f"Processing PDF: {pdf_path.name}")
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    tables = page.extract_tables()
                    records.append({
                        "source_file": pdf_path.name,
                        "page": page_num,
                        "text": text[:5000],  # Limit for storage
                        "has_table": len(tables) > 0,
                        "table_count": len(tables),
                        "document_type": "PDF",
                    })
        except ImportError:
            logger.warning("pdfplumber not installed; using pre-processed CSV for PDFs")
            break
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")

    return records


def load_processed_csvs() -> dict[str, pd.DataFrame]:
    """Load all pre-processed CSV datasets."""
    csvs = {}
    for csv_file in PROCESSED_DIR.glob("*.csv"):
        try:
            csvs[csv_file.stem] = pd.read_csv(csv_file)
            logger.info(f"Loaded {csv_file.name}: {len(csvs[csv_file.stem])} rows")
        except Exception as e:
            logger.error(f"Error loading {csv_file.name}: {e}")
    return csvs


def run_full_extraction() -> dict[str, list]:
    """
    Run the complete data extraction pipeline.
    Returns dict with 'statewide_records', 'pdf_pages', 'rag_docs'.
    """
    logger.info("Starting full data extraction pipeline...")
    all_records = []

    # Extract from PIP 2022-24
    pip2224_zip = ARCHIVES_DIR / "Maharashtra-PIP-2022-24.zip"
    if pip2224_zip.exists():
        excel_files = find_excel_files_in_zip(pip2224_zip)
        for fname, data in excel_files:
            if "NPCC_PIP22-24" in fname or "PIP22-24" in fname.upper():
                # Extract Annexure-1_detailed
                records = extract_pip_annexure1_detailed(data, fname, "Annexure-1_detailed")
                all_records.extend(records)
                logger.info(f"PIP 2022-24: extracted {len(records)} records")

    # Extract from PIP 2024-26
    pip2426_zip = ARCHIVES_DIR / "Maharahtra-PIP-2024-26.zip"
    if pip2426_zip.exists():
        excel_files = find_excel_files_in_zip(pip2426_zip)
        for fname, data in excel_files:
            if "PIP" in fname.upper() and fname.lower().endswith(('.xlsx', '.xls')):
                records = extract_pip_annexure1_detailed(data, fname, "Annexure-1_detailed")
                all_records.extend(records)
                logger.info(f"PIP 2024-26: extracted {len(records)} records from {fname}")

    # Load pre-processed CSVs
    csvs = load_processed_csvs()

    return {
        "statewide_records": all_records,
        "csv_data": csvs,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_full_extraction()
    print(f"Extracted {len(result['statewide_records'])} statewide PIP records")
    print(f"Loaded CSVs: {list(result['csv_data'].keys())}")
