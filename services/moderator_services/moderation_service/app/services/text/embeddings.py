"""
Embeddings Module (Rewritten)
=============================

Step 4 & 5: Semantic embedding + FAISS similarity search
"""

from typing import Dict, List, Optional
from .models import ViolationType


class SemanticEncoder:
    """Step 4: Semantic embedding using Sentence Transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = None
        self.model_name = model_name
        self.dimension = None
        self._load_model()

    def _load_model(self):
        """Load sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

            # get embedding dimension dynamically
            self.dimension = self.model.get_sentence_embedding_dimension()

            print(f"✓ Transformer loaded: {self.model_name} (dim={self.dimension})")

        except Exception as e:
            print(f"⚠ Transformer unavailable: {e}")

    def encode(self, text: str) -> Optional[List[float]]:
        """Encode a single text"""
        if not self.model or not text:
            return None

        try:
            emb = self.model.encode(text, convert_to_numpy=True)
            return emb.tolist()
        except Exception as e:
            print(f"⚠ Encoding error: {e}")
            return None

    def encode_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Encode batch texts"""
        if not self.model or not texts:
            return None

        try:
            embs = self.model.encode(texts, convert_to_numpy=True)
            return embs.tolist()
        except Exception as e:
            print(f"⚠ Batch encoding error: {e}")
            return None


class VectorDatabase:
    """Step 5: FAISS vector similarity search"""

    def __init__(
        self,
        encoder: SemanticEncoder,
        similarity_threshold: float = 0.70,
        preload_patterns: bool = True,
    ):
        self.encoder = encoder
        self.index = None
        self.dimension = encoder.dimension
        self.similarity_threshold = similarity_threshold
        self.violation_texts: List[str] = []
        self.violation_labels: List[ViolationType] = []
        self._initialize()

        if preload_patterns:
            self._load_and_index_patterns()

    # -----------------------------
    # FAISS initialization
    # -----------------------------

    def _initialize(self):
        """Init FAISS index"""
        if not self.dimension:
            print("⚠ No embedding dimension - FAISS disabled")
            return

        try:
            import faiss
            self.index = faiss.IndexFlatL2(self.dimension)
            print(f"✓ FAISS index initialized (dim={self.dimension})")
        except ImportError:
            print("⚠ FAISS not available -> vector search disabled")
        except Exception as e:
            print(f"⚠ FAISS init error: {e}")

    # -----------------------------
    # Pattern loading + encoding
    # -----------------------------

    def _load_violation_patterns(self):
        """Raw “seed” patterns before embedding"""

        self.violation_texts = [
            # weapons
            "buy guns cheap firearms for sale",
            "sell weapons illegally black market",
            "assault rifles ammunition available",
            "handguns pistols revolvers for sale",

            # drugs
            "drugs for sale cocaine heroin meth",
            "buy marijuana weed cannabis online",
            "prescription pills opioids available",
            "drug dealer fast delivery discrete",

            # scams
            "get rich quick guaranteed returns",
            "double your money investment opportunity",
            "wire transfer western union urgent",
            "lottery winner inheritance claim now",
            "miracle weight loss lose pounds fast",
            "work from home make thousands daily",

            # sexual
            "escort services girls available call",
            "adult entertainment sexual services",
            "nude pictures videos onlyfans content",
            "massage happy ending full service",

            # violence
            "kill someone murder for hire",
            "beat hurt attack assault revenge",
            "torture harm violence threat",
            "looking to hire hitman",

            # hate
            "hate foreigners racist movement",
            "kill jews muslims destroy them",
            "white power nazi supremacy",
            "racial slurs discriminate",

            # illegal
            "stolen items no receipts cheap",
            "fake documents passport identity",
            "counterfeit money credit cards",
            "hack accounts passwords data",
            "human trafficking exploitation",
            "pirated software movies illegal",

            # spam
            "click here urgent act now limited",
            "amazing deal buy now dont miss",
            "free money guaranteed winner",
        ]

        self.violation_labels = [
            ViolationType.WEAPONS, ViolationType.WEAPONS,
            ViolationType.WEAPONS, ViolationType.WEAPONS,

            ViolationType.DRUGS, ViolationType.DRUGS,
            ViolationType.DRUGS, ViolationType.DRUGS,

            ViolationType.SCAM, ViolationType.SCAM,
            ViolationType.SCAM, ViolationType.SCAM,
            ViolationType.SCAM, ViolationType.SCAM,

            ViolationType.SEXUAL, ViolationType.SEXUAL,
            ViolationType.SEXUAL, ViolationType.SEXUAL,

            ViolationType.VIOLENCE, ViolationType.VIOLENCE,
            ViolationType.VIOLENCE, ViolationType.VIOLENCE,

            ViolationType.HATE_SPEECH, ViolationType.HATE_SPEECH,
            ViolationType.HATE_SPEECH, ViolationType.HATE_SPEECH,

            ViolationType.ILLEGAL, ViolationType.ILLEGAL,
            ViolationType.ILLEGAL, ViolationType.ILLEGAL,
            ViolationType.ILLEGAL, ViolationType.ILLEGAL,

            ViolationType.SPAM, ViolationType.SPAM, ViolationType.SPAM,
        ]

    def _load_and_index_patterns(self):
        """Encode + add patterns at startup"""
        if not self.index:
            return

        self._load_violation_patterns()

        embeddings = self.encoder.encode_batch(self.violation_texts)
        if not embeddings:
            print("⚠ Pattern embedding failed")
            return

        self.add_vectors(embeddings, self.violation_labels)
        print(f"✓ Preloaded {len(embeddings)} violation vectors")

    # -----------------------------
    # Runtime FAISS operations
    # -----------------------------

    def add_vectors(self, vectors: List[List[float]], labels: List[ViolationType]):
        """Add vectors to FAISS index"""
        if not self.index:
            return

        import numpy as np
        self.index.add(np.array(vectors, dtype=np.float32))
        self.violation_labels.extend(labels)

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search nearest vectors + return structured result"""

        if not self.index:
            return []
        if not query_embedding:
            return []

        try:
            import numpy as np

            query = np.array([query_embedding], dtype=np.float32)
            distances, indices = self.index.search(query, min(k, self.index.ntotal))

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.violation_labels):
                    continue

                similarity = 1.0 / (1.0 + dist)  # L2 → similarity score

                if similarity < self.similarity_threshold:
                    continue  # ignore weak matches

                results.append({
                    "similarity": similarity,
                    "distance": float(dist),
                    "violation_type": self.violation_labels[idx].value,
                    "reference_text": self.violation_texts[idx],
                })

            return results

        except Exception as e:
            print(f"⚠ Vector search error: {e}")
            return []
