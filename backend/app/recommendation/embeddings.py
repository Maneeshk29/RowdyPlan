"""
Embedding Service for Rowdy Plan Recommendation Engine.

Generates semantic embeddings using sentence-transformers,
with fallback to random vectors for testing when the model is unavailable.
"""

import logging
import threading
import hashlib

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Singleton embedding service using sentence-transformers.

    Falls back to deterministic pseudo-random vectors when
    sentence-transformers is not installed or the model fails to load.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instance = instance
            return cls._instance

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if self._initialized:
            return
        self._model_name = model_name
        self._model = None
        self._use_fallback = False
        self._embedding_dim = 384  # Default for all-MiniLM-L6-v2
        self._initialized = True

    def _load_model(self):
        """Lazy-load the sentence-transformers model."""
        if self._model is not None or self._use_fallback:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.info(
                "Loaded sentence-transformers model: %s (dim=%d)",
                self._model_name,
                self._embedding_dim,
            )
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Using deterministic fallback vectors for testing."
            )
            self._use_fallback = True
        except Exception as e:
            logger.warning(
                "Failed to load model '%s': %s. Using fallback vectors.",
                self._model_name,
                str(e),
            )
            self._use_fallback = True

    def _fallback_vector(self, text: str) -> np.ndarray:
        """
        Generate a deterministic pseudo-random vector from text.
        Uses SHA-256 hash to seed numpy RNG for reproducibility.
        """
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        seed = int(text_hash[:8], 16)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self._embedding_dim).astype(np.float64)
        # Normalize to unit vector
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text string.

        Args:
            text: Input text to embed.

        Returns:
            numpy array of shape (embedding_dim,).
        """
        self._load_model()

        if self._use_fallback:
            return self._fallback_vector(text)

        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float64)

    def encode_batch(self, texts: list[str]) -> list[np.ndarray]:
        """
        Batch encode multiple texts.

        Args:
            texts: List of input texts.

        Returns:
            List of numpy arrays, one per input text.
        """
        self._load_model()

        if self._use_fallback:
            return [self._fallback_vector(t) for t in texts]

        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return [emb.astype(np.float64) for emb in embeddings]

    def compute_similarity(
        self, vec_a: np.ndarray, vec_b: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec_a: First vector.
            vec_b: Second vector.

        Returns:
            Cosine similarity score in [-1, 1].
        """
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    def build_student_embedding(self, profile: dict) -> np.ndarray:
        """
        Build a single embedding representing the student by combining
        their profile information into a descriptive text.

        Args:
            profile: Normalized student profile dict.

        Returns:
            numpy array embedding.
        """
        parts = []

        if profile.get("major"):
            parts.append(f"Major: {profile['major']}")

        if profile.get("career_goal"):
            parts.append(f"Career goal: {profile['career_goal']}")

        skills = profile.get("skills", [])
        if skills:
            parts.append(f"Skills: {', '.join(skills[:20])}")

        langs = profile.get("programming_languages", [])
        if langs:
            parts.append(f"Programming: {', '.join(langs[:10])}")

        experience = profile.get("experience", [])
        if experience:
            exp_descriptions = []
            for exp in experience[:5]:
                title = exp.get("title", "")
                company = exp.get("company", "")
                if title:
                    exp_descriptions.append(f"{title} at {company}" if company else title)
            if exp_descriptions:
                parts.append(f"Experience: {'; '.join(exp_descriptions)}")

        interests = profile.get("career_interests", [])
        if interests:
            parts.append(f"Interests: {', '.join(interests[:10])}")

        industries = profile.get("industries", [])
        if industries:
            parts.append(f"Industries: {', '.join(industries[:5])}")

        coursework = profile.get("coursework", [])
        if coursework:
            parts.append(f"Courses: {', '.join(coursework[:10])}")

        text = ". ".join(parts) if parts else "Student profile"
        return self.encode(text)

    def build_opportunity_embedding(self, opportunity: dict) -> np.ndarray:
        """
        Build a single embedding for an opportunity (job, event, etc.)
        by combining its description, skills, and requirements.

        Args:
            opportunity: Opportunity dict with title, description, skills, etc.

        Returns:
            numpy array embedding.
        """
        parts = []

        if opportunity.get("title"):
            parts.append(opportunity["title"])

        if opportunity.get("description"):
            # Truncate long descriptions
            desc = opportunity["description"][:500]
            parts.append(desc)

        if opportunity.get("organization"):
            parts.append(f"Organization: {opportunity['organization']}")

        required_skills = opportunity.get("required_skills", [])
        if required_skills:
            parts.append(f"Required skills: {', '.join(required_skills[:15])}")

        preferred_skills = opportunity.get("preferred_skills", [])
        if preferred_skills:
            parts.append(f"Preferred skills: {', '.join(preferred_skills[:10])}")

        if opportunity.get("location"):
            parts.append(f"Location: {opportunity['location']}")

        if opportunity.get("type"):
            parts.append(f"Type: {opportunity['type']}")

        text = ". ".join(parts) if parts else "Opportunity"
        return self.encode(text)

    @classmethod
    def reset(cls):
        """Reset singleton instance (useful for testing)."""
        with cls._lock:
            cls._instance = None
