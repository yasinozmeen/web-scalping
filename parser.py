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
    
    for card in product_cards:
        try:
            product = {}
            
            # ASIN ve Index
            attributes = get_attributes('product_card')
            if attributes:
                for key, attr in attributes.items():
                    product[key] = card.get(attr, '')
            
            # Organik sonuç mu?
            organic_elements = card.xpath(get_selector('is_organic'))
            if organic_elements:
                product['is_organic'] = organic_elements[0].get(get_attribute('is_organic'), 'false') == 'true'
            else:
                product['is_organic'] = False
            
            # ASIN zorunlu alan
            if not product.get('asin'):
                continue
            
            products.append(product)
            
        except Exception as e:
            print(f"Ürün bilgileri analiz edilemedi: {str(e)}")
            continue
    
    return products

def main():
    """Ana fonksiyon"""
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
    
    print(f"Toplam {len(products)} ürün verisi çekildi ve {output_file} dosyasına kaydedildi.")

if __name__ == "__main__":
    main() 