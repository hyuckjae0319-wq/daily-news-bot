import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

KST = datetime.timezone(datetime.timedelta(hours=9))


def send_telegram(message: str) -> bool:
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[ERROR] TELEGRAM_TOKEN or CHAT_ID is not set.")
        return False

    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
    success = True
    for chunk in chunks:
        try:
            payload = json.dumps({
                "chat_id": CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML"
            }).encode("utf-8")
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.getcode() != 200:
                    success = False
        except Exception as e:
            print(f"[ERROR] Telegram send failed: {e}")
            success = False
    return success


def get_weather_info(location: str = "Jeju") -> tuple:
    try:
        encoded = urllib.parse.quote(location)
        url = f"https://wttr.in/{encoded}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        desc_list = current.get("weatherDesc", [])
        description = desc_list[0]["value"] if desc_list else "N/A"
        return temp_c, description, feels_like
    except Exception as e:
        print(f"[ERROR] Weather fetch failed: {e}")
        return "N/A", "N/A", "N/A"


def get_google_news(keyword: str = "", limit: int = 3) -> list:
    try:
        if keyword:
            encoded_kw = urllib.parse.quote(keyword)
            url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        news_list = []
        for item in root.findall("./channel/item")[:limit]:
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is not None and link_el is not None:
                link_text = link_el.text or (link_el.tail or "").strip()
                news_list.append((title_el.text or "(no title)", link_text))
        return news_list
    except Exception as e:
        print(f"[ERROR] News fetch failed: {e}")
        return []


def main():
    now = datetime.datetime.now(KST)
    month_day = now.strftime("%m-%d")

    anniversaries = {
        "01-01": "새해 첫날 🎊",
        "03-01": "3·1절",
        "03-19": "혁재 생일 🎂",
        "06-03": "내 생일 🎂",
        "08-15": "광복절",
        "09-17": "오빠 생일 🎂",
        "10-03": "개천절",
        "10-09": "한글날",
        "11-29": "혁준이 생일 🎂",
        "12-03": "도연이 생일 🎂",
        "12-25": "크리스마스 🎄",
    }

    lines = []
    lines.append(f"🔔 <b>[데일리 브리핑]</b> {now.strftime("%Y-%m-%d %H:%M")} KST
")

    if month_day in anniversaries:
        lines.append(f"🎉 오늘은 <b>{anniversaries[month_day]}</b>입니다! 뜻깨은 하루 보내세요.
")
    else:
        lines.append("오늘은 특별히 지정된 기념일은 없지만, 행복한 하루 보내시길 바랍니다!
")

    temp, weather, feels = get_weather_info("Jeju")
    lines.append(
        f"🌤️ <b>제주 날씨</b>
"
        f"  🌡️ 현재: {temp}°C  (체감 {feels}°C)
"
        f"  ☁️ 상태: {weather}
"
    )

    lines.append("📰 <b>주요 뉴스</b>")
    all_news = get_google_news(limit=2) + get_google_news(keyword="제주", limit=1)
    if all_news:
        for idx, (title, link) in enumerate(all_news, 1):
            lines.append(f"  {idx}. {title}
     🔗 {link}")
    else:
        lines.append("  최신 뉴스를 가져오지 못했습니다.")

    lines.append("")

    lines.append("🎊 <b>제주 축제/행사 소식</b>")
    festivals = get_google_news(keyword="제주 축제", limit=2)
    if festivals:
        for idx, (title, link) in enumerate(festivals, 1):
            lines.append(f"  {idx}. {title}
     🔗 {link}")
    else:
        lines.append("  현재 등록된 축제 소식이 없습니다.")

    full_message = "
".join(lines)
    print(full_message)

    result = send_telegram(full_message)
    if not result:
        raise SystemExit("[ERROR] Telegram send failed. Marking workflow as failed.")


if __name__ == "__main__":
    main()
