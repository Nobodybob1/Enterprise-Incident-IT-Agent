"""
Retrieve relevant runbook chunks for a query
"""

import voyageai
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "runbooks"
EMBED_MODEL = "voyage-3"

vo = voyageai.Client()
qdrant = QdrantClient(path="qdrant_data")

def retrieve(query: str, top_k: int = 2, min_score: float = 0.3):
    query_embedding = vo.embed([query], model=EMBED_MODEL, input_type="query").embeddings[0]

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k
    )

    matches = [
        {"filename": r.payload["filename"], "text": r.payload["text"], "source": r.payload.get("source", "runbook"),"score": r.score} # Backward compatible with old points.
        for r in results.points
        if r.score >= min_score
    ]
    return matches

if __name__ == "__main__":
    # Manual test
    query = "server is not responding to requests"
    matches = retrieve(query)
    for m in matches:
        print(f"\n--- {m['filename']} (score: {m['score']:.3f})---")
        print(m["text"][:200], "...")