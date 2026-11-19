
import json
from pathlib import Path

import numpy as np
import joblib
from scipy.sparse import save_npz
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.ingest import load_property_data


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_DIR = PROJECT_ROOT / "vector_store"

VECTORIZER_PATH = VECTOR_DIR / "tfidf_vectorizer.joblib"
MATRIX_PATH = VECTOR_DIR / "tfidf_matrix.npz"
METADATA_PATH = VECTOR_DIR / "metadata.json"


def build_vector_index():
    # Step 1: Load searchable documents
    documents = load_property_data()

    if not documents:
        raise ValueError("No property documents found.")

    texts = [
        document["content"]
        for document in documents
    ]

    # Step 2: Create a multilingual-friendly character TF-IDF vectorizer
    print("Creating TF-IDF vectorizer...")

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
        max_features=100000,
        sublinear_tf=True,
        dtype=np.float32
    )

    # Step 3: Convert documents into sparse numerical vectors
    print("Generating TF-IDF matrix...")

    matrix = vectorizer.fit_transform(texts)

    # Step 4: Save index and metadata
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(vectorizer, VECTORIZER_PATH)
    save_npz(MATRIX_PATH, matrix)

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\nTF-IDF index created successfully!")
    print(f"Documents indexed: {matrix.shape[0]}")
    print(f"Features generated: {matrix.shape[1]}")
    print(f"Vectorizer saved at: {VECTORIZER_PATH}")
    print(f"Matrix saved at: {MATRIX_PATH}")
    print(f"Metadata saved at: {METADATA_PATH}")


if __name__ == "__main__":
    build_vector_index()
