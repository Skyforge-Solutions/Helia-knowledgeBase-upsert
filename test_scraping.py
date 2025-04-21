import trafilatura, requests, pdfplumber
from io import BytesIO

def scrape_blog(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return "Error: fetch failed"
    text = trafilatura.extract(downloaded) or ""
    return text.strip() or "Error: no text found"

def scrape_pdf(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    if "application/pdf" not in r.headers.get("Content-Type", ""):
        return "Error: not a PDF"
    with pdfplumber.open(BytesIO(r.content)) as pdf:
        txt = "".join(page.extract_text() or "" for page in pdf.pages)
    return txt.strip() or "Error: no text found"

if __name__ == "__main__":
    # url = "https://connectsafely.org/wp-content/uploads/2022/05/Parents-Guide-to-TikTok-2022-final.pdf"
    # print(scrape_pdf(url))