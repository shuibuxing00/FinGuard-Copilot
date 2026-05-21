"""
Compliance RAG (Retrieval-Augmented Generation) module.
Provides vector search over compliance regulations and laws.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings


class ComplianceRAG:
    """
    Retrieves relevant compliance regulations based on anomaly type or query.
    Uses Chroma vector database for semantic search.
    """
    
    # Anomaly type to regulation mapping
    ANOMALY_TO_CLAUSE: Dict[str, str] = {
        "large_amount": "large_transaction_threshold",
        "time_anomaly": "transaction_timing_rules",
        "device_anomaly": "device_security_requirements",
        "amount_spike": "rapid_transaction_detection",
        "rapid_transfers": "fund_movement_restrictions",
        "unusual_pattern": "behavioral_anomaly_detection"
    }
    
    def __init__(self, laws_dir: str = "data/compliance_laws"):
        """
        Initialize compliance RAG with local Chroma instance.
        
        Args:
            laws_dir: Directory containing compliance law text files
        """
        self.laws_dir = Path(laws_dir)
        
        # Initialize Chroma with local persistence
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb",
                persist_directory=".chroma_db",
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="compliance_regulations",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load compliance laws
        self._load_laws()
    
    def _load_laws(self) -> None:
        """
        Load compliance law texts from files and insert into vector database.
        Splits by paragraphs for granular retrieval.
        """
        try:
            if not self.laws_dir.exists():
                print(f"Warning: Laws directory not found: {self.laws_dir}")
                return
            
            # Get all .txt files
            law_files = list(self.laws_dir.glob("*.txt"))
            
            if not law_files:
                print(f"Warning: No law files found in {self.laws_dir}")
                return
            
            doc_id = 0
            
            for law_file in law_files:
                try:
                    with open(law_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    law_name = law_file.stem
                    
                    # Split by paragraphs (double newlines)
                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                    
                    for i, paragraph in enumerate(paragraphs):
                        if len(paragraph) > 10:  # Only add meaningful paragraphs
                            doc_id += 1
                            
                            self.collection.add(
                                ids=[f"{law_name}_{i}"],
                                documents=[paragraph],
                                metadatas=[{
                                    "source": law_name,
                                    "paragraph": i,
                                    "type": "regulation"
                                }]
                            )
                
                except Exception as e:
                    print(f"Error loading {law_file}: {e}")
            
            print(f"Loaded {doc_id} compliance clauses into RAG")
        
        except Exception as e:
            print(f"Error in _load_laws: {e}")
    
    def search(self, query: str, k: int = 3) -> str:
        """
        Search for relevant compliance clauses using semantic similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            Formatted string of relevant regulation clauses
        """
        try:
            if self.collection.count() == 0:
                return "No compliance regulations loaded."
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            if not results or not results['documents'] or not results['documents'][0]:
                return f"No relevant regulations found for: {query}"
            
            # Format results
            output_parts = [f"**Relevant Compliance Clauses** (Query: {query})\n"]
            
            for i, (doc, metadata_list) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0]
            ), 1):
                source = metadata_list.get('source', 'Unknown')
                output_parts.append(f"\n{i}. **{source}**")
                output_parts.append(f"   {doc[:200]}..." if len(doc) > 200 else f"   {doc}")
            
            return "\n".join(output_parts)
        
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def get_compliance_basis(self, anomaly_type: str) -> str:
        """
        Retrieve specific compliance clauses for an anomaly type.
        
        Args:
            anomaly_type: Type of anomaly (large_amount, time_anomaly, etc.)
            
        Returns:
            Relevant regulation text
        """
        try:
            # Map anomaly type to compliance aspect
            search_term = self.ANOMALY_TO_CLAUSE.get(
                anomaly_type,
                anomaly_type
            )
            
            # Search for relevant clauses
            return self.search(
                query=f"{anomaly_type} compliance requirement",
                k=3
            )
        
        except Exception as e:
            return f"Compliance basis lookup error: {str(e)}"
    
    def get_all_sources(self) -> List[str]:
        """
        Get list of all compliance sources loaded.
        
        Returns:
            List of source names
        """
        try:
            if self.collection.count() == 0:
                return []
            
            # Get all metadata
            all_data = self.collection.get()
            sources = set()
            
            for metadata in all_data['metadatas']:
                if 'source' in metadata:
                    sources.add(metadata['source'])
            
            return sorted(list(sources))
        
        except Exception:
            return []
