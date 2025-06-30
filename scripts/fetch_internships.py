import requests
from datetime import datetime, timezone
from app.db import SessionLocal
from app.models import Internship

INTERNSHIP_FEED_URL = "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/dev/.github/scripts/listings.json"


def parse_unix(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def fetch_and_save():
    session = SessionLocal()

    response = requests.get(INTERNSHIP_FEED_URL)
    internships = response.json()

    for item in internships:
        internship = Internship(
            company=item.get("company_name"),
            role=item.get("title"),
            location=", ".join(item.get("locations", [])),
            remote=False,  # No explicit remote flag—set logic if needed
            link=item.get("url"),
            date_posted=parse_unix(item.get("date_posted", item.get("date_updated"))),
            source=item.get("source"),
        )
        session.add(internship)

    session.commit()
    print("✅ Internship data saved.")


if __name__ == "__main__":
    print("Starting internship fetch...")
    fetch_and_save()
