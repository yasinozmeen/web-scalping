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
    html_content = await page.content()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML içeriği {filename} dosyasına kaydedildi.")

def parse_html_with_bs4(filename):
    with open(filename, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Ürün konteynerini bul
    product_container = soup.find("div", {"class": "s-main-slot"})
    if not product_container:
        print("Ürün konteyneri bulunamadı!")
        return []
    
    products = []
    # Tüm ürün kartlarını bul
    product_cards = product_container.find_all("div", {"data-asin": True})
    
    for card in product_cards:
        try:
            asin = card.get("data-asin")
            if not asin:
                continue
                
            # Başlık
            title_element = card.find("h2", {"class": "a-size-mini"})
            if title_element:
                title = title_element.find("span").get_text().strip()
            else:
                title = "N/A"
            
            # URL
            url_element = card.find("a", {"class": "a-link-normal s-no-outline"})
            url = "https://www.amazon.com" + url_element["href"] if url_element and url_element.get("href") else "N/A"
            
            # Fiyat
            price_element = card.find("span", {"class": "a-price-whole"})
            price = price_element.get_text().strip() if price_element else "N/A"
            
            # Yıldız Puanı
            rating_element = card.find("span", {"class": "a-icon-alt"})
            rating = rating_element.get_text().strip() if rating_element else "N/A"
            
            # Değerlendirme Sayısı
            review_count_element = card.find("span", {"class": "a-size-base s-underline-text"})
            review_count = review_count_element.get_text().strip() if review_count_element else "0"
            
            # Prime Uygunluğu
            prime_element = card.find("i", {"class": "a-icon-prime"})
            is_prime = "Yes" if prime_element else "No"
            
            product = {
                "asin": asin,
                "title": title,
                "url": url,
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "is_prime": is_prime
            }
            products.append(product)
            
        except Exception as e:
            print(f"Ürün bilgileri analiz edilemedi: {str(e)}")
            continue
    
    return products

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
            
            # Amazon ana sayfasına git
            await page.goto("https://www.amazon.com")
            print("Amazon ana sayfasına gidildi.")
            
            # Arama yap
            await page.fill("#twotabsearchtextbox", "laptop")
            await page.click("#nav-search-submit-button")
            print("Arama yapıldı ve sonuçlar bekleniyor...")
            
            # Sayfanın yüklenmesini bekle
            await page.wait_for_selector("div.s-main-slot")
            print("Arama sonuçları yüklendi.")
            
            # HTML içeriğini kaydet
            await save_html_content(page, "amazon_search.html")
            
            # HTML içeriğini analiz et
            products = parse_html_with_bs4("amazon_search.html")
            
            if products:
                print(f"{len(products)} ürün bulundu ve analiz edildi.")
                # Ürün verilerini JSON dosyasına kaydet
                with open("product_data.json", "w", encoding="utf-8") as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)
                print("Ürün verileri product_data.json dosyasına kaydedildi.")
            else:
                print("Hiç ürün bulunamadı!")
            
            await browser.close()
            print("Tarayıcı kapatıldı ve tüm bağlantılar sonlandırıldı.")
            
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())