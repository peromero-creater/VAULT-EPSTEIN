import requests
import os
from pathlib import Path

# URLs identified from DOJ archives
DOCS = {
    "Maxwell_Indictment.pdf": "https://www.justice.gov/usao-sdny/press-release/file/1451521/download",
    "Trial_Exhibit_52.pdf": "https://www.justice.gov/usao-sdny/press-release/file/1457816/download",
    "Trial_Exhibit_101.pdf": "https://www.justice.gov/usao-sdny/press-release/file/1458906/download",
    "Trial_Exhibit_202.pdf": "https://www.justice.gov/usao-sdny/press-release/file/1459201/download",
    "Trial_Exhibit_304.pdf": "https://www.justice.gov/usao-sdny/press-release/file/1459351/download"
}

DATA_DIR = Path(__file__).parent.parent / "data" / "files"

def download_docs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    for filename, url in DOCS.items():
        dest = DATA_DIR / filename
        if dest.exists():
            print(f"Skipping {filename}, already exists.")
            continue
            
        print(f"Downloading {filename} from {url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            with open(dest, 'wb') as f:
                f.write(response.content)
            print(f"Successfully downloaded {filename}")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

if __name__ == "__main__":
    download_docs()
