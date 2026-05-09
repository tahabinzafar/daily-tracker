import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
import sys

UK_TZ = ZoneInfo("Europe/London")


def fetch(url, user_agent="Mozilla/5.0"):
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
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


def format_change(current, previous):
    diff = current - previous
    pct = (diff / previous) * 100
    arrow = "🟢 ▲" if diff >= 0 else "🔴 ▼"
    sign = "+" if diff >= 0 else ""
    return f"{arrow} {sign}{diff:,.0f} ({sign}{pct:.2f}%)"


def get_btc_price():
    try:
        # current price
        current_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,gbp"
        current_data = json.loads(fetch(current_url))
        usd = current_data["bitcoin"]["usd"]
        gbp = current_data["bitcoin"]["gbp"]

        # yesterday's closing price (daily interval, last 2 days)
        hist_url_usd = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=2&interval=daily"
        hist_url_gbp = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=gbp&days=2&interval=daily"

        hist_usd = json.loads(fetch(hist_url_usd))
        hist_gbp = json.loads(fetch(hist_url_gbp))

        # prices array: [[timestamp, price], ...] — second to last is yesterday's close
        prev_usd = hist_usd["prices"][-2][1]
        prev_gbp = hist_gbp["prices"][-2][1]

        usd_change = format_change(usd, prev_usd)
        gbp_change = format_change(gbp, prev_gbp)

        return (
            f"${usd:,} USD / £{gbp:,} GBP\n\n"
            f"| | USD | GBP |\n"
            f"|---|---|---|\n"
            f"| vs yesterday's close | {usd_change} | {gbp_change} |"
        )

    except Exception as e:
        return f"Could not fetch BTC price: {e}"


def get_weather():
    try:
        url = "https://wttr.in/London?format=3"
        return fetch(url, user_agent="curl/7.68.0").strip()
    except Exception as e:
        return f"Could not fetch weather: {e}"


def build_readme(preview=False):
    now_uk = datetime.now(UK_TZ)
    today = now_uk.strftime("%A, %d %B %Y")
    last_updated = now_uk.strftime("%Y-%m-%d %H:%M %Z")

    print("Fetching BBC headlines...")
    bbc = get_headlines("BBC", "http://feeds.bbci.co.uk/news/rss.xml")

    print("Fetching AP News headlines...")
    ap = get_headlines("AP News", "https://feeds.apnews.com/rss/topnews")

    print("Fetching Al Jazeera headlines...")
    aljazeera = get_headlines("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml")

    print("Fetching Guardian World headlines...")
    guardian = get_headlines("Guardian", "https://www.theguardian.com/world/rss")

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

### 📡 AP News
{ap}

### 🌍 Al Jazeera
{aljazeera}

### 🌐 Guardian World
{guardian}

### ₿ Bitcoin Price
{btc}

### 🌤️ London Weather
{weather}

---
*Last updated: {last_updated}*
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
