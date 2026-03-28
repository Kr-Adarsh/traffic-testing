import os
import csv
import requests
from datetime import datetime, timezone

OWNER = os.environ["TRAFFIC_OWNER"]
REPO  = os.environ["TRAFFIC_REPO"]
TOKEN = os.environ["TRAFFIC_TOKEN"]

BASE    = f"https://api.github.com/repos/{OWNER}/{REPO}/traffic"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
}
LOG_PATH = "traffic/traffic_log.csv"
FIELDNAMES = ["captured_at_utc", "type", "timestamp_utc", "count", "uniques"]

def fetch(endpoint):
    r = requests.get(BASE + endpoint, headers=HEADERS)
    print(f"STATUS: {r.status_code}  endpoint: {endpoint}")
    r.raise_for_status()
    return r.json()

def load_existing_keys():
    """Return a set of (type, timestamp_utc) already in the CSV."""
    if not os.path.exists(LOG_PATH):
        return set()
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {(row["type"], row["timestamp_utc"]) for row in reader}

def main():
    now = datetime.now(timezone.utc).isoformat()

    clones = fetch("/clones")
    views  = fetch("/views")

    os.makedirs("traffic", exist_ok=True)
    existing_keys = load_existing_keys()
    file_exists   = os.path.exists(LOG_PATH)

    new_rows = []

    for row in clones.get("clones", []):
        key = ("clone", row["timestamp"])
        if key not in existing_keys:
            new_rows.append([now, "clone", row["timestamp"], row["count"], row["uniques"]])

    for row in views.get("views", []):
        key = ("view", row["timestamp"])
        if key not in existing_keys:
            new_rows.append([now, "view", row["timestamp"], row["count"], row["uniques"]])

    if not new_rows:
        print("No new rows — CSV is already up to date.")
        return

    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(FIELDNAMES)
        writer.writerows(new_rows)

    print(f"Appended {len(new_rows)} new row(s).")

if __name__ == "__main__":
    main()