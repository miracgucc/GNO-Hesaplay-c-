import requests
import time
from bs4 import BeautifulSoup

# ------------------- AYARLAR -------------------
TELEGRAM_BOT_TOKEN = "8023283599:AAG18-FgDgZlo9wXmZsvm09RsHHFMYGSyAg"
CHAT_ID = "1244842635"

# Tarayıcıdan aldığın OİS oturum çerezlerini buraya ekle
COOKIES = {
    "PHPSESSID": "favsond5el202btbsb0s9172kv",
    "kullanici_tipi": "2"
}

CHECK_URL = "https://ois.pirireis.edu.tr/ogrenciler/belge/ogrsinavsonuc"

# ------------------- Telegram Mesaj Fonksiyonu -------------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram gönderilemedi:", e)

# ------------------- Sayfa İçeriğini Çek -------------------
def fetch_page():
    try:
        r = requests.get(CHECK_URL, cookies=COOKIES, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("Sayfa alınamadı:", e)
        return ""

# ------------------- Ana Döngü -------------------
def main():
    print("🔍 Sınav sonucu takip botu çalışıyor...")
    last_content = fetch_page()

    while True:
        time.sleep(600)  # Her 60 saniyede bir kontrol
        new_content = fetch_page()

        if new_content != last_content:
            print("📢 Değişiklik algılandı! Telegram gönderiliyor...")
            send_telegram("📢 Sınav sonuçları güncellendi! Kontrol et: " + CHECK_URL)
            last_content = new_content
        else:
            print("Değişiklik yok, bekleniyor...")

if __name__ == "__main__":
    main()
