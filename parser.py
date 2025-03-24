import json
import os
from amazon_selectors import get_selector, get_attributes, get_attribute
from lxml import html

def extract_product_data(html_file_path):
    """HTML dosyasından ürün verilerini çeker"""
    # HTML dosyasını oku
    with open(html_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # lxml tree objesi oluştur
    tree = html.fromstring(content)
    
    # Tüm ürün kartlarını bul
    product_cards = tree.xpath(get_selector('product_card'))
    products = []
    counter = 1  # Sayaç ekle
    
    for card in product_cards:
        try:
            product = {}
            
            # ASIN ve Index
            attributes = get_attributes('product_card')
            if attributes:
                for key, attr in attributes.items():
                    if key == 'index':
                        # Sayaç değerini kullan
                        product[key] = str(counter)
                        counter += 1  # Sayacı artır
                    else:
                        product[key] = card.get(attr, '')
            
            # Organik sonuç mu?
            sponsored_elements = card.xpath('.//span[contains(text(), "Sponsored")]')
            product['is_organic'] = len(sponsored_elements) == 0
            
            # ASIN zorunlu alan
            if not product.get('asin'):
                continue
            
            products.append(product)
            
        except Exception as e:
            print(f"Ürün bilgileri analiz edilemedi: {str(e)}")
            continue
    
    return products

def analyze_products(products):
    """Ürünlerin organik/sponsorlu dağılımını analiz eder"""
    ranges = []
    current_type = None
    start_index = 0
    
    for i, product in enumerate(products):
        if current_type is None:
            current_type = product['is_organic']
            start_index = i
        elif current_type != product['is_organic']:
            ranges.append((start_index + 1, i + 1, current_type))
            current_type = product['is_organic']
            start_index = i
    
    # Son aralığı ekle
    if start_index < len(products):
        ranges.append((start_index + 1, len(products), current_type))
    
    # Sonuçları yazdır
    for start, end, is_organic in ranges:
        if end == start:
            print(f"{start}. ürün {'' if is_organic else 'sponsorlu'} (is_organic: {str(is_organic).lower()})")
        else:
            print(f"{start}-{end} arası ürünler {'' if is_organic else 'sponsorlu'} (is_organic: {str(is_organic).lower()})")

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