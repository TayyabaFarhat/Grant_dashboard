# 🚀 LaunchPad Intelligence Dashboard

**A premium, auto-updating startup opportunities dashboard powered by GitHub Actions.**

Automatically discovers and displays startup competitions, grants, accelerators, fellowships, hackathons, and funding opportunities from across the internet — updated every 24 hours with zero manual intervention.

---

## ✨ Features

- **Auto-updated daily** via GitHub Actions (no manual work required)
- **Premium SaaS-quality UI** inspired by Stripe, Linear, and Notion
- **24+ pre-loaded opportunities** from top sources
- **Smart filtering** by type, country, status, and deadline
- **Live status badges** (Open, Closing Soon, New, Closed)
- **Dark mode** with elegant toggle
- **Fully responsive** — works on mobile, tablet, and desktop
- **Instant search** across all opportunity fields
- **Sources**: Devpost, Challenge.gov, F6S, Seedstars, EIC, Google News, Reddit, and more

---

## 🚀 Quick Deploy (5 minutes)

### Step 1: Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it: `startup-intelligence-dashboard`
3. Set to **Public** (required for free GitHub Pages)
4. Click **Create repository**

### Step 2: Upload Files

**Option A — GitHub Web UI (easiest):**
1. Open your new repository
2. Click **Add file → Upload files**
3. Drag and drop ALL project files/folders
4. Maintain the folder structure exactly
5. Click **Commit changes**

**Option B — Git CLI:**
```bash
git clone https://github.com/YOUR_USERNAME/startup-intelligence-dashboard.git
cd startup-intelligence-dashboard
# Copy all project files here
git add .
git commit -m "Initial deploy"
git push
```

### Step 3: Enable GitHub Pages

1. In your repository, go to **Settings → Pages**
2. Under **Source**, select **Deploy from a branch**
3. Select branch: `main` (or `master`)
4. Select folder: `/ (root)`
5. Click **Save**

⏳ Wait 2-3 minutes, then visit:
```
https://YOUR_USERNAME.github.io/startup-intelligence-dashboard/
```

### Step 4: Verify Automation

1. Go to **Actions** tab in your repository
2. You'll see the `Auto-Update Opportunities` workflow
3. Click **Run workflow** to test it immediately
4. It will automatically run every 24 hours from now on

---

## 📁 Project Structure

```
startup-intelligence-dashboard/
│
├── index.html              # Main dashboard page
├── style.css               # Premium SaaS styling
├── script.js               # Dashboard logic & filtering
├── opportunities.json      # Data file (auto-updated)
│
├── scraper/
│   ├── scraper.py          # Main scraper (all sources)
│   ├── social_scraper.py   # Social media scraper
│   └── requirements.txt    # Python dependencies
│
├── .github/workflows/
│   └── auto-update.yml     # GitHub Actions automation
│
└── README.md               # This file
```

---

## 🤖 How Automation Works

```
Every 24 hours (midnight UTC):
│
├── GitHub Actions triggers automatically
├── Installs Python + dependencies
├── Runs scraper.py
│   ├── Scrapes Devpost RSS
│   ├── Scrapes Challenge.gov API
│   ├── Scrapes Google News RSS
│   ├── Scrapes EIC (EU grants)
│   ├── Scrapes Seedstars
│   └── Scrapes F6S
├── Merges with existing data
├── Removes duplicates
├── Saves to opportunities.json
├── Commits & pushes to GitHub
└── GitHub Pages auto-deploys ✅
```

No servers. No paid APIs. No maintenance required.

---

## 📊 Data Sources

| Source | Type | Method |
|--------|------|--------|
| Devpost | Hackathons | RSS Feed |
| Challenge.gov | US Gov Grants | Public API |
| Google News | All types | RSS Feed |
| EU EIC | EU Grants | Web scraping |
| Seedstars | Competitions | Web scraping |
| F6S | Accelerators | Web scraping |
| Reddit | Community | RSS Feed |
| LinkedIn | Social signals | Via Google News |

---

## ➕ Adding New Sources

Edit `scraper/scraper.py` and add a new function:

```python
def scrape_my_source():
    log.info("Scraping My Source...")
    opps = []
    
    resp = safe_get("https://example.com/opportunities.rss")
    if not resp:
        return opps
    
    soup = BeautifulSoup(resp.text, "xml")
    for item in soup.find_all("item")[:20]:
        opps.append(normalize_opp({
            "name": item.find("title").get_text(strip=True),
            "organization": "My Source",
            "category": "Competition",
            "type": "competition",  # grant | competition | accelerator | hackathon | fellowship | funding
            "country": "Global",
            "link": item.find("link").get_text(strip=True),
            "source": "example.com",
            "description": "...",
            "tags": ["my-tag"],
        }))
    
    return opps
```

Then add it to the `scrapers` list in `main()`.

---

## 🎨 Customization

### Change Colors
Edit CSS variables in `style.css`:
```css
:root {
  --accent: #6d56fa;     /* Primary accent color */
  --bg: #f8f8f6;         /* Background color */
  /* ... */
}
```

### Add Categories
In `index.html`, add a new tab:
```html
<button class="tab" data-tab="mytype">My Category</button>
```

In `style.css`, add type badge style:
```css
.type-mytype { background: #e0f2fe; color: #0284c7; }
```

### Manual Data Entry
Add entries directly to `opportunities.json`:
```json
{
  "id": "custom001",
  "name": "My Opportunity",
  "organization": "My Org",
  "category": "Grant",
  "type": "grant",
  "country": "United States",
  "deadline": "2026-12-31",
  "prize": "$50,000",
  "link": "https://example.com",
  "source": "manual",
  "date_added": "2026-02-28T00:00:00Z",
  "status": "open",
  "description": "Description here.",
  "tags": ["tag1", "tag2"]
}
```

---

## 🛠 Local Development

```bash
# Install Python dependencies
pip install -r scraper/requirements.txt

# Run scraper locally
python scraper/scraper.py

# Serve locally (Python built-in server)
python -m http.server 8000
# → Visit http://localhost:8000
```

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 🙏 Data Sources Acknowledgment

Data is collected from publicly available sources including Devpost, Challenge.gov (US Government public data), Google News RSS, EU Innovation Council, Seedstars, F6S, and Reddit. All links direct to original sources. This dashboard is an aggregator for informational purposes.
