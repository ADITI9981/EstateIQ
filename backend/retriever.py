
import json
from pathlib import Path

import joblib
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_DIR = PROJECT_ROOT / "vector_store"

VECTORIZER_PATH = VECTOR_DIR / "tfidf_vectorizer.joblib"
MATRIX_PATH = VECTOR_DIR / "tfidf_matrix.npz"
METADATA_PATH = VECTOR_DIR / "metadata.json"


class PropertyRetriever:

    def __init__(self):
        print("Loading TF-IDF index...")

        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(
                "TF-IDF vectorizer not found. Run python -m backend.indexer first."
            )

        if not MATRIX_PATH.exists():
            raise FileNotFoundError(
                "TF-IDF matrix not found. Run python -m backend.indexer first."
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                "Document metadata not found. Run python -m backend.indexer first."
            )

        self.vectorizer = joblib.load(VECTORIZER_PATH)
        self.matrix = load_npz(MATRIX_PATH)

        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            self.documents = json.load(file)

        if self.matrix.shape[0] != len(self.documents):
            raise ValueError(
                "TF-IDF matrix and document metadata counts do not match."
            )

        print("Property retriever is ready!")
        print(f"Documents available: {len(self.documents)}")
    def infer_filters(self, query):
        """Identify explicit filters from the user's question."""

        query_lower = query.lower()
        filters = {}

        # Source filtering
        if "darglobal" in query_lower:
            filters["source"] = "DarGlobal"
        elif "wasalt" in query_lower:
            filters["source"] = "Wasalt"

        # Property listing keywords
        property_terms = [
            "available properties",
            "available property",
            "property listing",
            "property listings",
            "properties",
            "property",
            "villa",
            "apartment",
            "flat",
            "bedroom",
            "bathroom",
            "rental",
            "rent",
            "for sale",
            "for rent"
       ]

        # Development project keywords
        development_terms = [
            "development project",
            "developer project",
            "darglobal project",
            "projects",
            "development"
       ]

        # Identify document type
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
        """Check whether a document satisfies all inferred filters."""

        for field, expected_value in filters.items():
            actual_value = metadata.get(field)

            if actual_value is None:
                return False

            if str(actual_value).lower() != str(expected_value).lower():
                return False

        return True
    def search(self, query, top_k=3):
        """Retrieve exact matches first and support broad listing queries."""

        if not query or not query.strip():
            return []

        query_lower = query.lower().strip()

        # Apply metadata filters
        filters = self.infer_filters(query)

        # Detect broad listing requests
        broad_query_terms = [
            "show me",
            "list all",
            "all projects",
            "all properties",
            "available projects",
            "available properties",
            "what projects",
            "which projects",
            "dar global projects",
            "darglobal projects",
            "wasalt properties",
        ]

        is_broad_query = any(
            term in query_lower for term in broad_query_terms
        )

        # Broad queries should return all matching indexed records
        result_limit = len(self.documents) if is_broad_query else top_k

        # Exact project/property name matching
        exact_matches = []

        for document in self.documents:
            metadata = document["metadata"]
            title = metadata.get("title", "").lower().strip()

            if not title:
                continue

            if title in query_lower:
                if self.matches_filters(metadata, filters):
                    exact_matches.append({
                        "similarity_score": 1.0,
                        "content": document["content"],
                        "metadata": metadata
                    })

        # Return exact matches before semantic search
        if exact_matches:
            return exact_matches[:result_limit]

        # Normal TF-IDF search
        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            self.matrix
        ).flatten()

        results = []

        for document_index, score in enumerate(scores):

            if score <= 0:
                continue

            document = self.documents[document_index]
            metadata = document["metadata"]

            if not self.matches_filters(metadata, filters):
                continue

            results.append({
                "similarity_score": float(score),
                "content": document["content"],
                "metadata": metadata
            })

        results.sort(
            key=lambda item: item["similarity_score"],
            reverse=True
        )

        return results[:result_limit]



if __name__ == "__main__":

    retriever = PropertyRetriever()

    questions = [
        "What is The Astera and where is it located?",
        "What is DarGlobal developing in Jeddah?",
        "Find a 9-bedroom villa in Riyadh",
        "Which DarGlobal projects are under development?",
        "Tell me about Da Vinci Tower by Pagani",
        "What is Urban Oasis by Missoni?"
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
