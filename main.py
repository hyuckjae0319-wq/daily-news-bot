import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import sys
import re
import os

# 1. 보안 설정 (GitHub Secrets에서 가져옴)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(message):
    try:
        encoded_msg = urllib.parse.quote(message)
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={encoded_msg}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return response.getcode() == 200
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")
        return False

def get_google_news(keyword="", limit=3):
    try:
        if keyword:
            encoded_kw = urllib.parse.quote(keyword)
            url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        news_list = []
        for item in root.findall('./channel/item')[:limit]:
            title = item.find('title').text
            link = item.find('link').text
            news_list.append((title, link))
        return news_list
    except Exception as e:
        return []

def get_weather_info(location="서울"):
    try:
        encoded_loc = urllib.parse.quote(location + " 날씨")
        url = f"https://search.naver.com/search.naver?query={encoded_loc}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        temp_match = re.search(r'현재 온도</span>(.*?)(?:°|℃|</span>)', html)
        weather_match = re.search(r'<span class="weather before_slash">(.*?)</span>', html)
        dust_match = re.search(r'미세먼지</strong>.*?<span class="txt">(.*?)</span>', html, re.S)
        temp = temp_match.group(1).strip() if temp_match else "알 수 없음"
        weather = weather_match.group(1).strip() if weather_match else "알 수 없음"
        dust = dust_match.group(1).strip() if dust_match else "알 수 없음"
        return temp, weather, dust
    except Exception:
        return "오류", "오류", "오류"

def main():
    output = []
    anniversaries = {"01-01": "신정", "03-01": "3·1절", "05-05": "어린이날", "06-06": "현충일", "08-15": "광복절", "10-03": "개천절", "10-09": "한글날", "12-25": "크리스마스"}
    
    current_time = datetime.datetime.now()
    month_day = current_time.strftime("%m-%d")
    
    output.append(f"🔔 [데일리 브리핑] {current_time.strftime('%Y-%m-%d %H:%M')}")
    
    if month_day in anniversaries:
        output.append(f"🎉 오늘은 {anniversaries[month_day]}입니다!")
    
    temp, weather, dust = get_weather_info("제주")
    output.append(f"\n[🌤️ 제주 날씨]\n🌡️ 온도: {temp}℃\n☁️ 상태: {weather}\n😷 미세먼지: {dust}")

    output.append("\n[📰 주요 뉴스]")
    head_news = get_google_news(limit=2)
    jeju_news = get_google_news(keyword="제주", limit=1)
    for idx, (title, link) in enumerate(head_news + jeju_news, 1):
        output.append(f"{idx}. {title}\n🔗 {link}")

    full_message = "\n".join(output)
    print(full_message)
    send_telegram(full_message)

if __name__ == "__main__":
    main()
