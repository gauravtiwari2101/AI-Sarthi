"""System Status Router"""
from fastapi import APIRouter
from slm.inference import get_slm, check_gpu
from rag.retrieval import get_rag_system

router = APIRouter()


@router.get("/status")
def system_status():
    """Get overall system status."""
    gpu = check_gpu()

    try:
        slm = get_slm()
        slm_status = slm.get_status()
    except Exception as e:
        slm_status = {"error": str(e), "loaded": False}

    try:
        rag = get_rag_system()
        rag_status = rag.get_status()
    except Exception as e:
        rag_status = {"error": str(e)}

    return {
        "system": "AI Sarthi v1.0",
        "gpu": gpu,
        "slm": slm_status,
        "rag": rag_status,
        "active_mode": _determine_mode(slm_status, gpu),
        "capabilities": {
            "sql_queries": True,
            "financial_calculations": True,
            "needs_based_allocation": True,
            "document_retrieval": rag_status.get("document_count", 0) > 0,
            "ai_explanation": slm_status.get("loaded", False),
            "multilingual": slm_status.get("loaded", False),
        },
    }


def _determine_mode(slm_status: dict, gpu: dict) -> str:
    if slm_status.get("loaded") and slm_status.get("mode") == "qwen3_lora":
        return "FULL_AI_MODE (Qwen3 LoRA Active)"
    if gpu.get("device") == "intel_arc_gpu":
        return "INTEL_ARC_ACCELERATED (Intel Arc 130V Active)"
    if gpu.get("available"):
        return f"GPU_ACCELERATED ({gpu.get('gpu_name', 'Active')})"
    return "DETERMINISTIC_SQL_RAG_MODE"
