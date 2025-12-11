# Malaysiakini Keyword Scraper

Build a **small research corpus** of Malaysiakini news stories that mention
**mental-health** and **LGBT-related** terms.

The script:

- pulls articles from Malaysiakini’s **English news RSS feed**
- downloads each article page
- searches for configured **keywords**
- saves:
  - a **CSV summary** of all matches
  - the **full plain text** of each matching article

> ⚠️ **Important:** Before using this for real research, check Malaysiakini’s  
> Terms of Service / robots.txt and, ideally, obtain permission for text mining.

---

## 1. Quick Start

```bash
git clone https://github.com/IgnatiusEzeani/malaysiakini
cd malaysiakini

# (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python scrape_malaysiakini.py
