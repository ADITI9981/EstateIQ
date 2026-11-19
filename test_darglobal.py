
import requests
from bs4 import BeautifulSoup

urls = [
    "https://darglobal.co.uk/tierra-viva",
    "https://darglobal.co.uk/the-astera",
    "https://darglobal.co.uk/press/dar-global-introduces-stunning-beach-residence-the-astera-interiors-by-aston-martin"
]

for url in urls:
    print("\n" + "=" * 60)
    print("Testing:", url)

    try:
        response = requests.get(url, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.get_text(strip=True) if soup.title else "No title"

        security_challenge = (
            "incapsula" in response.text.lower()
            or "imperva" in response.text.lower()
        )

        print("HTTP Status:", response.status_code)
        print("Page Title:", title)
        print("Content Length:", len(response.text))
        print("Security Challenge:", security_challenge)

    except requests.RequestException as error:
        print("Request failed:", error)
