import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from scraper.common import save_json, get_timestamp


PROPERTY_URL = (
    "https://wasalt.sa/en/property/rent/"
    "villa-250-sqm-facing-south-with-9-bedrooms-5891036"
)

HEADERS = {
    "User-Agent": "EstateIQ-Research/1.0"
}


def extract_json_ld(soup):
    """Extract structured data from JSON-LD scripts."""

    results = []

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):
        try:
            data = json.loads(script.string or script.get_text())

            items = data if isinstance(data, list) else [data]

            for item in items:
                if isinstance(item, dict):
                    results.append(item)

        except (json.JSONDecodeError, TypeError):
            continue

    return results


def clean_description(description):
    """Remove HTML, phone numbers and contact prompts."""

    text = BeautifulSoup(
        description or "",
        "html.parser"
    ).get_text(" ", strip=True)

    # Remove Saudi phone number patterns.
    text = re.sub(
        r"(?<!\d)(?:\+?966|0)?5\d{8}(?!\d)",
        "[CONTACT REMOVED]",
        text
    )

    # Remove the remaining contact request.
    text = re.sub(
        r"لمزيد من التفاصيل.*$",
        "",
        text
    )

    return re.sub(r"\s+", " ", text).strip()


def extract_property(url):
    """Extract selected public property fields."""

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=25
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    structured_items = extract_json_ld(soup)

    property_data = next(
        (
            item for item in structured_items
            if item.get("@type") == "SingleFamilyResidence"
        ),
        None
    )

    if not property_data:
        raise ValueError("Property structured data not found.")

    address = property_data.get("address", {})
    offers = property_data.get("offers", [])

    if isinstance(offers, dict):
        offers = [offers]

    offer = offers[0] if offers else {}

    title = property_data.get("name")

    if not title:
        raise ValueError("Property title not found.")

    description = clean_description(
        property_data.get("description", "")
    )

    path_parts = urlparse(url).path.rstrip("/").split("/")
    listing_id = path_parts[-1].split("-")[-1]

    # Extract area from the title where available.
    area_match = re.search(r"(\d+(?:\.\d+)?)\s*SQM", title, re.I)

    result = {
        "source": "Wasalt",
        "source_url": url,
        "listing_id": listing_id,
        "retrieved_at_utc": get_timestamp(),
        "title": title,
        "property_type": title.split()[0],
        "transaction_type": (
            "Rent" if "/rent/" in url else
            "Sale" if "/sale/" in url else
            "Unknown"
        ),
        "bedrooms": property_data.get("numberOfBedrooms"),
        "bathrooms": property_data.get("numberOfBathroomsTotal"),
        "area_sqm": float(area_match.group(1)) if area_match else None,
        "location": {
            "street": address.get("streetAddress"),
            "city": address.get("addressLocality"),
            "region": address.get("addressRegion"),
            "country": address.get("addressCountry")
        },
        "price": offer.get("price"),
        "price_currency": "SAR" if "SAR" in str(offer.get("priceCurrency", "")) else None,
        "price_period": "year" if "Year" in str(offer.get("priceCurrency", "")) else None,
        "price_source_label": offer.get("priceCurrency"),
        "image_url": property_data.get("image"),
        "description": description
    }

    return result


if __name__ == "__main__":
    print("Starting EstateIQ Wasalt scraper...")

    try:
        property_info = extract_property(PROPERTY_URL)

        save_json(
            property_info,
            "wasalt_sample_property.json"
        )

        print("\nClean property record:")
        print(json.dumps(
            property_info,
            indent=4,
            ensure_ascii=False
        ))

    except requests.RequestException as error:
        print("Website request failed:", error)

    except Exception as error:
        print("Scraping failed:", error)
