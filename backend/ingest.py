
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_json_records(file_path):
    """Load either one JSON record or a list of records."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    return [data]


def format_location(location):
    """Support both dictionary and string locations."""
    if isinstance(location, dict):
        return ", ".join(
            str(value)
            for value in location.values()
            if value and value != "Unknown"
        )

    return str(location or "Unknown")


def load_property_data():
    """Load and normalize property listings and development projects."""

    documents = []

    for file_path in RAW_DATA_DIR.glob("*.json"):
        records = load_json_records(file_path)

        for record in records:
            document_type = record.get("document_type", "property")
            location = format_location(record.get("location"))

            if document_type == "development":
                content = f"""
                Document Type: Real Estate Development
                Project: {record.get('title', 'Unknown')}
                Developer: {record.get('developer', 'Unknown')}
                Property Type: {record.get('property_type', 'Unknown')}
                Location: {location}
                Status: {record.get('status', 'Unknown')}
                Unit Types: {record.get('unit_types', 'Unknown')}
                Bedrooms: {record.get('bedrooms', 'Not specified')}
                Area: {record.get('area_sqm', 'Not specified')}
                Expected Completion: {record.get('expected_completion', 'Not specified')}
                Gross Development Value: {record.get('gross_development_value', 'Not disclosed')}
                Description: {record.get('description', '')}
                Additional Details: {record.get('additional_details', '')}
                """

            else:
                payment_options = record.get("payment_options", {})

                one_payment = payment_options.get(
                    "one_payment", "Not specified"
                )
                two_payments = payment_options.get(
                    "two_payments", "Not specified"
                )
                payment_currency = payment_options.get(
                    "currency", record.get("price_currency", "Unknown")
                )
                payment_period = payment_options.get(
                    "period", record.get("price_period", "Unknown")
                )

                content = f"""
                Document Type: Property Listing
                Property: {record.get('title', 'Unknown')}
                Property Type: {record.get('property_type', 'Unknown')}
                Transaction: {record.get('transaction_type', 'Unknown')}
                Location: {location}
                Bedrooms: {record.get('bedrooms', 'Unknown')}
                Bathrooms: {record.get('bathrooms', 'Unknown')}
                Area: {record.get('area_sqm', 'Unknown')} square meters
                Listed Price: {record.get('price', 'Unknown')}
                Currency: {record.get('price_currency', 'Unknown')}
                Rental Period: {record.get('price_period', 'Unknown')}
                One Payment Option: {one_payment} {payment_currency} per {payment_period}
                Two Payments Option: {two_payments} {payment_currency} per {payment_period}
                Description: {record.get('description', '')}
                """

            metadata = {
                "document_type": document_type,
                "source": record.get("source"),
                "source_url": record.get("source_url"),
                "listing_id": record.get("listing_id"),
                "project_id": record.get("project_id"),
                "title": record.get("title"),
                "property_type": record.get("property_type"),
                "transaction_type": record.get("transaction_type"),
                "location": location,
                "city": (
                    record.get("location", {}).get("city")
                    if isinstance(record.get("location"), dict)
                    else None
                ),
                "country": (
                    record.get("location", {}).get("country")
                    if isinstance(record.get("location"), dict)
                    else None
                ),
                "bedrooms": record.get("bedrooms"),
                "price": record.get("price"),
                "price_currency": record.get("price_currency"),
                "price_period": record.get("price_period"),
                "payment_options": record.get("payment_options"),
                "status": record.get("status"),
                "expected_completion": record.get("expected_completion"),
                "retrieved_at_utc": record.get("retrieved_at_utc"),
                "collection_method": record.get("collection_method")
            }

            documents.append({
                "content": " ".join(content.split()),
                "metadata": metadata
            })

    return documents


if __name__ == "__main__":
    documents = load_property_data()

    print(f"\nTotal documents loaded: {len(documents)}")

    for index, document in enumerate(documents, start=1):
        print(f"\n--- Document {index} ---")
        print(document["content"])
        print("\nMetadata:")
        print(json.dumps(
            document["metadata"],
            indent=4,
            ensure_ascii=False
        ))
