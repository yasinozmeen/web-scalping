import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError
from datetime import datetime
from parser import extract_product_data, analyze_products
import argparse
import json
import time
import psutil
from bs4 import BeautifulSoup

def get_network_usage():
    net_io = psutil.net_io_counters()
    return {
        'gönderilen': net_io.bytes_sent,
        'alınan': net_io.bytes_recv,
        'toplam': net_io.bytes_sent + net_io.bytes_recv
    }

def format_bytes(bytes):
    for unit in ['B', 'KB', 'MB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} GB"

def log_network_usage(start_usage, current_usage, step_name):
    sent_diff = current_usage['gönderilen'] - start_usage['gönderilen']
    recv_diff = current_usage['alınan'] - start_usage['alınan']
    total_diff = current_usage['toplam'] - start_usage['toplam']
    
    print(f"\n{step_name} - Network Kullanımı:")
    print(f"Gönderilen: {format_bytes(sent_diff)}")
    print(f"Alınan: {format_bytes(recv_diff)}")
    print(f"Toplam: {format_bytes(total_diff)}")

def clean_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Ana ürün listesini bul
    search_results = soup.find('div', {'class': 's-search-results'})
    if search_results:
        # Yeni temiz div oluştur
        clean_results = soup.new_tag('div')
        clean_results['class'] = 's-search-results'
        
        # Tüm ürün kartlarını bul
        product_cards = search_results.find_all('div', {'data-asin': True})
        index_counter = 1
        
        for card in product_cards:
            # Sponsorlu/Reklam kontrolü
            sponsored_elem = card.find('span', string=lambda x: x and 'Sponsored' in str(x))
            sponsored_class = card.find(class_=lambda x: x and 'sponsored' in str(x).lower())
            
            # Eğer sponsorlu değilse
            if not sponsored_elem and not sponsored_class and card.get('data-asin'):
                # Kartın kopyasını al
                clean_card = card
                
                # Önce gereksiz içerikleri temizle
                for tag in clean_card.find_all(['script', 'style', 'iframe', 'noscript', 'svg']):
                    tag.decompose()
                
                # Tüm resimleri kaldır
                for img in clean_card.find_all('img'):
                    img.decompose()
                
                # Video ve medya içeriklerini kaldır
                for tag in clean_card.find_all(['video', 'audio', 'source', 'picture']):
                    tag.decompose()
                
                # Gereksiz attributeları temizle
                for tag in clean_card.find_all(True):
                    # Korunacak attributelar
                    keep_attrs = ['data-asin', 'data-component-type', 'class']
                    
                    # Mevcut attributeları kontrol et
                    attrs = dict(tag.attrs)
                    for attr in attrs:
                        # Resim ve stil ile ilgili attributeları kaldır
                        if attr not in keep_attrs:
                            del tag[attr]
                    
                    # Class'ları temizle ama önemli olanları koru
                    if tag.has_attr('class'):
                        classes = tag.get('class', [])
                        tag['class'] = [c for c in classes if c in ['a-price-whole', 'a-text-normal']]
                
                # Yeni index değerini ekle
                clean_card['data-index'] = str(index_counter)
                index_counter += 1
                
                clean_results.append(clean_card)
        
        # Boşlukları ve gereksiz karakterleri temizle
        return str(clean_results).replace('\n', '').replace('  ', ' ')
    return ""

async def save_html_content(content, filename):
    os.makedirs('data', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"HTML içeriği kaydedildi: {filename}")

async def wait_for_page_load(page):
    """Sayfanın tam olarak yüklenmesini bekler"""
    print("Sayfa yükleniyor...", flush=True)
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=60000)
        await page.wait_for_selector('[data-asin]', state="visible", timeout=60000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        print("Sayfa tamamen yüklendi", flush=True)
    except TimeoutError:
        print("Sayfa yükleme zaman aşımı - mevcut içerikle devam ediliyor", flush=True)

async def main():
    start_time = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--search', '-s', type=str, required=True)
    args = parser.parse_args()
    
    start_network_usage = get_network_usage()
    step_network_usage = start_network_usage.copy()
    
    # Bright Data bilgileri
    username = "brd-customer-hl_b2cfbf43-zone-scraping_browser1"
    password = "c7liyhvlkal7"
    host = "brd.superproxy.io"
    port = "9222"

    try:
        async with async_playwright() as p:
            print("Scraping başlatılıyor...", flush=True)
            
            # Browser başlatma öncesi network kullanımı
            current_usage = get_network_usage()
            log_network_usage(step_network_usage, current_usage, "Browser Başlatma Öncesi")
            step_network_usage = current_usage.copy()
            
            session_id = f"session_{int(time.time())}"
            ws_url = f"wss://{username}-session-{session_id}:{password}@{host}:{port}"
            
            browser = await p.chromium.connect_over_cdp(
                ws_url,
                timeout=60000,
            )

            # Browser başlatma sonrası network kullanımı
            current_usage = get_network_usage()
            log_network_usage(step_network_usage, current_usage, "Browser Başlatma")
            step_network_usage = current_usage.copy()

            context = await browser.new_context(
                viewport={'width': 1366, 'height': 768}
            )

            # Gereksiz içerikleri engelle
            await context.route("**/*", lambda route: route.continue_() if route.request.resource_type == "document" else route.abort())

            page = await context.new_page()

            # Direkt arama URL'ine git (.com'a geçtik)
            search_url = f"https://www.amazon.com/s?k={args.search}&ref=sr_pg_1"
            
            # Sadece HTML yükle
            response = await page.goto(
                search_url,
                timeout=60000,
                wait_until='domcontentloaded'
            )

            # Sadece s-search-results div'ini seç ve al
            content = await page.evaluate("""
                () => {
                    const results = document.querySelector('div.s-search-results');
                    if (!results) return '';
                    
                    // Sadece gerekli yapıyı kopyala
                    const clean = results.cloneNode(true);
                    
                    // Tüm medya içeriklerini kaldır
                    clean.querySelectorAll('img,svg,video,iframe,style,script').forEach(el => el.remove());
                    
                    // Sponsorlu içerikleri kaldır
                    clean.querySelectorAll('[data-component-type="sp-sponsored-result"]').forEach(el => el.remove());
                    
                    // Sadece gerekli attributeları tut
                    clean.querySelectorAll('*').forEach(el => {
                        const keepAttrs = ['data-asin', 'data-component-type', 'class'];
                        Array.from(el.attributes).forEach(attr => {
                            if (!keepAttrs.includes(attr.name)) {
                                el.removeAttribute(attr.name);
                            }
                        });
                        
                        // Class'ları da temizle
                        if (el.hasAttribute('class')) {
                            const classes = el.getAttribute('class').split(' ');
                            const keepClasses = ['s-search-results', 'a-price-whole', 'a-text-normal'];
                            el.setAttribute('class', classes.filter(c => keepClasses.includes(c)).join(' '));
                            if (!el.getAttribute('class')) el.removeAttribute('class');
                        }
                    });
                    
                    // Boş elementleri kaldır
                    clean.querySelectorAll('*').forEach(el => {
                        if (!el.children.length && !el.textContent.trim()) {
                            el.remove();
                        }
                    });
                    
                    return clean.outerHTML;
                }
            """)
            
            # Gereksiz boşlukları ve satır sonlarını kaldır
            content = ' '.join(content.split())
            content = content.replace('> <', '><')
            
            # İçerik alma sonrası network kullanımı
            current_usage = get_network_usage()
            log_network_usage(step_network_usage, current_usage, "İçerik Alma")
            step_network_usage = current_usage.copy()

            # HTML'i temizle ve kaydet
            clean_content = clean_html(content)
            
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            html_filename = f'data/amazon_{args.search}_search_page_{timestamp}.html'
            
            os.makedirs('data', exist_ok=True)
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(clean_content)

            products = extract_product_data(html_filename)
            
            json_filename = f'data/amazon_{args.search}_products_{timestamp}.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)

            html_size = os.path.getsize(html_filename)
            end_network_usage = get_network_usage()
            total_usage = end_network_usage['toplam'] - start_network_usage['toplam']
            end_time = time.time()
            
            print("\nİşlem Özeti:")
            print(f"Süre: {end_time - start_time:.2f} saniye")
            print(f"İnternet Kullanımı: {format_bytes(total_usage)}")
            print(f"HTML Dosya Boyutu: {format_bytes(html_size)}")
            print(f"Organik Ürün Sayısı: {len(products)} adet")
            print(f"Dosya: {json_filename}")

            # Final network kullanımı
            end_network_usage = get_network_usage()
            print("\nToplam Network Kullanımı:")
            print(f"Başlangıç: {format_bytes(start_network_usage['toplam'])}")
            print(f"Bitiş: {format_bytes(end_network_usage['toplam'])}")
            print(f"Fark: {format_bytes(end_network_usage['toplam'] - start_network_usage['toplam'])}")
            
            print("\nDetaylı Network Kullanımı:")
            print(f"Toplam Gönderilen: {format_bytes(end_network_usage['gönderilen'] - start_network_usage['gönderilen'])}")
            print(f"Toplam Alınan: {format_bytes(end_network_usage['alınan'] - start_network_usage['alınan'])}")

            await browser.close()

    except Exception as e:
        print(f"Hata: {str(e)}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
