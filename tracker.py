import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

CACHE_FILE = "price_cache.json"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode()


def get_headlines(name, url, limit=3):
    try:
        xml_data = fetch(url)
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        headlines = []
        for item in items[:limit]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            if title:
                headlines.append(f"- [{title}]({link})")
        return "\n".join(headlines)
    except Exception as e:
        return f"- Could not fetch {name} feed: {e}"


def load_last_price():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None


def save_price(usd, gbp):
    with open(CACHE_FILE, "w") as f:
        json.dump({
            "usd": usd,
            "gbp": gbp,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        }, f)


def format_change(current, previous):
    diff = current - previous
    pct = (diff / previous) * 100
    arrow = "🟢 ▲" if diff >= 0 else "🔴 ▼"
    sign = "+" if diff >= 0 else ""
    return f"{arrow} {sign}{diff:,.0f} ({sign}{pct:.2f}%)"


def get_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,gbp"
        data = json.loads(fetch(url))
        usd = data["bitcoin"]["usd"]
        gbp = data["bitcoin"]["gbp"]

        last = load_last_price()
        save_price(usd, gbp)

        price_line = f"${usd:,} USD / £{gbp:,} GBP"

        if last:
            usd_change = format_change(usd, last["usd"])
            gbp_change = format_change(gbp, last["gbp"])
            since = last.get("timestamp", "last update")
            return (
                f"{price_line}\n\n"
                f"| | USD | GBP |\n"
                f"|---|---|---|\n"
                f"| Change since {since} | {usd_change} | {gbp_change} |"
            )
        else:
            return f"{price_line}\n\n*No previous data yet — change will show from tomorrow.*"

    except Exception as e:
        return f"Could not fetch price: {e}"


def get_weather():
    try:
        url = "https://wttr.in/London?format=3"
        return fetch(url).strip()
    except Exception as e:
        return f"Could not fetch weather: {e}"


def build_readme(preview=False):
    today = datetime.utcnow().strftime("%A, %d %B %Y")

    print("Fetching BBC headlines...")
    bbc = get_headlines("BBC", "http://feeds.bbci.co.uk/news/rss.xml")

    print("Fetching Reuters headlines...")
    reuters = get_headlines("Reuters", "https://feeds.reuters.com/reuters/topNews")

    print("Fetching Al Jazeera headlines...")
    aljazeera = get_headlines("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml")

    print("Fetching BTC price...")
    btc = get_btc_price()

    print("Fetching weather...")
    weather = get_weather()

    readme = f"""# Morning Brief 🌍

> Auto-updated every day via GitHub Actions.

---

## {today}

### 📰 BBC News
{bbc}

### 📡 Reuters
{reuters}

### 🌍 Al Jazeera
{aljazeera}

### ₿ Bitcoin Price
{btc}

### 🌤️ London Weather
{weather}

---
*Last updated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC*
"""

    if preview:
        print("\n--- PREVIEW ---\n")
        print(readme)
        print("--- END PREVIEW ---")
    else:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme)
        print("README.md written successfully.")


if __name__ == "__main__":
    # Run locally without writing file:  python tracker.py --preview
    # Run normally (writes README.md):   python tracker.py
    preview_mode = "--preview" in sys.argv
    if preview_mode:
        print("Running in preview mode — README will not be written.\n")
    build_readme(preview=preview_mode)
