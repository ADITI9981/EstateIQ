
import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.ingest import load_property_data


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_DIR = PROJECT_ROOT / "vector_store"

INDEX_PATH = VECTOR_DIR / "estateiq.faiss"
METADATA_PATH = VECTOR_DIR / "metadata.json"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def build_vector_index():
    # Step 1: Load searchable property documents
    documents = load_property_data()

    if not documents:
        raise ValueError("No property documents found.")

    texts = [document["content"] for document in documents]

    # Step 2: Load the multilingual embedding model
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    # Step 3: Convert text into numerical vectors
    print("Generating embeddings...")
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    # Step 4: Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)

    # Step 5: Add embeddings to FAISS
    index.add(embeddings)

    # Step 6: Save index and associated metadata
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=4)

    print("\nVector index created successfully!")
    print(f"Documents indexed: {index.ntotal}")
    print(f"Embedding dimensions: {dimension}")
    print(f"Index saved at: {INDEX_PATH}")
    print(f"Metadata saved at: {METADATA_PATH}")


if __name__ == "__main__":
    build_vector_index()
