import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError
from dotenv import load_dotenv
from datetime import datetime
from parser import extract_product_data, analyze_products
import argparse
import json
import time

async def save_html_content(content, filename):
    os.makedirs('data', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"HTML içeriği kaydedildi: {filename}")

async def wait_for_page_load(page):
    """Sayfanın tam olarak yüklenmesini bekler"""
    print("Sayfa yükleniyor...", flush=True)
    try:
        # Sayfanın yüklenmesini bekle
        await page.wait_for_load_state("domcontentloaded", timeout=60000)
        
        # Ürün kartlarının yüklenmesini bekle
        await page.wait_for_selector('[data-asin]', state="visible", timeout=60000)
        
        # Lazy-load edilen görsellerin yüklenmesi için sayfayı aşağı kaydır
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)  # Ek yüklenme süresi
        
        # Tekrar yukarı çık
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        
        print("Sayfa tamamen yüklendi", flush=True)
    except TimeoutError:
        print("Sayfa yükleme zaman aşımı - mevcut içerikle devam ediliyor", flush=True)

async def main():
    # Argüman parser'ı oluştur
    parser = argparse.ArgumentParser(description='Amazon ürün arama ve veri çekme aracı')
    parser.add_argument('--search', '-s', type=str, default='red car',
                      help='Aranacak ürün adı (varsayılan: red car)')
    args = parser.parse_args()
    
    search_term = args.search
    print(f"Aranacak ürün: {search_term}", flush=True)

    try:
        # Bright Data bilgilerini yükle
        load_dotenv()
        auth = os.getenv('BRIGHT_DATA_AUTH')
        host = os.getenv('BRIGHT_DATA_HOST')
        port = os.getenv('BRIGHT_DATA_PORT')

        if not all([auth, host, port]):
            raise ValueError("Bright Data bilgileri eksik. Lütfen .env dosyasını kontrol edin.")

        proxy_url = f"wss://{auth}@{host}:{port}"
        print("Proxy bağlantısı kuruluyor...", flush=True)

        async with async_playwright() as p:
            # Tarayıcıyı Bright Data proxy'si ile başlat
            browser = await p.chromium.connect_over_cdp(proxy_url)
            page = await browser.new_page()

            # Amazon'a git
            print("Amazon ana sayfasına gidiliyor...", flush=True)
            try:
                await page.goto('https://www.amazon.com', 
                              wait_until="domcontentloaded",
                              timeout=60000)
                print("Amazon ana sayfasına gidildi", flush=True)
            except TimeoutError:
                print("Ana sayfa yükleme zaman aşımı - devam ediliyor", flush=True)

            # Arama kutusunu bekle ve arama yap
            print(f"'{search_term}' için arama yapılıyor...", flush=True)
            try:
                await page.wait_for_selector('#twotabsearchtextbox', timeout=60000)
                await page.fill('#twotabsearchtextbox', search_term)
                await page.click('#nav-search-submit-button')
            except TimeoutError:
                print("Arama kutusu bulunamadı", flush=True)
                raise
            
            # Sayfanın tam olarak yüklenmesini bekle
            await wait_for_page_load(page)
            print(f"'{search_term}' araması tamamlandı", flush=True)

            # HTML içeriğini kaydet
            print("HTML içeriği kaydediliyor...", flush=True)
            content = await page.content()
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            html_filename = f'data/amazon_{search_term}_search_page_{timestamp}.html'
            await save_html_content(content, html_filename)

            # Ürün verilerini çek ve kaydet
            print("Ürün verileri çekiliyor...", flush=True)
            products = extract_product_data(html_filename)
            json_filename = f'data/amazon_{search_term}_products_{timestamp}.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            print(f"\nToplam {len(products)} ürün bulundu", flush=True)
            print("\nÜrün Analizi:", flush=True)
            analyze_products(products)
            print(f"\nAyrıntılı veriler {json_filename} dosyasına kaydedildi.", flush=True)

            await browser.close()

    except Exception as e:
        print(f"Hata oluştu: {str(e)}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())