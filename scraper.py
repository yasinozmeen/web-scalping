import os
from playwright.sync_api import sync_playwright, TimeoutError, Error
from dotenv import load_dotenv
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup
import re
import asyncio
from playwright.async_api import async_playwright
from amazon_selectors import get_selector, is_required, SELECTORS
from parser import extract_product_data

# Load environment variables
load_dotenv()

# Bright Data Configurations
BRIGHT_DATA_USERNAME = os.getenv('BRIGHT_DATA_USERNAME')
BRIGHT_DATA_PASSWORD = os.getenv('BRIGHT_DATA_PASSWORD')
BROWSER_WS = f"wss://{BRIGHT_DATA_USERNAME}:{BRIGHT_DATA_PASSWORD}@brd.superproxy.io:9222"

TIMEOUTS = {
    'page_load': 180000,  
    'navigation': 90000   
}

async def save_html_content(page, filename):
    """HTML içeriğini dosyaya kaydeder."""
    html_content = await page.content()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML içeriği {filename} dosyasına kaydedildi.")

async def main():
    try:
        async with async_playwright() as p:
            # WebSocket bağlantısı için gerekli bilgiler
            auth = os.getenv("BRIGHT_DATA_AUTH")
            host = os.getenv("BRIGHT_DATA_HOST")
            port = os.getenv("BRIGHT_DATA_PORT")
            
            browser = await p.chromium.connect_over_cdp(f"wss://{auth}@{host}:{port}")
            page = await browser.new_page()
            
            print("Tarayıcı başlatıldı ve sayfa oluşturuldu.")
            
            # Arama kelimesi
            search_keyword = "laptop"  # Bu kısmı daha sonra parametre olarak alabiliriz
            
            # Amazon ana sayfasına git
            await page.goto("https://www.amazon.com")
            print("Amazon ana sayfasına gidildi.")
            
            # Arama yap
            await page.fill("#twotabsearchtextbox", search_keyword)
            await page.click("#nav-search-submit-button")
            print(f"'{search_keyword}' için arama yapıldı ve sonuçlar bekleniyor...")
            
            # Sayfanın yüklenmesini bekle
            await page.wait_for_selector(get_selector('product_container'))
            print("Arama sonuçları yüklendi.")
            
            # Zaman damgası oluştur
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # HTML dosya adını oluştur
            html_filename = f"data/amazon_{search_keyword}_search_page_{timestamp}.html"
            
            # HTML içeriğini kaydet
            os.makedirs("data", exist_ok=True)  # data klasörünü oluştur
            await save_html_content(page, html_filename)
            
            # HTML içeriğini analiz et
            products = extract_product_data(html_filename)
            
            # Sonuçları JSON dosyasına kaydet
            output_file = os.path.join("data", f"amazon_{search_keyword}_products_{timestamp}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            print(f"Toplam {len(products)} ürün verisi çekildi ve {output_file} dosyasına kaydedildi.")
            
            await browser.close()
            
    except Exception as e:
        print(f"Bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())