"""
Ingest runbooks + past incident tickets into a local Qdrant vector store.
Run this once (or whenever you add/change runbooks or tickets)
"""

import os
import json
import glob
import voyageai
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

load_dotenv()

RUNBOOKS_DIR = "data/runbooks"
INCIDENTS_PATH = "data/incidents.json"
COLLECTION_NAME = "runbooks"
EMBED_MODEL = "voyage-3"

vo = voyageai.Client()
qdrant = QdrantClient(path="qdrant_data") # Local on-disk store, no server needed

def load_runbooks():
    """
    Each file becomes one chunk - fine for short beginner runbooks.
    Later we could split long docs into smaller chunks.
    Runbooks aren'ttied to one specific service (they're symptom-based),
    so "service" is None - this makes them always eligible in retrieval's service filter,
    regardless of which service an inident triages to.
    """
    docs = []

    for filepath in glob.glob(f"{RUNBOOKS_DIR}/*.md"):
        with open(filepath, "r") as f:
            text = f.read()
        docs.append({"filename": os.path.basename(filepath), "text": text, "source": "runbook", "service": None})
    return docs

def load_incidents():
    """
    Each past ticket becomes one chunk, formatted as a short narrative
    (title + description + resolution) so it embeds comparably to a runbook's symptoms/resolution structure.
    Unlike runbooks, tickets ARE tied to one real service - that's stored as its own payload field
    (not just embedded in the text) so retrieval can filter on it directly.
    """

    docs = []
    if not os.path.exists(INCIDENTS_PATH):
        print(f"No incidents file found at {INCIDENTS_PATH}, skipping tickets.")
        return docs

    with open(INCIDENTS_PATH, "r") as f:
        tickets = json.load(f)

    for t in tickets:
        text = (
            f"Incident {t['ticket_id']} - {t['service']} ({t['date']})\n"
            f"{t['title']}\n\n"
            f"{t['description']}\n\n"
            f"Resolution: {t['resolution']}"
        )
        docs.append({"filename": t['ticket_id'], "text": text, "source": "ticket", "service": t["service"]})

    return docs

def main():
    docs = load_runbooks() + load_incidents()
    n_runbooks = sum(1 for d in docs if d["source"] == "runbook")
    n_incidents = sum(1 for d in docs if d["source"] == "ticket")
    print(f"Found {n_runbooks} runbooks and {n_incidents} past tickets to ingest.")

    texts = [d["text"] for d in docs]
    result = vo.embed(texts, model=EMBED_MODEL, input_type="document")
    embeddings = result.embeddings

    # Create the collection (deletes and recreates if it already exists)
    if qdrant.collection_exists(COLLECTION_NAME):
        qdrant.delete_collection(COLLECTION_NAME)
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE)
    )

    points = [
        PointStruct(
            id=i,
            vector=embeddings[i],
            payload={"filename": docs[i]["filename"], 
                     "text": docs[i]["text"], 
                     "source": docs[i]["source"],
                     "service": docs[i]["service"]
                }
        )
        for i in range(len(docs))
    ]
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Ingested {len(points)} documents into Qdrant collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    main()