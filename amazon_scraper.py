import os
from playwright.sync_api import sync_playwright, TimeoutError, Error
from dotenv import load_dotenv
import json
from datetime import datetime
import time

# Load environment variables
load_dotenv()

TIMEOUTS = {
    'page_load': 180000,  
    'navigation': 90000   
}
#agdkjfhsad
def setup_browser_context(playwright):
    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='tr-TR',
            timezone_id='Europe/Istanbul'
        )
        page = context.new_page()
        return browser, context, page
    except TimeoutError:
        print("❌ Tarayıcı başlatma zsasdaman asdfsadsaşımına uğradı!")
        raise
    except Error as e:
        print(f"❌ Tarayıcı başlatma hatası: {str(e)}")
        raise

def scrape_amazon_product(page, url):
    try:
        print(f"🔍 Ürün sayfası yükleniyor: {url}")
        
        # URL'yi temizle - sadece ürün ID'sini al
        clean_url = url.split('/dp/')[0] + '/dp/' + url.split('/dp/')[1].split('/')[0]
        print(f"🔗 Temizlenmiş URL: {clean_url}")
        
        # Temizlenmiş URL ile sayfaya git
        page.goto(clean_url, timeout=TIMEOUTS['page_load'])
        
        # Sayfa yüklenme stratejisini değiştir
        print("⌛ Sayfa yükleniyor...")
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_selector("#productTitle", timeout=30000)
        
        product_data = {}
        
        # Başlık
        if page.locator("#productTitle").is_visible():
            product_data["title"] = page.locator("#productTitle").inner_text().strip()
            print("✅ Başlık alındı")
        
        # Fiyat - birden fazla seçici dene
        price_selectors = [
            "span.a-price-whole",
            ".a-price .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice"
        ]
        
        for selector in price_selectors:
            try:
                if page.locator(selector).first.is_visible():
                    product_data["price"] = page.locator(selector).first.inner_text().strip()
                    print("✅ Fiyat alındı")
                    break
            except:
                continue
        
        if "price" not in product_data:
            product_data["price"] = "Fiyat bulunamadı"
        
        # Değerlendirme
        if page.locator("#acrPopover").is_visible():
            product_data["rating"] = page.locator("#acrPopover").get_attribute("title")
            print("✅ Değerlendirme alındı")
        else:
            product_data["rating"] = "Değerlendirme bulunamadı"
        
        # Stok durumu
        if page.locator("#availability").is_visible():
            product_data["availability"] = page.locator("#availability").inner_text().strip()
            print("✅ Stok durumu alındı")
        else:
            product_data["availability"] = "Stok durumu bulunamadı"
        
        product_data["timestamp"] = datetime.now().isoformat()
        product_data["url"] = clean_url
        
        print("✅ Tüm ürün bilgileri başarıyla çekildi!")
        return product_data
        
    except TimeoutError:
        print("❌ Sayfa yükleme zaman aşımına uğradı!")
        print("🔄 Yeniden deneniyor...")
        time.sleep(5)
        try:
            return scrape_amazon_product(page, url)  # Bir kez daha dene
        except:
            return None
    except Error as e:
        print(f"❌ Veri çekme hatası: {str(e)}")
        return None

def save_product_data(data, filename="product_data.json"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Veriler kaydedildi: {filename}")
    except Exception as e:
        print(f"❌ Veri kaydetme hatası: {str(e)}")

def main():
    print("🔗 Tarayıcı başlatılıyor...")
    
    try:
        with sync_playwright() as p:
            browser = None
            context = None
            page = None

            try:
                browser, context, page = setup_browser_context(p)

                print("🌐 Amazon ana sayfasına gidiliyor...")
                page.goto("https://www.amazon.com.tr", timeout=TIMEOUTS['page_load'])
                time.sleep(3)

                print("🔍 Ürün aranıyor...")
                page.fill("#twotabsearchtextbox", "airpods")
                page.keyboard.press("Enter")
                time.sleep(5)

                print("📦 Ürün sonuçları bekleniyor...")
                page.wait_for_selector("[data-component-type='s-search-result']", timeout=20000)
                time.sleep(3)

                print("📦 İlk ürün seçiliyor...")
                try:
                    # Birden fazla seçiciyi sırayla dene
                    selectors = [
                        "h2 a.a-link-normal",  # Yeni ana seçici
                        ".a-link-normal.s-underline-text",  # Alternatif 1
                        ".s-image",  # Alternatif 2 (ürün resmine tıklama)
                        ".a-size-mini a"  # Alternatif 3
                    ]

                    product_found = False
                    for selector in selectors:
                        try:
                            print(f"🔍 Seçici deneniyor: {selector}")
                            products = page.locator(selector)
                            if products.count() > 0:
                                print(f"✅ Ürün bulundu: {selector}")
                                # İlk görünür ürünü bul ve tıkla
                                for i in range(products.count()):
                                    if products.nth(i).is_visible():
                                        products.nth(i).click()
                                        product_found = True
                                        time.sleep(3)
                                        break
                            if product_found:
                                break
                        except Exception as e:
                            print(f"⚠️ Bu seçici başarısız oldu: {selector}")
                            continue

                    if not product_found:
                        raise Exception("Hiçbir ürün bulunamadı")

                except Exception as e:
                    print(f"⚠️ Ürün seçme hatası: {str(e)}")
                    raise

                product_url = page.url
                print(f"🔗 Ürün URL'si: {product_url}")

                product_data = scrape_amazon_product(page, product_url)

                if product_data:
                    save_product_data(product_data)
                else:
                    raise Exception("Ürün bilgileri çekilemedi!")
                    
            finally:
                if page:
                    try:
                        page.close()
                    except:
                        pass
                if context:
                    try:
                        context.close()
                    except:
                        pass
                if browser:
                    try:
                        browser.close()
                    except:
                        pass
                print("🔒 Tüm bağlantılar kapatıldı.")

    except Exception as e:
        print(f"❌ Beklenmeyen bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    main()