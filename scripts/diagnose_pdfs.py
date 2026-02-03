import fitz
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "files"

def diagnose():
    for file_path in DATA_DIR.glob("*.pdf"):
        print(f"\n--- {file_path.name} ---")
        try:
            doc = fitz.open(file_path)
            print(f"Pages: {len(doc)}")
            for i in range(min(3, len(doc))):
                page = doc.load_page(i)
                text = page.get_text()
                print(f"Page {i+1} text snippet ({len(text)} chars):")
                print(text[:200] + "...")
            doc.close()
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

if __name__ == "__main__":
    diagnose()
