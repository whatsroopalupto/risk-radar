"""Inspect public PPAC/EIA report formats; no account details or keys involved."""
from io import BytesIO
from pathlib import Path
import httpx
from pypdf import PdfReader

URL="https://ppac.gov.in/download.php?file=rep_studies%2F1792155544_Snapshot_of_India_Oil_and_Gas_Sept_2026_V3.pdf"

def main():
    response=httpx.get(URL,follow_redirects=True,timeout=45)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise SystemExit("Public download did not return a PDF; account/download access may be required")
    document=PdfReader(BytesIO(response.content))
    for index,page in enumerate(document.pages):
        text=page.extract_text()
        if "crude oil import" in text.lower() or "crude oil and petroleum" in text.lower():
            print(f"PAGE {index+1}\n{text[:6500]}\n")

if __name__=="__main__":
    main()
