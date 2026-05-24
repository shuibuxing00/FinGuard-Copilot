"""
Compliance RAG (Retrieval-Augmented Generation) module.
Provides vector search over compliance regulations and laws.
Falls back to keyword search when ChromaDB is unavailable (e.g. Windows without wheels).
"""

from pathlib import Path
from typing import List, Dict, Optional
import re

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False


class _KeywordComplianceIndex:
    """Lightweight in-memory index when ChromaDB cannot be installed."""

    def __init__(self, laws_dir: Path):
        self.documents: List[Dict] = []
        self._load(laws_dir)

    def _load(self, laws_dir: Path) -> None:
        if not laws_dir.exists():
            return
        for law_file in laws_dir.glob("*.txt"):
            try:
                content = law_file.read_text(encoding="utf-8")
                law_name = law_file.stem
                for i, paragraph in enumerate(content.split("\n\n")):
                    paragraph = paragraph.strip()
                    if len(paragraph) > 10:
                        self.documents.append(
                            {"source": law_name, "paragraph": i, "text": paragraph}
                        )
            except OSError as exc:
                print(f"Error loading {law_file}: {exc}")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        if not self.documents:
            return []
        tokens = set(re.findall(r"[a-zA-Z0-9_]+", query.lower()))
        if not tokens:
            return self.documents[:k]

        scored = []
        for doc in self.documents:
            text_lower = doc["text"].lower()
            score = sum(1 for t in tokens if t in text_lower)
            if score:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return self.documents[:k]
        return [doc for _, doc in scored[:k]]


class ComplianceRAG:
    """
    Retrieves relevant compliance regulations based on anomaly type or query.
    Uses Chroma vector database when available; otherwise keyword search.
    """

    ANOMALY_TO_CLAUSE: Dict[str, str] = {
        "large_amount": "large_transaction_threshold",
        "time_anomaly": "transaction_timing_rules",
        "device_anomaly": "device_security_requirements",
        "amount_spike": "rapid_transaction_detection",
        "rapid_transfers": "fund_movement_restrictions",
        "unusual_pattern": "behavioral_anomaly_detection",
        "short_time_high_freq": "rapid_transaction_detection",
        "new_device": "device_security_requirements",
        "location_mismatch": "behavioral_anomaly_detection",
        "amount_peak": "large_transaction_threshold",
    }

    def __init__(self, laws_dir: str = "data/compliance_laws"):
        self.laws_dir = Path(laws_dir)
        self._use_chroma = CHROMADB_AVAILABLE
        self.client = None
        self.collection = None
        self._keyword_index: Optional[_KeywordComplianceIndex] = None

        if self._use_chroma:
            self._init_chroma()
        else:
            self._keyword_index = _KeywordComplianceIndex(self.laws_dir)
            print(
                "ChromaDB not available — using keyword-based compliance search fallback."
            )

    def _init_chroma(self) -> None:
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb",
                persist_directory=".chroma_db",
                anonymized_telemetry=False,
            )
        )
        self.collection = self.client.get_or_create_collection(
            name="compliance_regulations",
            metadata={"hnsw:space": "cosine"},
        )
        self._load_laws_chroma()

    def _load_laws_chroma(self) -> None:
        try:
            if not self.laws_dir.exists() or self.collection is None:
                return
            if self.collection.count() > 0:
                return

            law_files = list(self.laws_dir.glob("*.txt"))
            doc_id = 0
            for law_file in law_files:
                try:
                    content = law_file.read_text(encoding="utf-8")
                    law_name = law_file.stem
                    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                    for i, paragraph in enumerate(paragraphs):
                        if len(paragraph) > 10:
                            doc_id += 1
                            self.collection.add(
                                ids=[f"{law_name}_{i}"],
                                documents=[paragraph],
                                metadatas=[
                                    {
                                        "source": law_name,
                                        "paragraph": i,
                                        "type": "regulation",
                                    }
                                ],
                            )
                except OSError as exc:
                    print(f"Error loading {law_file}: {exc}")
        except Exception as exc:
            print(f"Chroma load error, falling back to keyword index: {exc}")
            self._use_chroma = False
            self._keyword_index = _KeywordComplianceIndex(self.laws_dir)

    def search(self, query: str, k: int = 3) -> str:
        try:
            if self._use_chroma and self.collection is not None:
                return self._search_chroma(query, k)
            return self._search_keyword(query, k)
        except Exception as exc:
            return f"Search error: {exc}"

    def _search_chroma(self, query: str, k: int) -> str:
        if self.collection.count() == 0:
            return "No compliance regulations loaded."

        results = self.collection.query(query_texts=[query], n_results=k)
        if not results or not results["documents"] or not results["documents"][0]:
            return f"No relevant regulations found for: {query}"

        output_parts = [f"**Relevant Compliance Clauses** (Query: {query})\n"]
        for i, (doc, metadata_list) in enumerate(
            zip(results["documents"][0], results["metadatas"][0]), 1
        ):
            source = metadata_list.get("source", "Unknown")
            output_parts.append(f"\n{i}. **{source}**")
            output_parts.append(
                f"   {doc[:200]}..." if len(doc) > 200 else f"   {doc}"
            )
        return "\n".join(output_parts)

    def _search_keyword(self, query: str, k: int) -> str:
        if not self._keyword_index or not self._keyword_index.documents:
            return "No compliance regulations loaded."

        hits = self._keyword_index.search(query, k)
        output_parts = [
            f"**Relevant Compliance Clauses** (Keyword search — Query: {query})\n"
        ]
        for i, doc in enumerate(hits, 1):
            text = doc["text"]
            output_parts.append(f"\n{i}. **{doc['source']}**")
            output_parts.append(
                f"   {text[:200]}..." if len(text) > 200 else f"   {text}"
            )
        return "\n".join(output_parts)

    def get_compliance_basis(self, anomaly_type: str) -> str:
        try:
            return self.search(
                query=f"{anomaly_type} compliance requirement",
                k=3,
            )
        except Exception as exc:
            return f"Compliance basis lookup error: {exc}"

    def get_all_sources(self) -> List[str]:
        try:
            if self._use_chroma and self.collection is not None:
                if self.collection.count() == 0:
                    return []
                all_data = self.collection.get()
                sources = {
                    m["source"] for m in all_data["metadatas"] if "source" in m
                }
                return sorted(sources)

            if self._keyword_index:
                return sorted({d["source"] for d in self._keyword_index.documents})
            return []
        except Exception:
            return []
