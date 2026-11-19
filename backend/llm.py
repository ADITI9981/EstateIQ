
import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY is missing from .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    timeout=45.0,
    max_retries=0,
    default_headers={
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "EstateIQ"
    }
)


def generate_answer(question, retrieved_properties):

    if not retrieved_properties:
        return "I couldn't find a matching property in the available data."

    context_parts = []

    for index, result in enumerate(retrieved_properties, start=1):
        metadata = result["metadata"]

        context_parts.append(f"""
Property {index}:
{result["content"]}

Source: {metadata.get("source_url")}
Data retrieved at: {metadata.get("retrieved_at_utc")}
""")

    context = "\n".join(context_parts)

    system_prompt = """
You are EstateIQ, an accurate and helpful AI real estate assistant.

Answer real estate questions using ONLY the supplied property information.

STRICT ACCURACY RULES:

1. Use retrieved property context as your source of truth.
   Never invent prices, locations, property features, availability,
   payment terms, or project information.

2. PAYMENT OPTIONS:
   - Distinguish one-payment and two-payment prices.
   - Use "One Payment Option" for one payment.
   - Use "Two Payments Option" for two payments.
   - Never substitute the general listed price for a specific option.
   - If payment details conflict, explain the discrepancy.
   - Never invent installment dates or amounts per installment.

3. PROPERTY DETAILS:
   - Distinguish bedrooms from bathrooms.
   - If a detail is missing, say it is not specified.

4. PROJECT DETAILS:
   - Distinguish announced projects from projects under development.
   - Never describe announced plans as completed developments.

5. ANSWER FORMAT:
   - Answer the exact question first.
   - Use the currency provided in the context.
   - Include the rental period when discussing rent.
   - Be concise, clear, and professional.

6. SOURCE AND VERIFICATION:
   - Include the original source URL when available.
   - Explain that prices and availability can change.

7. If information is missing, clearly say so.

Do not use outside knowledge to fill gaps in the supplied data.
"""

    user_prompt = f"""
Retrieved property and project information:

{context}

User question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            extra_body={
                "models": [
                    "inclusionai/ling-3.2-flash:free",
                    "nvidia/nemotron-3.5-lightning:free"
                ]
            }
        )

        print("Model used:", response.model)

        return response.choices[0].message.content

    except Exception as error:
        print(f"OpenRouter error: {type(error).__name__}: {error}")
        raise


if __name__ == "__main__":

    from backend.retriever import PropertyRetriever

    retriever = PropertyRetriever()

    question = "Tell me about the 9-bedroom villa in Riyadh."

    properties = retriever.search(question)

    answer = generate_answer(question, properties)

    print("\nEstateIQ AI Response:\n")
    print(answer)
