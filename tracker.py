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


# Weather from wttr.in, which has a simple JSON API and good UK coverage. The advice messages are custom based on temp and conditions.
def get_weather():
    try:
        url = "https://wttr.in/London?format=j1"
        data = json.loads(fetch(url, user_agent="curl/7.68.0"))

        current = data["current_condition"][0]
        temp_c = int(current["temp_C"])
        feels_c = int(current["FeelsLikeC"])
        desc = current["weatherDesc"][0]["value"].lower()
        humidity = int(current["humidity"])

        # today's high/low
        today = data["weather"][0]
        high = int(today["maxtempC"])
        low = int(today["mintempC"])

        # custom message based on conditions
        if temp_c <= 5:
            advice = "🧥 Heavy coat weather. Don't leave without one."
        elif temp_c <= 12:
            if "rain" in desc or "drizzle" in desc or "shower" in desc:
                advice = "🌧️ Cold and wet — layers plus a waterproof."
            else:
                advice = "🧣 Chilly out. A jacket and scarf will do."
        elif temp_c <= 18:
            if "rain" in desc or "drizzle" in desc or "shower" in desc:
                advice = "☔ Mild but rainy — light jacket and an umbrella."
            else:
                advice = "🙂 Decent enough. Light jacket should be fine."
        elif temp_c <= 24:
            advice = "😎 Nice out. You can get away with just a t-shirt."
        else:
            advice = "☀️ Warm day in London — rare, enjoy it."

        summary = (
            f"**{temp_c}°C** (feels like {feels_c}°C) — {desc.capitalize()}\n"
            f"High {high}°C / Low {low}°C &nbsp;|&nbsp; Humidity {humidity}%\n\n"
            f"> {advice}"
        )
        return summary

    except Exception as e:
        return f"Could not fetch weather: {e}"


# Markets
def trend_label(prices):
    """Simple 7-day moving average trend vs current price."""
    if len(prices) < 7:
        return "insufficient data"
    ma7 = sum(prices[-7:]) / 7
    current = prices[-1]
    diff_pct = ((current - ma7) / ma7) * 100
    if diff_pct > 1:
        return f"📈 Above 7d MA by {diff_pct:.1f}%"
    elif diff_pct < -1:
        return f"📉 Below 7d MA by {abs(diff_pct):.1f}%"
    else:
        return f"➡️ Flat around 7d MA ({diff_pct:+.1f}%)"


def get_btc():
    try:
        # current
        current_data = json.loads(fetch(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        ))
        usd = current_data["bitcoin"]["usd"]

        # history for yesterday close + 7d MA
        hist = json.loads(fetch(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=10&interval=daily"
        ))
        prices = [p[1] for p in hist["prices"]]
        prev = prices[-2]

        diff = usd - prev
        pct = (diff / prev) * 100
        arrow = "🟢 ▲" if diff >= 0 else "🔴 ▼"
        sign = "+" if diff >= 0 else ""
        change = f"{arrow} {sign}${diff:,.0f} ({sign}{pct:.2f}%)"
        trend = trend_label(prices)

        return (
            f"**${usd:,}**\n"
            f"vs yesterday's close: {change}\n"
            f"Trend: {trend}"
        )
    except Exception as e:
        return f"Could not fetch BTC: {e}"


def get_sp500():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=1d&range=12d"
        data = json.loads(fetch(url))
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]

        current = closes[-1]
        prev = closes[-2]

        diff = current - prev
        pct = (diff / prev) * 100
        arrow = "🟢 ▲" if diff >= 0 else "🔴 ▼"
        sign = "+" if diff >= 0 else ""
        change = f"{arrow} {sign}{diff:,.1f} ({sign}{pct:.2f}%)"
        trend = trend_label(closes)

        return (
            f"**{current:,.1f}**\n"
            f"vs previous close: {change}\n"
            f"Trend: {trend}"
        )
    except Exception as e:
        return f"Could not fetch S&P 500: {e}"


# README builder

def build_readme(preview=False):
    now_uk = datetime.now(UK_TZ)
    today = now_uk.strftime("%A, %d %B %Y")
    last_updated = now_uk.strftime("%Y-%m-%d %H:%M %Z")

    print("Fetching weather...")
    weather = get_weather()

    print("Fetching BBC News...")
    bbc = get_headlines("BBC News", "http://feeds.bbci.co.uk/news/rss.xml")

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

    print("Fetching BTC...")
    btc = get_btc()

    print("Fetching S&P 500...")
    sp500 = get_sp500()

    readme = f"""# 🌍 Morning Brief

> Auto-updated every day at 8am UK time via GitHub Actions.

---

## 📅 {today}

---

## 🌤️ London Weather

{weather}

---

## 🗞️ World News

### 📰 BBC News
{bbc}

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

## 📊 Markets

### ₿ Bitcoin (BTC/USD)
{btc}

### 🇺🇸 S&P 500
{sp500}

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
