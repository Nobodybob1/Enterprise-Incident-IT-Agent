"""
Ingest runbooks into a local Qdrant vector store.
Run this once (or whenever you add/change runbooks)
"""

import os
import glob
import voyageai
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

load_dotenv()

RUNBOOKS_DIR = "data/runbooks"
COLLECTION_NAME = "runbooks"
EMBED_MODEL = "voyage-3"

vo = voyageai.Client()
qdrant = QdrantClient(path="qdrant_data") # Local on-disk store, no server needed

def load_runbooks():
    """
    Each file becomes one chunk - fine for short beginned runbooks.
    Later we could split long docs into smalled chunks
    """
    docs = []

    for filepath in glob.glob(f"{RUNBOOKS_DIR}/*.md"):
        with open(filepath, "r") as f:
            text = f.read()
        docs.append({"filename": os.path.basename(filepath), "text": text})
    return docs

def main():
    docs = load_runbooks()
    print (f"Found {len(docs)} runbooks to ingest.")

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
            payload={"filename": docs[i]["filename"], "text": docs[i]["text"]},
        )
        for i in range(len(docs))
    ]
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Ingested {len(points)} runbooks into Qdrant collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    main()