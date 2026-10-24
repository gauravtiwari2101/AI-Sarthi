"""
AI Sarthi — RAG (Retrieval-Augmented Generation) System
Ingests documents, creates embeddings, and provides hybrid retrieval.
"""
import os
import json
import logging
import pickle
from pathlib import Path
from typing import Optional
import re

logger = logging.getLogger(__name__)

WORKSPACE = Path(__file__).parent.parent.parent.parent / "AI_Sarthi_Antigravity_Workspace"
RAG_INDEX_DIR = Path(__file__).parent.parent.parent / "data" / "rag_index"
RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i: i + chunk_size])
        if len(chunk.strip()) > 50:  # Skip tiny chunks
            chunks.append(chunk)
    return chunks


def build_rag_corpus() -> list[dict]:
    """
    Build RAG corpus from all available documents.
    Returns list of {text, metadata} dicts.
    """
    documents = []
    processed_dir = WORKSPACE / "datasets" / "processed"

    # Load pre-processed PDF text
    pdf_text_file = processed_dir / "pdf_page_text_extended.csv"
    if pdf_text_file.exists():
        import pandas as pd
        df = pd.read_csv(pdf_text_file)
        for _, row in df.iterrows():
            text = str(row.get("text", "")).strip()
            if len(text) < 50:
                continue
            chunks = chunk_text(text)
            for ci, chunk in enumerate(chunks):
                documents.append({
                    "text": chunk,
                    "source_file": str(row.get("source_file", "")),
                    "page": row.get("page"),
                    "document_type": str(row.get("document_type", "PDF")),
                    "year_range": str(row.get("year_range", "")),
                    "chunk_index": ci,
                    "metadata_str": f"Source: {row.get('source_file', '')}, Page: {row.get('page', '?')}",
                })
        logger.info(f"Loaded {len(documents)} PDF text chunks")

    # Load RAG documents
    rag_doc_file = processed_dir / "rag_documents_extended.csv"
    if rag_doc_file.exists():
        import pandas as pd
        df = pd.read_csv(rag_doc_file)
        for _, row in df.iterrows():
            text = str(row.get("text", "")).strip()
            if len(text) < 50:
                continue
            chunks = chunk_text(text, chunk_size=400)
            for ci, chunk in enumerate(chunks):
                src = str(row.get("source_file", ""))
                documents.append({
                    "text": chunk,
                    "source_file": src,
                    "page": row.get("page"),
                    "document_type": str(row.get("document_type", "RAG")),
                    "year_range": str(row.get("year_range", "")),
                    "chunk_index": ci,
                    "metadata_str": f"Source: {src}, Page: {row.get('page', '?')}",
                })
        logger.info(f"Total documents after RAG CSV: {len(documents)}")

    return documents


class RAGSystem:
    """
    Hybrid retrieval system using FAISS for semantic search
    and BM25-style keyword search as fallback.
    """

    def __init__(self):
        self.documents: list[dict] = []
        self.embedder = None
        self.faiss_index = None
        self.embeddings_available = False
        self._load_or_build()

    def _try_load_embedder(self):
        """Try to load sentence-transformers embedder (free, local)."""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            logger.info(f"Loading embedder: {model_name}")
            self.embedder = SentenceTransformer(model_name)
            self.embeddings_available = True
            logger.info("Embedder loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed; using keyword-only search")
        except Exception as e:
            logger.warning(f"Could not load embedder: {e}")

    def _load_or_build(self):
        """Load existing index or build from scratch."""
        index_file = RAG_INDEX_DIR / "faiss_index.pkl"
        docs_file = RAG_INDEX_DIR / "documents.pkl"

        if index_file.exists() and docs_file.exists():
            logger.info("Loading existing RAG index...")
            try:
                with open(docs_file, "rb") as f:
                    self.documents = pickle.load(f)
                with open(index_file, "rb") as f:
                    self.faiss_index = pickle.load(f)
                if self.faiss_index is not None:
                    self.embeddings_available = True
                    self._try_load_embedder()
                logger.info(f"Loaded RAG index with {len(self.documents)} documents")
                return
            except Exception as e:
                logger.warning(f"Could not load existing index: {e}")

        # Build new index
        self._build_index()

    def _build_index(self):
        """Build FAISS index from corpus."""
        logger.info("Building RAG index from corpus...")
        self.documents = build_rag_corpus()

        if not self.documents:
            logger.warning("No documents found for RAG index")
            return

        self._try_load_embedder()

        if self.embeddings_available and self.embedder:
            try:
                import faiss
                import numpy as np

                logger.info(f"Computing embeddings for {len(self.documents)} chunks...")
                texts = [d["text"] for d in self.documents]

                # Batch embed
                batch_size = 64
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i: i + batch_size]
                    embs = self.embedder.encode(batch, show_progress_bar=False)
                    all_embeddings.append(embs)
                    if i % 1000 == 0:
                        logger.info(f"Embedded {i}/{len(texts)} chunks...")

                embeddings = np.vstack(all_embeddings).astype("float32")
                faiss.normalize_L2(embeddings)

                dim = embeddings.shape[1]
                self.faiss_index = faiss.IndexFlatIP(dim)  # Inner product (cosine after normalize)
                self.faiss_index.add(embeddings)
                logger.info(f"Built FAISS index with {self.faiss_index.ntotal} vectors")

                # Save index
                with open(RAG_INDEX_DIR / "faiss_index.pkl", "wb") as f:
                    pickle.dump(self.faiss_index, f)
                with open(RAG_INDEX_DIR / "documents.pkl", "wb") as f:
                    pickle.dump(self.documents, f)
                logger.info("RAG index saved")

            except ImportError:
                logger.warning("faiss-cpu not installed; using keyword-only search")
                self.embeddings_available = False
            except Exception as e:
                logger.error(f"FAISS build failed: {e}")
                self.embeddings_available = False
        else:
            # Save documents only
            with open(RAG_INDEX_DIR / "documents.pkl", "wb") as f:
                pickle.dump(self.documents, f)

    def keyword_search(self, query: str, k: int = 10) -> list[dict]:
        """BM25-style keyword search using TF-IDF approximation."""
        query_terms = set(re.sub(r'[^\w\s]', ' ', query.lower()).split())
        if not query_terms:
            return []

        scored = []
        for i, doc in enumerate(self.documents):
            text_lower = doc["text"].lower()
            # Count query term occurrences
            score = sum(
                text_lower.count(term) * (1 / (1 + text_lower.count(term)))
                for term in query_terms
                if len(term) > 2
            )
            # Boost for exact phrase
            if query.lower() in text_lower:
                score += 5.0
            if score > 0:
                scored.append((score, i, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, idx, doc in scored[:k]:
            results.append({**doc, "score": score, "retrieval_method": "keyword"})
        return results

    def semantic_search(self, query: str, k: int = 10) -> list[dict]:
        """FAISS-based semantic search."""
        if not self.embeddings_available or self.faiss_index is None:
            return []

        try:
            import numpy as np
            import faiss

            q_emb = self.embedder.encode([query]).astype("float32")
            faiss.normalize_L2(q_emb)

            scores, indices = self.faiss_index.search(q_emb, k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.documents):
                    results.append({
                        **self.documents[idx],
                        "score": float(score),
                        "retrieval_method": "semantic",
                    })
            return results
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
            return []

    def hybrid_retrieve(self, query: str, k: int = 8) -> list[dict]:
        """
        Hybrid retrieval: combine semantic and keyword results.
        Returns top-k deduplicated results.
        """
        semantic_results = self.semantic_search(query, k=k * 2)
        keyword_results = self.keyword_search(query, k=k * 2)

        # Deduplicate and merge by document text fingerprint
        seen = set()
        merged = []
        for r in semantic_results + keyword_results:
            fp = hash(r["text"][:200])
            if fp not in seen:
                seen.add(fp)
                merged.append(r)

        # Sort by score, take top k
        merged.sort(key=lambda x: x.get("score", 0), reverse=True)
        return merged[:k]

    def get_status(self) -> dict:
        """Return RAG system status."""
        return {
            "document_count": len(self.documents),
            "embeddings_available": self.embeddings_available,
            "faiss_index_vectors": self.faiss_index.ntotal if self.faiss_index else 0,
            "index_saved": (RAG_INDEX_DIR / "faiss_index.pkl").exists(),
        }


# Singleton instance
_rag_system: Optional[RAGSystem] = None


def get_rag_system() -> RAGSystem:
    """Get or create the singleton RAG system."""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
    return _rag_system


def retrieve_evidence(query: str, k: int = 5) -> list[dict]:
    """
    Public API: retrieve relevant evidence for a query.
    Returns list of evidence dicts with source citations.
    """
    rag = get_rag_system()
    results = rag.hybrid_retrieve(query, k=k)

    # Format for API response
    evidence = []
    for r in results:
        evidence.append({
            "text": r["text"][:800],  # Limit length
            "source": r.get("source_file", "Unknown"),
            "page": r.get("page"),
            "year_range": r.get("year_range"),
            "retrieval_method": r.get("retrieval_method", "keyword"),
            "relevance_score": round(r.get("score", 0), 4),
            "citation": r.get("metadata_str", ""),
        })

    return evidence
