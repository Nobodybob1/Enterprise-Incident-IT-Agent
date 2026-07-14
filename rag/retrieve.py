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

def retrieve(query: str, top_k: int = 2):
    query_embedding = vo.embed([query], model=EMBED_MODEL, input_type="query").embeddings[0]

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k
    )

    return [
        {"filename": r.payload["filename"], "text": r.payload["text"], "score": r.score}
        for r in results.points
    ]

if __name__ == "__main__":
    # Manual test
    query = "server is not responding to requests"
    matches = retrieve(query)
    for m in matches:
        print(f"\n--- {m['filename']} (score: {m['score']:.3f})---")
        print(m["text"][:200], "...")