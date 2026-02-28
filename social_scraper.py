"""
LaunchPad Intelligence — Social & LinkedIn Scraper
Scrapes startup opportunities from social platforms using public RSS and search.
"""

import logging
import re
import time
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("social_scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
TIMEOUT = 15


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_get(url):
    try:
        resp = SESSION.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp
    except Exception as e:
        log.warning(f"Failed: {url} → {e}")
        return None


# ---- Twitter/X Public RSS via Nitter ----

def scrape_twitter_opportunities():
    """Scrape startup opportunity tweets via Nitter (public RSS proxy)."""
    log.info("Scraping Twitter/X via public RSS...")
    opps = []

    nitter_instances = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.1d4.us",
    ]

    search_terms = [
        "startup+grant+applications+open",
        "accelerator+program+apply+now",
        "startup+competition+deadline",
    ]

    for instance in nitter_instances[:1]:  # Try first instance
        for term in search_terms:
            url = f"{instance}/search/rss?q={term}&f=tweets"
            resp = safe_get(url)
            if not resp:
                continue

            soup = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")[:5]

            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")

                if not title_el:
                    continue

                text = title_el.get_text(strip=True)
                if len(text) < 20:
                    continue

                opps.append({
                    "id": f"tw_{hash(text) % 10**8:08d}",
                    "name": text[:80],
                    "organization": "Twitter/X Community",
                    "category": "Social Feed",
                    "type": "competition",
                    "country": "Global",
                    "deadline": "",
                    "prize": "Varies",
                    "link": link_el.get_text(strip=True) if link_el else "",
                    "source": "twitter.com",
                    "date_added": now_iso(),
                    "status": "open",
                    "description": (desc_el.get_text(strip=True) if desc_el else text)[:200],
                    "tags": ["social", "twitter"],
                })

            time.sleep(0.5)

    log.info(f"Twitter/X: {len(opps)} opportunities")
    return opps


# ---- LinkedIn Public Opportunity Feeds ----

def scrape_linkedin_opportunities():
    """
    Scrape LinkedIn public job/opportunity pages (no auth required for public pages).
    Uses LinkedIn's public opportunity RSS where available.
    """
    log.info("Scraping LinkedIn public opportunity signals...")
    opps = []

    # LinkedIn doesn't provide RSS; use Google News for LinkedIn-sourced signals
    url = (
        "https://news.google.com/rss/search?"
        "q=site:linkedin.com+startup+competition+grant+accelerator&"
        "hl=en-US&gl=US&ceid=US:en"
    )
    resp = safe_get(url)
    if not resp:
        return opps

    soup = BeautifulSoup(resp.text, "xml")
    items = soup.find_all("item")[:8]

    for item in items:
        title_el = item.find("title")
        link_el = item.find("link")
        src_el = item.find("source")

        if not title_el:
            continue

        text = title_el.get_text(strip=True)
        text = re.sub(r"\s*-\s*LinkedIn$", "", text).strip()

        if len(text) < 10:
            continue

        opps.append({
            "id": f"li_{hash(text) % 10**8:08d}",
            "name": text[:100],
            "organization": "LinkedIn",
            "category": "Competition",
            "type": "competition",
            "country": "Global",
            "deadline": "",
            "prize": "Varies",
            "link": link_el.get_text(strip=True) if link_el else "",
            "source": "linkedin.com",
            "date_added": now_iso(),
            "status": "open",
            "description": f"Startup opportunity shared on LinkedIn: {text[:200]}",
            "tags": ["linkedin", "professional"],
        })

    log.info(f"LinkedIn signals: {len(opps)} opportunities")
    return opps


# ---- Facebook Public Groups (via RSS aggregators) ----

def scrape_facebook_opportunities():
    """
    Facebook doesn't offer public RSS. Use RSS aggregator proxies
    for public startup community pages where available.
    """
    log.info("Scraping Facebook public startup signals via RSS bridge...")
    opps = []

    # Use RSS feed for public startup communities via news search
    url = (
        "https://news.google.com/rss/search?"
        "q=startup+competition+grant+2026+facebook&"
        "hl=en-US&gl=US&ceid=US:en"
    )
    resp = safe_get(url)
    if not resp:
        return opps

    soup = BeautifulSoup(resp.text, "xml")
    items = soup.find_all("item")[:5]

    for item in items:
        title_el = item.find("title")
        link_el = item.find("link")

        if not title_el:
            continue

        text = title_el.get_text(strip=True)
        if "facebook" not in text.lower() and not any(
            w in text.lower() for w in ["startup", "grant", "competition", "accelerator"]
        ):
            continue

        opps.append({
            "id": f"fb_{hash(text) % 10**8:08d}",
            "name": text[:100],
            "organization": "Facebook Community",
            "category": "Competition",
            "type": "competition",
            "country": "Global",
            "deadline": "",
            "prize": "Varies",
            "link": link_el.get_text(strip=True) if link_el else "",
            "source": "facebook.com",
            "date_added": now_iso(),
            "status": "open",
            "description": f"Startup opportunity from social media: {text[:200]}",
            "tags": ["social", "community"],
        })

    log.info(f"Facebook signals: {len(opps)} opportunities")
    return opps


# ---- Reddit Public RSS ----

def scrape_reddit_opportunities():
    """Scrape Reddit public subreddits for startup opportunities."""
    log.info("Scraping Reddit public subreddits...")
    opps = []

    subreddits = [
        "r/startups",
        "r/entrepreneur",
        "r/smallbusiness",
    ]

    for sub in subreddits:
        url = f"https://www.reddit.com/{sub}/search.rss?q=grant+competition+accelerator+fellowship&sort=new"
        resp = safe_get(url)
        if not resp:
            time.sleep(1)
            continue

        soup = BeautifulSoup(resp.text, "xml")
        entries = soup.find_all("entry")[:5]

        for entry in entries:
            title_el = entry.find("title")
            link_el = entry.find("link")
            content_el = entry.find("content")

            if not title_el:
                continue

            text = title_el.get_text(strip=True)
            if not any(
                w in text.lower()
                for w in ["grant", "competition", "accelerator", "fellowship", "hackathon", "prize", "funding"]
            ):
                continue

            href = link_el.get("href", "") if link_el else ""
            desc = BeautifulSoup(
                content_el.get_text(strip=True) if content_el else "", "html.parser"
            ).get_text()[:200]

            opps.append({
                "id": f"rd_{hash(text) % 10**8:08d}",
                "name": text[:100],
                "organization": f"Reddit {sub}",
                "category": "Community",
                "type": "competition",
                "country": "Global",
                "deadline": "",
                "prize": "Varies",
                "link": href,
                "source": "reddit.com",
                "date_added": now_iso(),
                "status": "open",
                "description": desc or text[:200],
                "tags": ["reddit", "community"],
            })

        time.sleep(1)

    log.info(f"Reddit: {len(opps)} opportunities")
    return opps


def get_all_social_opportunities():
    """Run all social scrapers and return combined results."""
    all_opps = []

    scrapers = [
        scrape_linkedin_opportunities,
        scrape_reddit_opportunities,
        # scrape_twitter_opportunities,  # Enable if Nitter is accessible
        # scrape_facebook_opportunities,  # Enable if needed
    ]

    for scraper in scrapers:
        try:
            result = scraper()
            all_opps.extend(result)
        except Exception as e:
            log.error(f"{scraper.__name__} failed: {e}")

    return all_opps


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    results = get_all_social_opportunities()
    print(f"\nTotal social opportunities: {len(results)}")
    for r in results[:5]:
        print(f"  - {r['name'][:60]}")
