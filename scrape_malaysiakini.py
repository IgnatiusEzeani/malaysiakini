import csv
import re
import time
from pathlib import Path
from typing import List, Dict, Set

import requests
from bs4 import BeautifulSoup
import feedparser


# ===================== CONFIGURATION =====================

BASE_URL = "https://www.malaysiakini.com"
RSS_URL = "https://www.malaysiakini.com/rss/en/news.rss"  # English news feed

# Delay between HTTP requests (be polite!)
REQUEST_DELAY = 1.0  # seconds
TIMEOUT = 15
MAX_RSS_ITEMS = None  # set to an int to limit, e.g. 500

OUTPUT_DIR = Path("malaysiakini_corpus")
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "malaysiakini_keyword_hits.csv"
TEXT_DIR = OUTPUT_DIR / "articles"
TEXT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "AcademicKeywordScraper/1.0 (contact: your-email@example.com)"
}

# --------- KEYWORDS (from Dawn’s table; can be edited) ---------

MENTAL_HEALTH_KEYWORDS = [
    "mental", "mentally", "behavioural", "behavioral", "emotional", "psychiatry", "psychiatric",
    "psychiatrist", "psychology", "psychological", "psychologist", "counselling", "counseling", 
    "counsellor", "counselor", "therapy", "therapist", "therapeutic", "psychotherapy", 
    "psychotherapeutic", "psychotherapists", "depression", "depressed", "suicide", "suicidal",
    "anxiety", "anxious", "stress", "stressed", "trauma", "traumatised", "traumatized",
    "self-harm", "addiction", "addictive", "substance abuse", "alcoholism", "bipolar", "schizophrenia", 
    "schizophrenic", "ocd", "obsessive compulsive disorder", "ptsd", "post-traumatic stress disorder", 
    "adhd", "attention deficit hyperactivity disorder", "autism", "autistic", "isolation", 
    "loneliness", "lonely", "wellbeing", "well-being", "mindfulness", "stressed", "stressful", 
    "coping", "cope", "stigma", "resilience", "discriminate", "discrimination", "discriminated",
]

LGBT_KEYWORDS = [
    "lgb", "lgbt", "lgbtq", "lgbtq+", "lgbtqia", "lgbtqia+", "lesbian", "gay", "homosexual", 
    "homosexuality", "bisexual", "bisexuality", "transgender", "trans", "transwoman", "transwomen",
    "transman", "transmen", "transsexual", "transvestite", "non-binary", "nonbinary", "queer", 
    "intersex", "sogie", "sogiesc", "sex", "sexual", "sexuality", "gender", "masculine", "masculinity",
    "feminine", "femininity",
]

ALL_KEYWORDS = sorted(set(
    [kw.lower() for kw in MENTAL_HEALTH_KEYWORDS + LGBT_KEYWORDS]
))

# Compile regex patterns with word boundaries (case-insensitive)
KEYWORD_PATTERNS: Dict[str, re.Pattern] = {
    kw: re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in ALL_KEYWORDS
}


# ===================== CORE FUNCTIONS =====================

def fetch_url(url: str) -> str | None:
    """Fetch a URL with basic retries. Returns HTML text or None."""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                # Not found; no point retrying
                return None
            else:
                print(f"[WARN] {url} -> HTTP {resp.status_code}")
        except requests.RequestException as e:
            print(f"[ERROR] Request failed ({url}): {e}")
        # Backoff before retry
        time.sleep(2 ** attempt)
    return None


def extract_plain_text(html: str) -> str:
    """
    Strip HTML and return a single normalised text string.
    We intentionally keep everything (nav, footer etc.) because we only
    care about whether the keyword appears anywhere on the page.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles, etc.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Normalise whitespace
    return re.sub(r"\s+", " ", text)


def find_matching_keywords(text: str) -> List[str]:
    """Return a sorted list of keywords found in the given text."""
    matches: Set[str] = set()
    for kw, pattern in KEYWORD_PATTERNS.items():
        if pattern.search(text):
            matches.add(kw)
    return sorted(matches)


def article_id_from_url(url: str) -> str:
    """
    Extract a reasonable file stem from the article URL.
    Malaysiakini news URLs look like /news/762983
    """
    m = re.search(r"/news/(\d+)", url)
    if m:
        return m.group(1)
    # fallback: slug from last path part
    slug = url.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^\w\-]+", "_", slug)
    return slug or "article"


def process_rss_feed(rss_url: str = RSS_URL, max_items: int | None = MAX_RSS_ITEMS):
    """
    Parse the RSS feed, fetch each article, check for keyword matches,
    and save any hits to CSV + individual text files.
    """
    print(f"[INFO] Fetching RSS feed: {rss_url}")
    feed = feedparser.parse(rss_url)

    rows = []
    seen_urls: Set[str] = set()

    for i, entry in enumerate(feed.entries):
        if max_items is not None and i >= max_items:
            break

        url = entry.link
        if not url.startswith("http"):
            url = BASE_URL + url

        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = entry.title
        published = getattr(entry, "published", "")
        print(f"[INFO] [{i+1}/{len(feed.entries)}] Fetching article: {title} ({url})")

        html = fetch_url(url)
        if not html:
            print(f"[WARN] Skipping (could not fetch): {url}")
            time.sleep(REQUEST_DELAY)
            continue

        text = extract_plain_text(html)
        matches = find_matching_keywords(text)

        if matches:
            print(f"  -> HIT: {len(matches)} keyword(s) found")
            article_id = article_id_from_url(url)
            text_path = TEXT_DIR / f"{article_id}.txt"
            with text_path.open("w", encoding="utf-8") as f:
                f.write(text)

            rows.append({
                "url": url,
                "title": title,
                "published": published,
                "keywords": ";".join(matches),
                "text_file": str(text_path),
            })
        else:
            print("  -> no relevant keywords")

        time.sleep(REQUEST_DELAY)

    # Write CSV summary
    if rows:
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["url", "title", "published", "keywords", "text_file"],
            )
            writer.writeheader()
            writer.writerows(rows)

        print(f"[INFO] Done. {len(rows)} matching articles saved to {CSV_PATH}")
    else:
        print("[INFO] No matches found in the RSS feed.")


# ===================== ENTRY POINT =====================

if __name__ == "__main__":
    """
    Usage:
        python scrape_malaysiakini_keywords.py

    Adjust:
      - RSS_URL if you want a different section/language
      - keyword lists above
      - MAX_RSS_ITEMS if you want to limit how many feed items you scan
    """
    process_rss_feed()
