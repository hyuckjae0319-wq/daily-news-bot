import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import sys
import re
import os

# 1. 보안 설정
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
    except Exception:
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
    # 요청하신 기념일 및 생일 목록
    anniversaries = {
        "01-01": "새해 첫날", 
        "03-01": "3·1절", 
        "03-19": "혁재 생일", 
        "06-03": "내생일", 
        "08-15": "광복절", 
        "09-17": "오빠생일", 
        "10-03": "개천절", 
        "10-09": "한글날", 
        "11-29": "혁준이 생일", 
        "12-03": "도연이 생일", 
        "12-25": "크리스마스"
    }
    
    current_time = datetime.datetime.now()
    month_day = current_time.strftime("%m-%d")
    
    output.append(f"🔔 [데일리 브리핑] {current_time.strftime('%Y-%m-%d %H:%M')}\n")
    
    # 1. 기념일 체크 (요청하신 문구 적용)
    if month_day in anniversaries:
        output.append(f"🎉 오늘은 {anniversaries[month_day]}입니다! 뜻깊은 하루 보내세요.\n")
    else:
        output.append("오늘은 특별히 지정된 기념일은 없지만, 행복한 하루 보내시길 바랍니다!\n")
    
    # 2. 날씨 정보
    temp, weather, dust = get_weather_info("제주")
    output.append(f"[🌤️ 제주 날씨]\n🌡️ 온도: {temp}℃\n☁️ 상태: {weather}\n😷 미세먼지: {dust}\n")

    # 3. 주요 뉴스
    output.append("[📰 주요 뉴스]")
    all_news = get_google_news(limit=2) + get_google_news(keyword="제주", limit=1)
    if all_news:
        for idx, (title, link) in enumerate(all_news, 1):
            output.append(f"{idx}. {title}\n🔗 {link}")
    else:
        output.append("최신 뉴스를 가져오지 못했습니다.")

    # 4. 축제 및 행사 정보 (요청하신 문구 적용)
    output.append("\n[🎊 제주 축제/행사 소식]")
    festivals = get_google_news(keyword="제주 축제", limit=2)
    if festivals:
        for idx, (title, link) in enumerate(festivals, 1):
            output.append(f"{idx}. {title}\n🔗 {link}")
    else:
        output.append("오늘은 축제가 없음니다")

    full_message = "\n".join(output)
    print(full_message)
    send_telegram(full_message)

if __name__ == "__main__":
    main()
