from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from facial_recognition import facial_recognition


@dataclass
class MatchResult:
    missing_person_id: str
    similarity: float
    data: Dict[str, Any]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype("float32").ravel()
    b = b.astype("float32").ravel()
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def build_database_embeddings(missing_persons_collection) -> List[Dict[str, Any]]:
    """
    Load all missing-person embeddings into memory.
    """
    people = list(missing_persons_collection.find({"face_embedding": {"$exists": True}}))
    db: List[Dict[str, Any]] = []
    for p in people:
        emb = p.get("face_embedding")
        if not emb:
            continue
        db.append(
            {
                "id": str(p["_id"]),
                "embedding": np.array(emb, dtype="float32"),
                "data": {
                    "name": p.get("name"),
                    "age": p.get("age"),
                    "gender": p.get("gender"),
                    "lastSeenLocation": p.get("lastSeenLocation"),
                    "contactInfo": p.get("contactInfo", ""),
                },
            }
        )
    return db


def best_match_for_embedding(
    query_emb: np.ndarray,
    db_embeddings: List[Dict[str, Any]],
    threshold: float = 0.6,
) -> Optional[MatchResult]:
    """
    Compute best cosine-similarity match for a single query embedding.
    """
    if not db_embeddings:
        return None

    best: Optional[MatchResult] = None
    for cand in db_embeddings:
        sim = cosine_similarity(query_emb, cand["embedding"])
        if sim < threshold:
            continue
        if best is None or sim > best.similarity:
            best = MatchResult(
                missing_person_id=cand["id"],
                similarity=sim,
                data=cand["data"],
            )
    return best


def embedding_from_face_rgb(face_rgb) -> Optional[np.ndarray]:
    """
    Generate an embedding using your existing facial_recognition pipeline.
    """
    emb = facial_recognition.generate_embedding_from_array(face_rgb)
    if emb is None:
        return None
    return np.array(emb, dtype="float32")

