import time
import json
import random
import argparse
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# .env dosyasını yükle
load_dotenv()

def random_sleep():
    """Random bekleme süresi"""
    time.sleep(random.uniform(2, 5))

def get_all_variants(page, asin):
    """Verilen ASIN'in tüm varyasyonlarını bulur"""
    print(f"\n🔍 ASIN {asin} için varyasyonlar kontrol ediliyor...")
    url = f"https://www.amazon.com/dp/{asin}"
    print(f"📌 Detay URL: {url}")
    
    # Sayfaya git ve yüklenene kadar bekle
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        random_sleep()
        
        # Bot korumasını aşmak için scroll
        page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        page.mouse.wheel(delta_x=0, delta_y=random.randint(300, 700))
        random_sleep()
        
        variants = set()
        variants.add(asin)  # Mevcut ASIN'i ekle
        
        # JavaScript ile varyasyonları bul
        script = """
        () => {
            const variants = new Set();
            
            // Script içindeki varyasyonları bul
            const scripts = document.getElementsByTagName('script');
            for (const script of scripts) {
                const text = script.textContent || '';
                if (text.includes('dimensionValuesDisplayData')) {
                    const matches = text.match(/B[A-Z0-9]{9}/g) || [];
                    matches.forEach(match => variants.add(match));
                }
            }
            
            // Varyasyon butonlarından ASIN'leri topla
            document.querySelectorAll('[data-defaultasin]').forEach(el => {
                const asin = el.getAttribute('data-defaultasin');
                if (asin) variants.add(asin);
            });
            
            // Parent ASIN'i bul
            const parentElement = document.querySelector('[data-parent-asin]');
            if (parentElement) {
                const parentAsin = parentElement.getAttribute('data-parent-asin');
                if (parentAsin) variants.add(parentAsin);
            }
            
            return Array.from(variants);
        }
        """
        
        found_variants = page.evaluate(script) or []
        if found_variants:
            print("\n🔍 Varyasyonlar:")
            for variant in found_variants:
                if variant not in variants and len(variant) == 10 and variant.startswith('B'):
                    print(f"   - {variant}")
                    variants.add(variant)

        variants = list(variants)
        print(f"\n✅ Toplam {len(variants)} varyasyon bulundu")
        return variants
        
    except Exception as e:
        print(f"\n❌ Sayfa yükleme hatası: {str(e)}")
        return [asin]

def find_first_variant_position(playwright, browser_ws, keyword, variants):
    """Verilen varyasyonlardan ilk bulunanın pozisyonunu döndürür"""
    print(f"\n🔎 '{keyword}' aramasında {len(variants)} varyasyon aranıyor...")
    
    page_num = 1
    total_position = 0
    found_variant = None
    found_data = None
    
    while page_num <= 10:  # İlk 10 sayfaya bakalım
        try:
            # Her sayfa için yeni bir bağlantı
            print(f"\n🔄 Sayfa {page_num} için yeni bağlantı kuruluyor...")
            browser = playwright.chromium.connect_over_cdp(browser_ws)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Arama URL'ini oluştur
            if page_num == 1:
                url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
            else:
                url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}&page={page_num}"
            
            print(f"📄 Sayfa {page_num} kontrol ediliyor...")
            print(f"📌 URL: {url}")
            
            # Sayfaya git ve yüklenene kadar bekle
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            random_sleep()
            
            # Bot korumasını aşmak için scroll
            page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            page.mouse.wheel(delta_x=0, delta_y=random.randint(300, 700))
            random_sleep()
            
            # JavaScript ile ürünleri ve pozisyonları bul
            script = """
                () => {
                const products = [];
                document.querySelectorAll('[data-asin]').forEach((el, index) => {
                    const asin = el.getAttribute('data-asin');
                    if (asin) {
                        products.push({
                            asin: asin,
                            position: index + 1,
                            sponsored: el.querySelector('[data-component-type="sp-sponsored-result"]') !== null
                        });
                    }
                });
                return products;
            }
            """
            
            products = page.evaluate(script)
            
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
                    browser.close()
                    return found_data
            
            if found_variant:
                break
                
            # Bağlantıyı kapat
            browser.close()
            print(f"🔄 Sayfa {page_num} bağlantısı kapatıldı.")
            
            page_num += 1
            random_sleep()
            
        except Exception as e:
            print(f"\n❌ Sayfa {page_num} kontrol edilirken hata: {str(e)}")
            if 'browser' in locals():
                browser.close()
                print(f"🔄 Hatalı bağlantı kapatıldı.")
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

def main():
    parser = argparse.ArgumentParser(description='Amazon ASIN Kontrol Aracı')
    parser.add_argument('-k', '--keyword', required=True, help='Arama anahtar kelimesi')
    parser.add_argument('-a', '--asin', required=True, help='Kontrol edilecek ASIN')
    args = parser.parse_args()
    
    # Bright Data bilgilerini al
    bright_data_auth = os.getenv('BRIGHT_DATA_AUTH')
    bright_data_host = os.getenv('BRIGHT_DATA_HOST')
    bright_data_port = int(os.getenv('BRIGHT_DATA_PORT'))
    
    # Bright Data WebSocket URL'ini oluştur
    browser_ws = f"wss://{bright_data_auth}@{bright_data_host}:{bright_data_port}"
    print(f"\n🌐 Bright Data Scraping Browser'a bağlanılıyor...")
    print(f"📍 WebSocket URL: {browser_ws}")
    
with sync_playwright() as p:
    try:
            # Varyasyonları bulmak için ilk bağlantı
            print("\n🔄 Varyasyonlar için bağlantı kuruluyor...")
            browser = p.chromium.connect_over_cdp(browser_ws)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Tüm varyasyonları bul
            variants = get_all_variants(page, args.asin)
            
            # İlk bağlantıyı kapat
            browser.close()
            print("\n🔄 İlk bağlantı kapatıldı.")
            
            # Arama için yeni bağlantı
            print("\n🔄 Arama için yeni bağlantı kuruluyor...")
            browser = p.chromium.connect_over_cdp(browser_ws)
            
            # Varyasyonlardan herhangi birini bulmaya çalış
            result = find_first_variant_position(p, browser_ws, args.keyword, variants)
            
            # Sonuçları JSON formatında kaydet
            output = {
                'keyword': args.keyword,
                'original_asin': args.asin,
                'all_variants': variants,
                'search_results': result
            }
            
            with open('asin_results.json', 'w') as f:
                json.dump(output, f, indent=2)
                print("\n💾 Sonuçlar 'asin_results.json' dosyasına kaydedildi.")
            
            # Son bağlantıyı kapat
            browser.close()

    except Exception as e:
            print(f"\n❌ Genel Hata: {str(e)}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
