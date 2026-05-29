import requests

# =========================
# API KEY (اینجا بگذار)
# =========================
API_KEY = "YOUR_API_KEY"

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

# =========================
# گرفتن بازی‌های تمام شده
# =========================
def get_finished_matches():
    url = f"{BASE_URL}/fixtures?status=FT"
    response = requests.get(url, headers=HEADERS, timeout=30)
    return response.json()

# =========================
# گرفتن بازی‌های زنده
# =========================
def get_live_matches():
    url = f"{BASE_URL}/fixtures?live=all"
    response = requests.get(url, headers=HEADERS, timeout=30)
    return response.json()

# =========================
# گرفتن جدول گروه‌ها / لیگ
# =========================
def get_standings(league_id, season):
    url = f"{BASE_URL}/standings?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    return response.json()