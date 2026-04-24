import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

PAGE_URL = "https://science.nasa.gov/mission/landsat/outreach/your-name-in-landsat/"
OUT_DIR = "public/letters"
DB_FILE_SRC = "src/letterImages.json"
DB_FILE_PUBLIC = "public/letterImages.json"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs("src", exist_ok=True)
os.makedirs("public", exist_ok=True)

html = requests.get(PAGE_URL, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

database = {}
current_letter = None
current_place = None
current_coordinates = None
current_map_url = None

for tag in soup.find_all(["h2", "h3", "a"]):
    text = tag.get_text(" ", strip=True)

    if tag.name == "h2" and re.fullmatch(r"[A-Z]", text):
        current_letter = text
        database.setdefault(current_letter, [])
        os.makedirs(f"{OUT_DIR}/{current_letter}", exist_ok=True)
        current_place = None
        current_coordinates = None
        current_map_url = None
        continue

    if tag.name == "h3" and current_letter:
        current_place = text
        current_coordinates = None
        current_map_url = None
        continue

    if tag.name == "a" and current_letter and current_place:
        href = tag.get("href") or ""
        url = urljoin(PAGE_URL, href)

        if "°" in text:
            current_coordinates = text
            current_map_url = url
            continue

        if "download" in text.lower():
            filename = unquote(url.split("/")[-1].split("?")[0])
            safe_filename = re.sub(r"[^a-zA-Z0-9_.-]", "-", filename)

            local_path = f"{OUT_DIR}/{current_letter}/{safe_filename}"
            public_path = f"/letters/{current_letter}/{safe_filename}"

            print(f"Downloading {current_letter}: {current_place}")

            if not os.path.exists(local_path):
                img = requests.get(url, timeout=60).content
                with open(local_path, "wb") as f:
                    f.write(img)

            database[current_letter].append({
                "letter": current_letter,
                "place": current_place,
                "coordinates": current_coordinates or "",
                "map": current_map_url or "",
                "image": public_path,
                "source": url,
                "credit": "NASA / USGS Landsat"
            })

            current_place = None
            current_coordinates = None
            current_map_url = None

with open(DB_FILE_SRC, "w", encoding="utf-8") as f:
    json.dump(database, f, indent=2, ensure_ascii=False)

with open(DB_FILE_PUBLIC, "w", encoding="utf-8") as f:
    json.dump(database, f, indent=2, ensure_ascii=False)

print(f"Saved database to {DB_FILE_SRC}")
print(f"Saved database to {DB_FILE_PUBLIC}")
