"""
Skill Embeddings — sentence-transformer based semantic vectors for skills.

Uses all-MiniLM-L6-v2 (22MB, CPU-friendly, 384-dim).
Embeddings are cached in-memory and optionally persisted to a .npz file.

Usage:
    from app.ml.embeddings import get_embedder
    embedder = get_embedder()
    vec = embedder.encode_skill("machine learning")
    sim = embedder.cosine_similarity("python", "java")
"""

from __future__ import annotations

import os
import logging
import numpy as np
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Model to use — lightweight, no GPU needed
MODEL_NAME = "all-MiniLM-L6-v2"
CACHE_PATH = Path(__file__).parent / "skill_embedding_cache.npz"

# Module-level singleton
_embedder: Optional["SkillEmbedder"] = None


class SkillEmbedder:
    """
    Wraps a SentenceTransformer model for skill-name semantic similarity.

    The model is loaded lazily on first use.
    Embeddings are cached in a dict so each skill is encoded only once per session.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._cache: dict[str, np.ndarray] = {}

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading SentenceTransformer model: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error("Failed to load SentenceTransformer: %s", e)
                self._model = None

    def encode_skill(self, skill_name: str) -> Optional[np.ndarray]:
        """
        Encode a skill name to a 384-dim float32 vector.
        Returns None if the model is unavailable.
        """
        key = skill_name.lower().strip()
        if key in self._cache:
            return self._cache[key]

        self._load_model()
        if self._model is None:
            return None

        try:
            vec = self._model.encode(key, normalize_embeddings=True)
            self._cache[key] = vec
            return vec
        except Exception as e:
            logger.warning("Embedding failed for '%s': %s", skill_name, e)
            return None

    def encode_batch(self, skill_names: list[str]) -> dict[str, np.ndarray]:
        """Encode a batch of skill names efficiently."""
        to_encode = [s for s in skill_names if s.lower() not in self._cache]

        if to_encode:
            self._load_model()
            if self._model:
                try:
                    vecs = self._model.encode(
                        [s.lower() for s in to_encode],
                        normalize_embeddings=True,
                        batch_size=64,
                        show_progress_bar=False,
                    )
                    for skill, vec in zip(to_encode, vecs):
                        self._cache[skill.lower()] = vec
                except Exception as e:
                    logger.warning("Batch encoding failed: %s", e)

        return {s: self._cache[s.lower()] for s in skill_names if s.lower() in self._cache}

    def cosine_similarity(self, skill_a: str, skill_b: str) -> float:
        """
        Compute cosine similarity between two skill names.
        Returns value in [0.0, 1.0]. Higher = more similar.
        Falls back to lexical/synonym heuristics if sentence-transformers is unavailable.
        """
        sa = (skill_a or "").lower().strip()
        sb = (skill_b or "").lower().strip()
        if not sa or not sb:
            return 0.0
        if sa == sb:
            return 1.0

        # ── Domain-specific curated tech skill adjacency dictionary ──
        adjacent_pairs = {
            ("fastapi", "flask"): 0.84, ("flask", "fastapi"): 0.84,
            ("postgresql", "mysql"): 0.79, ("mysql", "postgresql"): 0.79,
            ("react", "vue"): 0.78, ("vue", "react"): 0.78,
            ("react", "angular"): 0.72, ("angular", "react"): 0.72,
            ("docker", "kubernetes"): 0.75, ("kubernetes", "docker"): 0.75,
            ("aws", "gcp"): 0.80, ("gcp", "aws"): 0.80,
            ("aws", "azure"): 0.80, ("azure", "aws"): 0.80,
            ("pytorch", "tensorflow"): 0.85, ("tensorflow", "pytorch"): 0.85,
            ("pandas", "numpy"): 0.75, ("numpy", "pandas"): 0.75,
            ("django", "fastapi"): 0.75, ("fastapi", "django"): 0.75,
            ("django", "flask"): 0.80, ("flask", "django"): 0.80,
            ("c++", "c"): 0.85, ("c", "c++"): 0.85,
            ("java", "kotlin"): 0.80, ("kotlin", "java"): 0.80,
            ("javascript", "typescript"): 0.88, ("typescript", "javascript"): 0.88,
            ("mongodb", "postgresql"): 0.65, ("postgresql", "mongodb"): 0.65,
            ("linux", "bash"): 0.78, ("bash", "linux"): 0.78,
            ("machine learning", "deep learning"): 0.82, ("deep learning", "machine learning"): 0.82,
        }
        if (sa, sb) in adjacent_pairs:
            return adjacent_pairs[(sa, sb)]

        vec_a = self.encode_skill(skill_a)
        vec_b = self.encode_skill(skill_b)
        if vec_a is not None and vec_b is not None:
            raw_dot = float(np.dot(vec_a, vec_b))
            return max(0.0, min(1.0, round(raw_dot, 4)))

        if sa in sb or sb in sa:
            return 0.72

        return 0.0

    def find_similar_skills(
        self,
        query_skill: str,
        candidate_skills: list[str],
        top_k: int = 5,
        threshold: float = 0.6,
    ) -> list[tuple[str, float]]:
        """
        Find the most semantically similar skills to a query skill.
        Returns [(skill_name, similarity_score)] sorted descending.
        """
        query_vec = self.encode_skill(query_skill)
        if query_vec is None:
            return []

        candidate_vecs = self.encode_batch(candidate_skills)
        scores: list[tuple[str, float]] = []

        for skill, vec in candidate_vecs.items():
            sim = float(np.dot(query_vec, vec))
            if sim >= threshold:
                scores.append((skill, round(sim, 4)))

        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]

    def save_cache(self, path: Path = CACHE_PATH):
        """Persist embedding cache to disk as .npz."""
        if not self._cache:
            return
        keys = list(self._cache.keys())
        vecs = np.stack([self._cache[k] for k in keys])
        np.savez_compressed(path, keys=keys, vecs=vecs)
        logger.info("Saved %d embeddings to %s", len(keys), path)

    def load_cache(self, path: Path = CACHE_PATH):
        """Load persisted embedding cache from .npz."""
        if not path.exists():
            return
        try:
            data = np.load(path, allow_pickle=True)
            keys = data["keys"].tolist()
            vecs = data["vecs"]
            for k, v in zip(keys, vecs):
                self._cache[k] = v
            logger.info("Loaded %d cached embeddings from %s", len(keys), path)
        except Exception as e:
            logger.warning("Could not load embedding cache: %s", e)


def get_embedder() -> SkillEmbedder:
    """Get or create the module-level embedder singleton."""
    global _embedder
    if _embedder is None:
        _embedder = SkillEmbedder()
        _embedder.load_cache()
    return _embedder
