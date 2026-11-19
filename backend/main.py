
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.retriever import PropertyRetriever
from backend.llm import generate_answer


# Initialize FastAPI
app = FastAPI(
    title="EstateIQ API",
    description="AI-powered real estate assistant using RAG",
    version="1.0.0"
)

# Load retriever once
retriever = PropertyRetriever()


# Request structure
class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Ask a real estate question"
    )


# Response structure
class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]


def extract_cited_sources(answer, retrieved_results):
    """
    Return only URLs cited in the AI answer
    that belong to the retrieved documents.
    """

    retrieved_urls = {
        result["metadata"].get("source_url")
        for result in retrieved_results
        if result["metadata"].get("source_url")
    }

    # Extract URLs from the generated answer
    cited_urls = re.findall(
        r"https?://[^\s<>\"']+",
        answer
    )

    # Remove trailing punctuation
    cited_urls = [
        url.rstrip(".,;:!?)")
        for url in cited_urls
    ]

    # Keep only URLs belonging to retrieved documents
    relevant_sources = []
    seen = set()

    for url in cited_urls:
        if url in retrieved_urls and url not in seen:
            relevant_sources.append(url)
            seen.add(url)

    return relevant_sources


@app.get("/")
def home():
    return {
        "message": "Welcome to EstateIQ API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "EstateIQ"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        # Step 1: Retrieve relevant documents
        results = retriever.search(
            request.question,
            top_k=3
        )

        # Step 2: Generate AI answer
        answer = generate_answer(
            request.question,
            results
        )

        # Step 3: Extract relevant cited sources
        sources = extract_cited_sources(
            answer,
            results
        )

        # Step 4: Return response
        return ChatResponse(
            question=request.question,
            answer=answer,
            sources=sources
        )

    except Exception as error:
        print(f"Chat API error: {type(error).__name__}: {error}")

        raise HTTPException(
            status_code=503,
            detail="EstateIQ is temporarily unable to process your request. Please try again."
        )
