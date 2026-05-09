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
    return f"{arrow} {sign}${diff:,.0f} ({sign}{pct:.2f}%)"


def get_btc_price():
    try:
        current_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        current_data = json.loads(fetch(current_url))
        usd = current_data["bitcoin"]["usd"]

        hist_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=2&interval=daily"
        hist_data = json.loads(fetch(hist_url))
        prev_usd = hist_data["prices"][-2][1]

        change = format_change(usd, prev_usd)

        return f"**${usd:,}** &nbsp;|&nbsp; vs yesterday's close: {change}"

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

    print("Fetching BBC News...")
    bbc = get_headlines("BBC News", "http://feeds.bbci.co.uk/news/rss.xml")

    print("Fetching AP News...")
    ap = get_headlines("AP News", "https://feeds.apnews.com/rss/topnews")

    print("Fetching Al Jazeera...")
    aljazeera = get_headlines("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml")

    print("Fetching Guardian World...")
    guardian_world = get_headlines("Guardian World", "https://www.theguardian.com/world/rss")

    print("Fetching BBC Sport...")
    bbc_sport = get_headlines("BBC Sport", "http://feeds.bbci.co.uk/sport/rss.xml")

    print("Fetching Sky Sports Football...")
    sky_football = get_headlines("Sky Sports", "https://www.skysports.com/rss/12040")

    print("Fetching Guardian Sport...")
    guardian_sport = get_headlines("Guardian Sport", "https://www.theguardian.com/sport/rss")

    print("Fetching ESPN...")
    espn = get_headlines("ESPN", "https://www.espn.com/espn/rss/news")

    print("Fetching BTC price...")
    btc = get_btc_price()

    print("Fetching weather...")
    weather = get_weather()

    readme = f"""# 🌍 Morning Brief

> Auto-updated every day at 8am UK time via GitHub Actions.

---

## 📅 {today}

---

## 🗞️ World News

### 📰 BBC News
{bbc}

### 📡 AP News
{ap}

### 🌍 Al Jazeera
{aljazeera}

### 🌐 The Guardian
{guardian_world}

---

## ⚽ Sports

### 🏟️ BBC Sport
{bbc_sport}

### 📺 Sky Sports Football
{sky_football}

### 🏅 The Guardian Sport
{guardian_sport}

### 🏈 ESPN
{espn}

---

## 📊 Markets & Weather

### ₿ Bitcoin
{btc}

### 🌤️ London
{weather}

---
<sub>Last updated: {last_updated}</sub>
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
