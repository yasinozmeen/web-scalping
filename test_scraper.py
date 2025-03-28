import requests
import time

def test_scraper_api():
    """ScraperAPI'yi test et"""
    api_key = '66290f8b3400b539397b3de6e8dcdae9'
    test_url = 'https://www.amazon.com/dp/B0DQYQKZQ2'
    
    print("🔄 ScraperAPI Test Başlıyor...")
    print(f"📍 Test URL: {test_url}")
    
    try:
        # İlk deneme
        print("\n📝 İlk Deneme:")
        payload = {
            'api_key': api_key,
            'url': test_url,
            'render': 'true',
            'timeout': 60000,
            'keep_headers': 'true',
            'premium': 'true',
            'country_code': 'us'
        }
        r = requests.get('https://api.scraperapi.com/', params=payload)
        print(f"📊 Durum Kodu: {r.status_code}")
        print(f"⏱️ Yanıt Süresi: {r.elapsed.total_seconds():.2f} saniye")
        
        # 2 saniye bekle
        time.sleep(2)
        
        # İkinci deneme
        print("\n📝 İkinci Deneme:")
        r = requests.get('https://api.scraperapi.com/', params=payload)
        print(f"📊 Durum Kodu: {r.status_code}")
        print(f"⏱️ Yanıt Süresi: {r.elapsed.total_seconds():.2f} saniye")
        
        # 2 saniye bekle
        time.sleep(2)
        
        # Üçüncü deneme
        print("\n📝 Üçüncü Deneme:")
        r = requests.get('https://api.scraperapi.com/', params=payload)
        print(f"📊 Durum Kodu: {r.status_code}")
        print(f"⏱️ Yanıt Süresi: {r.elapsed.total_seconds():.2f} saniye")
        
        print("\n✅ Test Tamamlandı!")
        
    except Exception as e:
        print(f"\n❌ Hata: {str(e)}")

if __name__ == "__main__":
    test_scraper_api() 