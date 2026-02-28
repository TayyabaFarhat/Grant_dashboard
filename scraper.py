"""
LaunchPad Intelligence — Main Scraper
Scrapes startup opportunities from multiple public sources.
Runs via GitHub Actions daily.
"""

import json
import hashlib
import logging
import re
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---- Setup ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
TIMEOUT = 15
OUTPUT_FILE = Path(__file__).parent.parent / "opportunities.json"


# ---- Utility ----

def safe_get(url, **kwargs):
    try:
        resp = SESSION.get(url, timeout=TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp
    except Exception as e:
        log.warning(f"Failed to fetch {url}: {e}")
        return None


def make_id(name, org):
    key = f"{name}{org}".lower()
    return hashlib.md5(key.encode()).hexdigest()[:8]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_opp(opp):
    """Ensure all required fields exist."""
    defaults = {
        "id": make_id(opp.get("name", ""), opp.get("organization", "")),
        "name": "",
        "organization": "",
        "category": "",
        "type": "competition",
        "country": "Global",
        "deadline": "",
        "prize": "Varies",
        "link": "",
        "source": "",
        "date_added": now_iso(),
        "status": "open",
        "description": "",
        "tags": [],
    }
    for k, v in defaults.items():
        opp.setdefault(k, v)
    # Clean strings
    for field in ["name", "organization", "country", "prize", "description"]:
        opp[field] = str(opp[field]).strip()
    return opp


# ---- Source: Devpost RSS ----

def scrape_devpost():
    log.info("Scraping Devpost RSS...")
    opps = []
    url = "https://devpost.com/hackathons.rss"
    resp = safe_get(url)
    if not resp:
        return opps

    soup = BeautifulSoup(resp.text, "xml")
    items = soup.find_all("item")[:20]

    for item in items:
        title = item.find("title")
        link = item.find("link")
        desc = item.find("description")
        pub_date = item.find("pubDate")

        if not title or not link:
            continue

        name = title.get_text(strip=True)
        url_val = link.get_text(strip=True)
        description = BeautifulSoup(
            desc.get_text(strip=True) if desc else "", "html.parser"
        ).get_text()[:250]

        opps.append(
            normalize_opp(
                {
                    "name": name,
                    "organization": "Devpost",
                    "category": "Hackathon",
                    "type": "hackathon",
                    "country": "Global",
                    "link": url_val,
                    "source": "devpost.com",
                    "description": description,
                    "tags": ["virtual", "online"],
                }
            )
        )
        time.sleep(0.2)

    log.info(f"Devpost: {len(opps)} opportunities")
    return opps


# ---- Source: Challenge.gov RSS ----

def scrape_challenge_gov():
    log.info("Scraping Challenge.gov RSS...")
    opps = []
    url = "https://www.challenge.gov/api/challenges.json"
    resp = safe_get(url)
    if not resp:
        return opps

    try:
        data = resp.json()
        challenges = data.get("results", [])[:15]
        for ch in challenges:
            name = ch.get("title", "")
            org = ch.get("agency_name", "US Government")
            prize = f"${ch.get('total_prize_offered_amount', 0):,.0f}" if ch.get(
                "total_prize_offered_amount"
            ) else "Varies"
            deadline = ch.get("end_date", "")
            link = ch.get("url", f"https://www.challenge.gov/challenge/{ch.get('id', '')}")
            desc = ch.get("brief_description", "")[:250]

            opps.append(
                normalize_opp(
                    {
                        "name": name,
                        "organization": org,
                        "category": "Grant",
                        "type": "grant",
                        "country": "United States",
                        "deadline": deadline[:10] if deadline else "",
                        "prize": prize,
                        "link": link,
                        "source": "challenge.gov",
                        "description": desc,
                        "tags": ["federal", "us-government"],
                    }
                )
            )
    except Exception as e:
        log.warning(f"Challenge.gov parse error: {e}")

    log.info(f"Challenge.gov: {len(opps)} opportunities")
    return opps


# ---- Source: F6S via public search ----

def scrape_f6s():
    log.info("Scraping F6S...")
    opps = []
    # F6S programs page (public)
    url = "https://www.f6s.com/programs"
    resp = safe_get(url)
    if not resp:
        return opps

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".program-card, .program-item, article.program")[:15]

    for card in cards:
        title_el = card.select_one("h2, h3, .program-title, .title")
        link_el = card.select_one("a[href]")
        org_el = card.select_one(".org-name, .company, .organizer")
        desc_el = card.select_one(".description, p")

        if not title_el or not link_el:
            continue

        name = title_el.get_text(strip=True)
        href = link_el.get("href", "")
        if href.startswith("/"):
            href = f"https://www.f6s.com{href}"
        org = org_el.get_text(strip=True) if org_el else "F6S Partner"
        desc = desc_el.get_text(strip=True)[:200] if desc_el else ""

        opps.append(
            normalize_opp(
                {
                    "name": name,
                    "organization": org,
                    "category": "Accelerator",
                    "type": "accelerator",
                    "country": "Global",
                    "link": href,
                    "source": "f6s.com",
                    "description": desc,
                    "tags": ["f6s", "startup-program"],
                }
            )
        )

    log.info(f"F6S: {len(opps)} opportunities")
    return opps


# ---- Source: Google News RSS (startup opportunities) ----

def scrape_google_news():
    log.info("Scraping Google News RSS for startup opportunities...")
    opps = []

    queries = [
        "startup+competition+2026",
        "startup+grant+2026",
        "accelerator+program+applications+open",
        "startup+hackathon+prize+2026",
        "fellowship+startup+founders+2026",
    ]

    for q in queries:
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        resp = safe_get(url)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item")[:5]

        for item in items:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            source_el = item.find("source")

            if not title or not link:
                continue

            name = re.sub(r"\s*-\s*[^-]+$", "", title.get_text(strip=True))
            link_val = link.get_text(strip=True)
            org = source_el.get_text(strip=True) if source_el else "News Source"

            # Infer type from query
            opp_type = "competition"
            if "grant" in q:
                opp_type = "grant"
            elif "accelerator" in q:
                opp_type = "accelerator"
            elif "hackathon" in q:
                opp_type = "hackathon"
            elif "fellowship" in q:
                opp_type = "fellowship"

            opps.append(
                normalize_opp(
                    {
                        "name": name[:100],
                        "organization": org,
                        "category": opp_type.title(),
                        "type": opp_type,
                        "country": "Global",
                        "link": link_val,
                        "source": "news.google.com",
                        "description": f"Recent news: {name[:200]}",
                        "tags": ["news", opp_type],
                    }
                )
            )

        time.sleep(0.5)

    log.info(f"Google News: {len(opps)} opportunities")
    return opps


# ---- Source: EU EIC (European Innovation Council) ----

def scrape_eic():
    log.info("Scraping EIC opportunities...")
    opps = []
    url = "https://eic.ec.europa.eu/eic-funding-opportunities_en"
    resp = safe_get(url)
    if not resp:
        return opps

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".opportunity-item, .call-item, article")[:8]

    for card in cards:
        title_el = card.select_one("h2, h3, h4")
        link_el = card.select_one("a[href]")
        if not title_el:
            continue

        name = title_el.get_text(strip=True)
        href = link_el.get("href", "") if link_el else "https://eic.ec.europa.eu"
        if href.startswith("/"):
            href = f"https://eic.ec.europa.eu{href}"

        opps.append(
            normalize_opp(
                {
                    "name": name[:100],
                    "organization": "European Innovation Council",
                    "category": "Grant",
                    "type": "grant",
                    "country": "European Union",
                    "prize": "€150K–€2.5M",
                    "link": href,
                    "source": "eic.ec.europa.eu",
                    "description": "EU EIC funding for deep tech and innovative startups.",
                    "tags": ["eu", "deep-tech", "non-dilutive"],
                }
            )
        )

    log.info(f"EIC: {len(opps)} opportunities")
    return opps


# ---- Source: Seedstars ----

def scrape_seedstars():
    log.info("Scraping Seedstars...")
    opps = []
    url = "https://www.seedstars.com/programs/"
    resp = safe_get(url)
    if not resp:
        return opps

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("article, .program-card, .opportunity")[:10]

    for card in cards:
        title_el = card.select_one("h2, h3, .title")
        link_el = card.select_one("a")
        desc_el = card.select_one("p, .desc")

        if not title_el:
            continue

        name = title_el.get_text(strip=True)
        href = link_el.get("href", "https://www.seedstars.com") if link_el else "https://www.seedstars.com"
        if href.startswith("/"):
            href = f"https://www.seedstars.com{href}"
        desc = desc_el.get_text(strip=True)[:200] if desc_el else ""

        opps.append(
            normalize_opp(
                {
                    "name": name,
                    "organization": "Seedstars",
                    "category": "Competition",
                    "type": "competition",
                    "country": "Emerging Markets",
                    "prize": "Up to $500,000",
                    "link": href,
                    "source": "seedstars.com",
                    "description": desc or "Seedstars startup competition for emerging market entrepreneurs.",
                    "tags": ["emerging-markets", "investment", "global"],
                }
            )
        )

    log.info(f"Seedstars: {len(opps)} opportunities")
    return opps


# ---- Deduplicate ----

def deduplicate(opportunities):
    seen_ids = set()
    seen_names = set()
    unique = []

    for opp in opportunities:
        oid = opp.get("id", "")
        name_key = opp.get("name", "").lower().strip()

        if oid in seen_ids or name_key in seen_names:
            continue

        seen_ids.add(oid)
        if name_key:
            seen_names.add(name_key)
        unique.append(opp)

    return unique


# ---- Load existing data ----

def load_existing():
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE) as f:
                data = json.load(f)
                return data.get("opportunities", [])
        except Exception as e:
            log.warning(f"Could not load existing data: {e}")
    return []


# ---- Save ----

def save(opportunities):
    data = {
        "last_updated": now_iso(),
        "total": len(opportunities),
        "opportunities": opportunities,
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"Saved {len(opportunities)} opportunities to {OUTPUT_FILE}")


# ---- Main ----

def main():
    log.info("=== LaunchPad Intelligence Scraper Starting ===")

    # Load existing to preserve curated data
    existing = load_existing()
    log.info(f"Loaded {len(existing)} existing opportunities")

    # Scrape all sources
    scrapers = [
        scrape_devpost,
        scrape_challenge_gov,
        scrape_google_news,
        scrape_eic,
        scrape_seedstars,
        scrape_f6s,
    ]

    new_opps = []
    for scraper in scrapers:
        try:
            result = scraper()
            new_opps.extend(result)
        except Exception as e:
            log.error(f"Scraper {scraper.__name__} failed: {e}")
        time.sleep(1)

    log.info(f"Scraped {len(new_opps)} new opportunities total")

    # Merge: existing + new
    all_opps = existing + new_opps
    unique = deduplicate(all_opps)

    # Filter out empties
    unique = [o for o in unique if o.get("name") and len(o["name"]) > 3]

    # Sort by date added desc
    unique.sort(
        key=lambda o: o.get("date_added", ""),
        reverse=True,
    )

    log.info(f"Final: {len(unique)} unique opportunities")
    save(unique)
    log.info("=== Scraper Complete ===")


if __name__ == "__main__":
    main()
