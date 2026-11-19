
import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_DIR = PROJECT_ROOT / "vector_store"

INDEX_PATH = VECTOR_DIR / "estateiq.faiss"
METADATA_PATH = VECTOR_DIR / "metadata.json"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class PropertyRetriever:

    def __init__(self):
        print("Loading vector index...")
        self.index = faiss.read_index(str(INDEX_PATH))

        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            self.documents = json.load(file)

        print("Loading embedding model...")
        self.model = SentenceTransformer(MODEL_NAME)

        print("Property retriever is ready!")

    def infer_filters(self, query):
        """
        Identify explicit filters from the user's question.
        """

        query_lower = query.lower()

        filters = {}

        # Source filtering
        if "darglobal" in query_lower:
            filters["source"] = "DarGlobal"

        elif "wasalt" in query_lower:
            filters["source"] = "Wasalt"

        # Document type filtering
        property_terms = [
            "villa", "apartment", "flat", "bedroom",
            "bathroom", "rental", "rent", "property listing"
        ]

        development_terms = [
            "development project", "developer project",
            "darglobal project", "projects", "development"
        ]

        if any(term in query_lower for term in property_terms):
            filters["document_type"] = "property"

        elif any(term in query_lower for term in development_terms):
            filters["document_type"] = "development"

        # Project status filtering
        if "under development" in query_lower:
            filters["status"] = "Under Development"

        elif "announced" in query_lower:
            filters["status"] = "Announced"

        return filters

    def matches_filters(self, metadata, filters):
        """
        Check whether a document satisfies all inferred filters.
        """

        for field, expected_value in filters.items():

            actual_value = metadata.get(field)

            if actual_value is None:
                return False

            if str(actual_value).lower() != str(expected_value).lower():
                return False

        return True

    def search(self, query, top_k=3):
        """
        Perform semantic search with metadata filtering.
        """

        if not query or not query.strip():
            return []

        # Convert the question into an embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        # Search all available documents
        total_documents = len(self.documents)

        scores, indices = self.index.search(
            query_embedding,
            total_documents
        )

        # Infer filters from the question
        filters = self.infer_filters(query)

        results = []

        for score, index in zip(scores[0], indices[0]):

            if index == -1:
                continue

            document = self.documents[index]
            metadata = document["metadata"]

            # Apply metadata filters
            if not self.matches_filters(metadata, filters):
                continue

            results.append({
                "similarity_score": float(score),
                "content": document["content"],
                "metadata": metadata
            })

        # Sort by semantic similarity
        results.sort(
            key=lambda item: item["similarity_score"],
            reverse=True
        )

        return results[:top_k]


if __name__ == "__main__":

    retriever = PropertyRetriever()

    questions = [
        "What is The Astera and where is it located?",
        "What is DarGlobal developing in Jeddah?",
        "Find a 9-bedroom villa in Riyadh",
        "Which DarGlobal projects are under development?"
    ]

    for question in questions:

        print("\n" + "=" * 60)
        print("Question:", question)

        results = retriever.search(question, top_k=3)

        if not results:
            print("No matching documents found.")
            continue

        for result in results:

            print("\nSource:", result["metadata"].get("source"))
            print("Project/Property:", result["metadata"].get("title"))
            print("Status:", result["metadata"].get("status"))
            print("Similarity:", round(result["similarity_score"], 4))
