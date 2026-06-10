import numpy as np
from typing import List

def generate_style_embedding(text_or_tags: List[str]) -> List[float]:
    """
    Placeholder for real style embedding generation.
    In a real app, this would use a model like Sentence-BERT or Vertex AI Embeddings.
    Returns a 128-dimensional unit-normalized random vector.
    """
    embedding = np.random.rand(128).astype(np.float32)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding.tolist()
