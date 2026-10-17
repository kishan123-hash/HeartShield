import os
import json
import logging
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("rag_service")

KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent / "knowledge_base" / "documents"


class RAGService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.doc_vectors: List[Dict[int, float]] = []
        self.doc_norms: List[float] = []

        self._load_corpus()
        self._build_index()
        self._initialized = True

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
        stopwords = {
            "the", "and", "is", "in", "to", "of", "it", "with", "for", "as", "on", "at",
            "by", "this", "that", "an", "be", "are", "from", "or", "which", "can", "has"
        }
        return [t for t in tokens if t not in stopwords]

    def _load_corpus(self):
        self.documents = []
        if KNOWLEDGE_BASE_DIR.exists():
            for json_file in sorted(KNOWLEDGE_BASE_DIR.glob("*.json")):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.documents.extend(data)
                        elif isinstance(data, dict):
                            self.documents.append(data)
                except Exception as e:
                    logger.warning(f"Error loading {json_file}: {e}")
            logger.info(f"Loaded {len(self.documents)} medical guideline passages into RAG knowledge base.")
        else:
            logger.warning(f"Knowledge base directory not found at {KNOWLEDGE_BASE_DIR}")

    def _build_index(self):
        if not self.documents:
            return

        df = {}
        num_docs = len(self.documents)

        # Build vocabulary & document frequencies
        doc_tokens_list = []
        for doc in self.documents:
            combined_text = f"{doc.get('title', '')} {doc.get('category', '')} {doc.get('content', '')}"
            tokens = self._tokenize(combined_text)
            doc_tokens_list.append(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        self.vocabulary = {token: idx for idx, token in enumerate(df.keys())}
        self.idf = {token: math.log((num_docs + 1) / (df[token] + 1)) + 1.0 for token in df}

        # Build TF-IDF document vectors
        self.doc_vectors = []
        self.doc_norms = []
        for tokens in doc_tokens_list:
            vec = {}
            for token in tokens:
                if token in self.vocabulary:
                    vec[token] = vec.get(token, 0) + 1.0

            # Apply TF-IDF weighting
            weighted_vec = {}
            sum_sq = 0.0
            for token, tf in vec.items():
                w = (1.0 + math.log(tf)) * self.idf[token]
                weighted_vec[token] = w
                sum_sq += w * w

            norm = math.sqrt(sum_sq) if sum_sq > 0 else 1.0
            self.doc_vectors.append(weighted_vec)
            self.doc_norms.append(norm)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.07
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant medical passages matching query with cosine similarity scores.
        """
        if not self.documents or not self.doc_vectors:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        q_vec = {}
        for token in q_tokens:
            q_vec[token] = q_vec.get(token, 0) + 1.0

        q_weighted = {}
        q_sum_sq = 0.0
        for token, tf in q_vec.items():
            if token in self.idf:
                w = (1.0 + math.log(tf)) * self.idf[token]
                q_weighted[token] = w
                q_sum_sq += w * w

        q_norm = math.sqrt(q_sum_sq) if q_sum_sq > 0 else 1.0

        scores = []
        for idx, (d_vec, d_norm) in enumerate(zip(self.doc_vectors, self.doc_norms)):
            dot_product = sum(
                weight * d_vec[token]
                for token, weight in q_weighted.items()
                if token in d_vec
            )
            similarity = dot_product / (q_norm * d_norm)
            if similarity >= threshold:
                scores.append((idx, similarity))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, sim in scores[:top_k]:
            doc = self.documents[idx]
            results.append({
                "id": doc.get("id"),
                "title": doc.get("title"),
                "source": doc.get("source"),
                "category": doc.get("category"),
                "content": doc.get("content"),
                "similarity_score": round(float(sim), 4)
            })

        return results


rag_service = RAGService()
