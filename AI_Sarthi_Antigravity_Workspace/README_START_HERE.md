# AI Sarthi — Antigravity Workspace

## How to use
1. Extract the entire ZIP locally (do not open the ZIP as the project folder).
2. Start Google Antigravity IDE → New Project → Add Folder → select the extracted `AI_Sarthi_Antigravity_Workspace` folder → Create → Local mode.
3. Paste `ANTIGRAVITY_MASTER_PROMPT.md` into the agent chat and ask it to execute end to end, not just plan.
4. Add two **missing** original FY 2026–27 districtwise detailed PDFs to `datasets/pdfs/`, if you have them. Suggested original names: `Maharashtra District wise budget expenditure 1(1).pdf` and `Maharashtra District wise budget expenditure 2(1).pdf`. They are not included here and cannot be silently reconstructed.
5. The uploaded files are *source inputs*, not a complete or verified district-year historical finance database. Validation and reconciliation are required.
6. INR 0 hard limit: do not activate paid GPU hosting or any billed service without approval. Hugging Face public model inference may need paid/eligible GPU.

### Contents
- `model/`: already-trained adapter ZIP; do not retrain automatically.
- `datasets/archives/`: four historical NHM PIP/ROP archives.
- `datasets/pdfs/`: Maharashtra Economic Survey 2025–26.
- `datasets/processed/`: extracted legacy CSV datasets; treat them as unverified until validated.
- `ANTIGRAVITY_MASTER_PROMPT.md`: agent implementation instructions.
- `manifest.json`: actual included files.

The prompt asks Antigravity to create ALL production code; none is assumed to be supplied.
