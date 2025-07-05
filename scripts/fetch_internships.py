import requests
import time
from app.db import SessionLocal
from app.models import Internship

URL = "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/dev/.github/scripts/listings.json"


def fetch_json():
    response = requests.get(URL)
    response.raise_for_status()
    return response.json()


def update_internships(data):
    db = SessionLocal()
    for item in data:
        internship = Internship(
            id=item["id"],
            company=item["company_name"],
            role=item["title"],
            location=", ".join(item.get("locations", [])),
            link=item.get("url"),
            date_posted=str(item.get("date_posted")),
            source=item.get("source"),
            active=item.get("active"),
            is_visible=item.get("is_visible"),
            season=item.get("season"),
        )
        db.merge(internship)  # update if exists, insert if new

    db.commit()
    db.close()


if __name__ == "__main__":

    while True:

        try:
            print("Fetching internships...", flush=True)
            data = fetch_json()
            update_internships(data)
            print("Internship data updated.", flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)
        time.sleep(3600)  # Fetch internship data every hour
