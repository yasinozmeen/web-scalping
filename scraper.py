import time
import json
import random
import argparse
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# .env dosyasını yükle
load_dotenv()

def random_sleep():
    """Random bekleme süresi"""
    time.sleep(random.uniform(2, 5))

def get_scraper_session(api_key):
    """ScraperAPI için session oluştur"""
    session = requests.Session()
    return session

def scrape_url(session, url, api_key):
    """ScraperAPI ile URL'i çek"""
    scraper_url = 'http://api.scraperapi.com'
    params = {
        'api_key': api_key,
        'url': url,
        'render': 'true'
    }
    print(f"\n🔄 ScraperAPI isteği yapılıyor...")
    print(f"📍 URL: {url}")
    response = session.get(scraper_url, params=params)
    print(f"📊 Durum Kodu: {response.status_code}")
    return response

def get_all_variants(session, api_key, asin):
    """Verilen ASIN'in tüm varyasyonlarını bulur"""
    print(f"\n🔍 ASIN {asin} için varyasyonlar kontrol ediliyor...")
    url = f"https://www.amazon.com/dp/{asin}"
    
    try:
        # ScraperAPI ile sayfayı çek
        response = scrape_url(session, url, api_key)
        if response.status_code != 200:
            print(f"\n❌ Sayfa çekme hatası: {response.status_code}")
            return [asin]
            
        soup = BeautifulSoup(response.text, 'lxml')
        variants = set()
        variants.add(asin)  # Mevcut ASIN'i ekle
        
        # Script içindeki varyasyonları bul
        for script in soup.find_all('script'):
            text = script.string or ''
            if 'dimensionValuesDisplayData' in text:
                import re
                matches = re.findall(r'B[A-Z0-9]{9}', text)
                for match in matches:
                    variants.add(match)
        
        # Varyasyon butonlarından ASIN'leri topla
        for element in soup.find_all(attrs={'data-defaultasin': True}):
            variant_asin = element.get('data-defaultasin')
            if variant_asin:
                variants.add(variant_asin)
        
        # Parent ASIN'i bul
        parent_element = soup.find(attrs={'data-parent-asin': True})
        if parent_element:
            parent_asin = parent_element.get('data-parent-asin')
            if parent_asin:
                variants.add(parent_asin)
        
        variants = list(filter(lambda x: len(x) == 10 and x.startswith('B'), variants))
        print(f"\n✅ Toplam {len(variants)} varyasyon bulundu")
        if variants:
            print("\n🔍 Varyasyonlar:")
            for variant in variants:
                print(f"   - {variant}")
                
        return variants
        
    except Exception as e:
        print(f"\n❌ Sayfa işleme hatası: {str(e)}")
        return [asin]

def find_first_variant_position(session, api_key, keyword, variants):
    """Verilen varyasyonlardan ilk bulunanın pozisyonunu döndürür"""
    print(f"\n🔎 '{keyword}' aramasında {len(variants)} varyasyon aranıyor...")
    
    page_num = 1
    total_position = 0
    found_variant = None
    found_data = None
    
    while page_num <= 10:  # İlk 10 sayfaya bakalım
        try:
            # Arama URL'ini oluştur
            if page_num == 1:
                url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
            else:
                url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}&page={page_num}"
            
            print(f"\n📄 Sayfa {page_num} kontrol ediliyor...")
            
            # ScraperAPI ile sayfayı çek
            response = scrape_url(session, url, api_key)
            if response.status_code != 200:
                print(f"\n❌ Sayfa çekme hatası: {response.status_code}")
                page_num += 1
                continue
                
            soup = BeautifulSoup(response.text, 'lxml')
            products = []
            
            # Ürünleri bul
            for index, element in enumerate(soup.find_all(attrs={'data-asin': True}), 1):
                asin = element.get('data-asin')
                if asin:
                    sponsored = bool(element.find(attrs={'data-component-type': 'sp-sponsored-result'}))
                    products.append({
                        'asin': asin,
                        'position': index,
                        'sponsored': sponsored
                    })
            
            print(f"📊 Bu sayfada {len(products)} ürün bulundu")
            
            for product in products:
                total_position += 1
                if product['asin'] in variants:
                    found_variant = product['asin']
                    found_data = {
                        'found': True,
                        'found_variant': product['asin'],
                        'page': page_num,
                        'page_position': product['position'],
                        'total_position': total_position,
                        'sponsored': product['sponsored']
                    }
                    print(f"\n✅ Varyasyon bulundu: {product['asin']}")
                    print(f"📊 Sayfa: {page_num}")
                    print(f"📊 Sayfa içi pozisyon: {product['position']}")
                    print(f"📊 Genel pozisyon: {total_position}")
                    print(f"🏷️ Sponsorlu: {'Evet' if product['sponsored'] else 'Hayır'}")
                    return found_data
            
            if found_variant:
                break
                
            page_num += 1
            random_sleep()
            
        except Exception as e:
            print(f"\n❌ Sayfa {page_num} kontrol edilirken hata: {str(e)}")
            page_num += 1
            continue
    
    print("\n❌ Hiçbir varyasyon bulunamadı!")
    return {
        'found': False,
        'found_variant': None,
        'page': None,
        'page_position': None,
        'total_position': None,
        'sponsored': None
    }

def process_asin(session, api_key, asin, title):
    """Tek bir ASIN'i işle"""
    print(f"\n{'='*50}")
    print(f"📦 ASIN: {asin}")
    print(f"📝 Başlık: {title}")
    print(f"{'='*50}")
    
    try:
        # Varyasyonları bul
        variants = get_all_variants(session, api_key, asin)
        
        if variants:
            # İlk bulunan varyasyonun pozisyonunu bul
            result = find_first_variant_position(session, api_key, title, variants)
            
            # Sonuçları kaydet
            result['asin'] = asin
            result['title'] = title
            
            return result
        
    except Exception as e:
        print(f"\n❌ Genel hata: {str(e)}")
        return {
            'asin': asin,
            'title': title,
            'error': str(e)
        }

def main():
    # Komut satırı argümanlarını parse et
    parser = argparse.ArgumentParser(description='Amazon ASIN Scraper')
    parser.add_argument('-a', '--asin', help='Tek bir ASIN için arama yap')
    parser.add_argument('-k', '--keyword', help='Arama kelimesi')
    args = parser.parse_args()

    # .env dosyasından API anahtarını al
    load_dotenv()
    api_key = os.getenv('SCRAPER_API_KEY')
    if not api_key:
        print("❌ SCRAPER_API_KEY bulunamadı!")
        return

    print(f"\n🔑 API Anahtarı: {api_key}\n")

    # Session oluştur
    session = get_scraper_session(api_key)

    # Tek ASIN için arama yapılıyorsa
    if args.asin and args.keyword:
        print(f"\n==================================================")
        print(f"📦 ASIN: {args.asin}")
        print(f"📝 Başlık: {args.keyword}")
        print(f"==================================================\n")
        
        result = process_asin(session, api_key, args.asin, args.keyword)
        if result:
            print("\n✅ Sonuçlar asin_results.json dosyasına kaydedildi.")
        return

    # Tüm ASIN'ler için arama yap
    asins = [
        ("B0DQYQKZQ2", "bounty paper towels"),
        ("B0DF8RSVJK", "scott paper towels"),
        ("B0DNTQ2YNT", "storage organizer"),
        ("B0DN8C9MTN", "paper bowls"),
        ("B0DLT4GBST", "jello shot cups"),
        ("B0DP2D8ZJT", "air fryer liners"),
        ("B0DSJW8SFG", "ice cream maker"),
        ("B0DRS9YN56", "espresso machine"),
        ("B0DRTR6F12", "coffee pods"),
        ("B0DTJR3HTL", "cream maker pints")
    ]

    results = []
    for i, (asin, title) in enumerate(asins, 1):
        print(f"\n==================================================")
        print(f"📦 ASIN: {asin}")
        print(f"📝 Başlık: {title}")
        print(f"==================================================\n")
        
        result = process_asin(session, api_key, asin, title)
        if result:
            results.append(result)
            
            # Her 5 ASIN'de bir sonuçları kaydet
            if i % 5 == 0:
                save_results(results)
                print(f"\n✅ {i} ASIN için sonuçlar kaydedildi.")
                results = []  # Sonuçları temizle
                
        # Her ASIN arasında 2-5 saniye bekle
        time.sleep(random.uniform(2, 5))
    
    # Kalan sonuçları kaydet
    if results:
        save_results(results)
        print(f"\n✅ Kalan sonuçlar kaydedildi.")

if __name__ == "__main__":
    main()
