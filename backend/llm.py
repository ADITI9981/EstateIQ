
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

# OpenRouter is optional because EstateIQ has a local fallback.
client = None

if API_KEY:
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



def generate_local_answer(question, retrieved_properties):
    """Generate a clean, structured response from indexed records."""

    if not retrieved_properties:
        return (
            "I couldn't find matching information in the available "
            "DarGlobal and Wasalt records. Please try another question."
        )

    answer_parts = [
        "Here is what I found in EstateIQ's available records:"
    ]

    for index, result in enumerate(retrieved_properties, start=1):
        metadata = result.get("metadata", {})
        content = result.get("content", "")

        title = metadata.get("title") or f"Record {index}"
        source = metadata.get("source")
        source_url = metadata.get("source_url")
        document_type = metadata.get("document_type")
        property_type = metadata.get("property_type")
        location = metadata.get("location")

        answer_parts.append(f"\n## {index}. {title}")

        if document_type == "property":
            if property_type:
                answer_parts.append(f"Property type: {property_type}")

            transaction = metadata.get("transaction_type")
            if transaction:
                answer_parts.append(f"Transaction: {transaction}")

            if location:
                answer_parts.append(f"Location: {location}")

            bedrooms = metadata.get("bedrooms")
            if bedrooms is not None:
                answer_parts.append(f"Bedrooms: {bedrooms}")

            # Bathrooms and area are currently stored in document content.
            bathrooms = re.search(r"Bathrooms:\s*(\d+)", content)
            if bathrooms:
                answer_parts.append(f"Bathrooms: {bathrooms.group(1)}")

            area = re.search(
                r"Area:\s*([\d.]+)\s*square meters", content, re.IGNORECASE
            )
            if area:
                answer_parts.append(f"Area: {area.group(1)} square meters")

            # Display payment options separately.
            payment_options = metadata.get("payment_options")

            if payment_options:
                currency = payment_options.get("currency", "Currency not specified")
                period = payment_options.get("period", "")

                answer_parts.append("\nRental / Payment details:")

                one_payment = payment_options.get("one_payment")
                two_payments = payment_options.get("two_payments")

                if one_payment is not None:
                    answer_parts.append(
                        f"One Payment Option: {one_payment:,.0f} "
                        f"{currency} per {period}"
                    )

                if two_payments is not None:
                    answer_parts.append(
                        f"Two Payments Option: {two_payments:,.0f} "
                        f"{currency} per {period}"
                    )

            elif metadata.get("price") is not None:
                price = metadata["price"]
                currency = metadata.get("price_currency") or ""
                period = metadata.get("price_period") or ""

                answer_parts.append(
                    f"Listed Price: {price:,.0f} {currency} {period}".strip()
                )

        elif document_type == "development":
            if location:
                answer_parts.append(f"Location: {location}")

            if property_type:
                answer_parts.append(f"Development type: {property_type}")

            status = metadata.get("status")
            if status:
                answer_parts.append(f"Project status: {status}")
            else:
                answer_parts.append(
                    "Project status: Not specified in the available records."
                )

            completion = metadata.get("expected_completion")
            if completion:
                answer_parts.append(f"Expected completion: {completion}")

            collection_method = metadata.get("collection_method")
            if collection_method:
                answer_parts.append(
                    f"Data collection: {collection_method}"
                )

        if source:
            answer_parts.append(f"\nSource: {source}")

        if source_url:
            answer_parts.append(f"Source URL: {source_url}")

    answer_parts.append(
        "\nNote: This response is generated from EstateIQ's indexed records "
        "without an external AI model. Some project details may be "
        "unavailable. Prices and availability can change; verify them "
        "with the original source."
    )

    return "\n".join(answer_parts)


def generate_answer(question, retrieved_properties):

    if not retrieved_properties:
        return generate_local_answer(question, retrieved_properties)

    if client is None:
        print("OpenRouter API key unavailable. Using local response.")
        return generate_local_answer(question, retrieved_properties)

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

        answer = response.choices[0].message.content

        if answer:
            print("Model used:", response.model)
            return answer

        print("OpenRouter returned an empty answer. Using local response.")
        return generate_local_answer(question, retrieved_properties)

    except Exception as error:
        print(f"OpenRouter error: {type(error).__name__}: {error}")
        print("Switching to local response generation.")
        return generate_local_answer(question, retrieved_properties)


if __name__ == "__main__":

    from backend.retriever import PropertyRetriever

    retriever = PropertyRetriever()

    question = "Tell me about the 9-bedroom villa in Riyadh."

    properties = retriever.search(question)

    answer = generate_answer(question, properties)

    print("\nEstateIQ Response:\n")
    print(answer)
