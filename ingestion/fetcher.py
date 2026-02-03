import requests
from bs4 import BeautifulSoup
import os
import zipfile
from pathlib import Path

BASE_URL = "https://www.justice.gov/action-center/epstein-library"
DATA_DIR = Path("/data/zips")

def fetch_datasets():
    print(f"Connecting to DOJ Epstein Library: {BASE_URL}")
    response = requests.get(BASE_URL)
    if response.status_id != 200:
        print("Failed to reach DOJ library.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # Finding download links for .zip files
    links = soup.find_all('a', href=lambda href: href and ".zip" in href)
    
    if not links:
        print("No zip datasets found on the page.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for link in links:
        zip_url = link['href']
        if not zip_url.startswith('http'):
            zip_url = "https://www.justice.gov" + zip_url
            
        zip_name = zip_url.split('/')[-1]
        target_path = DATA_DIR / zip_name
        
        if target_path.exists():
            print(f"Skipping {zip_name}, already exists.")
            continue
            
        print(f"Downloading {zip_name}...")
        r = requests.get(zip_url, stream=True)
        with open(target_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {zip_name}")

if __name__ == "__main__":
    fetch_datasets()
