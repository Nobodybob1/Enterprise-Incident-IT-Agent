"""
Retrieve relevant runbook chunks and past incident tickets for a query.
"""

from typing import Optional
import voyageai
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "runbooks"
EMBED_MODEL = "voyage-3"

vo = voyageai.Client()
qdrant = QdrantClient(path="qdrant_data")

def _build_filter(service_name: Optional[str]):
    runbook_clause = FieldCondition(key="source", match=MatchValue(value="runbook"))

    if not service_name or service_name == "unknown":
        return Filter(must=[runbook_clause])

    ticket_clause = Filter(
        must=[
            FieldCondition(key="source", match=MatchValue(value="ticket")),
            FieldCondition(key="service", match=MatchValue(value=service_name))
        ]
    )
    return Filter(should=[runbook_clause, ticket_clause])

def retrieve(query: str, service_name: Optional[str] = None, top_k: int = 3, min_score: float = 0.3):
    query_embedding = vo.embed([query], model=EMBED_MODEL, input_type="query").embeddings[0]

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=_build_filter(service_name),
        limit=top_k
    )

    matches = [
        {
            "filename": r.payload["filename"], 
            "text": r.payload["text"], 
            "source": r.payload.get("source", "runbook"),
            "score": r.score}
        for r in results.points
        if r.score >= min_score
    ]
    return matches

if __name__ == "__main__":
    # Manual test
    query = "server is not responding to requests"
    matches = retrieve(query, service_name="nginx")
    for m in matches:
        print(f"\n--- [{m['source']}] {m['filename']} (score: {m['score']:.3f})---")
        print(m["text"][:200], "...")