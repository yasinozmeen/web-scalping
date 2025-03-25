import json
import os
from bs4 import BeautifulSoup
import re

def extract_product_data(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    products = []
    index_counter = 1  # Index'i 1'den başlatıyoruz
    
    # Ana ürün listesini bul
    search_results = soup.find('div', {'class': 's-search-results'})
    if not search_results:
        return products

    # Tüm ürün kartlarını bul
    product_cards = search_results.find_all('div', {'data-asin': True})
    
    for card in product_cards:
        # ASIN kontrolü
        if not card.get('data-asin'):
            continue

        # Sponsorlu/Reklam kontrolü
        sponsored_elem = card.find('span', string=lambda x: x and 'Sponsored' in str(x))
        sponsored_class = card.find(class_=lambda x: x and 'sponsored' in str(x).lower())
        
        # Eğer sponsorlu değilse
        if not sponsored_elem and not sponsored_class:
            product = {
                'asin': card['data-asin'],
                'index': index_counter,  # Yeni index değeri
                'is_organic': True
            }
            products.append(product)
            index_counter += 1  # Her organik üründe index'i artır
    
    return products

def analyze_products(products):
    if not products:
        print("Ürün bulunamadı!")
        return
    
    organic_count = sum(1 for p in products if p['is_organic'])
    sponsored_count = len(products) - organic_count
    
    print(f"\nToplam Ürün: {len(products)}")
    print(f"Organik Ürün: {organic_count}")
    print(f"Sponsored Ürün: {sponsored_count}")

def main():
    """Ana fonksiyon"""
    import sys
    
    # En son HTML dosyasını bul
    data_dir = 'data'
    html_files = [f for f in os.listdir(data_dir) if f.endswith('.html')]
    
    if not html_files:
        print("HTML dosyası bulunamadı!")
        return
    
    latest_html = sorted(html_files)[-1]
    html_file_path = os.path.join(data_dir, latest_html)
    
    # Ürün verilerini çek
    products = extract_product_data(html_file_path)
    
    # Sonuçları JSON dosyasına kaydet
    output_file = os.path.join(data_dir, 'product_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"\nToplam {len(products)} ürün bulundu", flush=True)
    print("\nÜrün Analizi:", flush=True)
    sys.stdout.flush()
    analyze_products(products)
    print(f"\nAyrıntılı veriler {output_file} dosyasına kaydedildi.", flush=True)

    print("\nİşlem Özeti:")
    print(f"Süre: {end_time - start_time:.2f} saniye")
    print(f"İnternet Kullanımı: {format_bytes(total_usage)}")
    print(f"HTML Dosya Boyutu: {format_bytes(html_size)}")
    print(f"Sadece Organik Ürün Sayısı: {len(products)} adet")
    print(f"Dosya: {output_file}")

def test_last_data():
    """En son indirilen HTML dosyasından analiz yapar"""
    import sys
    
    # En son HTML dosyasını bul
    data_dir = 'data'
    html_files = [f for f in os.listdir(data_dir) if f.endswith('.html')]
    
    if not html_files:
        print("HTML dosyası bulunamadı!")
        return
    
    latest_html = sorted(html_files)[-1]
    html_file_path = os.path.join(data_dir, latest_html)
    
    # Ürün verilerini çek
    products = extract_product_data(html_file_path)
    
    print(f"\nToplam {len(products)} ürün bulundu", flush=True)
    print("\nÜrün Analizi:", flush=True)
    sys.stdout.flush()
    analyze_products(products)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_last_data()
    else:
        main() 