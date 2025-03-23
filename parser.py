from bs4 import BeautifulSoup
import json
import os
from amazon_selectors import get_selector, is_required, SELECTORS
import re

def extract_product_data(html_file_path):
    # HTML dosyasını oku
    with open(html_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # BeautifulSoup objesi oluştur
    soup = BeautifulSoup(content, 'html.parser')
    
    # Ürün konteynerini bul
    product_container = soup.select_one(get_selector('product_container'))
    if not product_container:
        print("Ürün konteyneri bulunamadı!")
        return []
    
    # Tüm ürün kartlarını bul
    product_cards = product_container.select(get_selector('product_card'))
    products = []
    
    for card in product_cards:
        try:
            product = {}
            
            # ASIN
            asin = card.get('data-asin', '')
            if not asin:
                continue
            product['asin'] = asin
            
            # Index
            product['index'] = card.get('data-index', '')
            
            # Her bir seçici için veri çekme işlemi
            for selector_name in SELECTORS:
                if selector_name in ['product_card', 'product_container']:
                    continue
                
                value = extract_field_value(card, selector_name)
                
                # Eğer zorunlu alan boşsa, hata fırlat
                if is_required(selector_name) and not value:
                    raise ValueError(f"Zorunlu alan boş: {selector_name}")
                
                # Özel durumlar için field mapping
                field_name = selector_name
                if selector_name == 'price':
                    field_name = 'current_price'
                
                product[field_name] = value
            
            # İndirim yüzdesi hesaplama
            if product.get('current_price', 'N/A') != 'N/A' and product.get('original_price', 'N/A') != 'N/A':
                try:
                    current = float(product['current_price'].replace('$', '').replace(',', ''))
                    original = float(product['original_price'].replace('$', '').replace(',', ''))
                    if original > current:
                        discount = ((original - current) / original) * 100
                        product['discount_percentage'] = f"{discount:.0f}%"
                    else:
                        product['discount_percentage'] = 'N/A'
                except:
                    product['discount_percentage'] = 'N/A'
            else:
                product['discount_percentage'] = 'N/A'
            
            products.append(product)
            
        except Exception as e:
            print(f"Ürün bilgileri analiz edilemedi: {str(e)}")
            continue
    
    return products

def extract_field_value(card, selector_name):
    """
    Belirtilen seçici için değeri çeker.
    
    Args:
        card: BeautifulSoup card elementi
        selector_name: Seçici adı
    
    Returns:
        str: Çekilen değer
    """
    # Ana seçiciyi dene
    element = card.select_one(get_selector(selector_name))
    
    # Ana seçici başarısız olursa alternatifleri dene
    if not element and selector_name in SELECTORS:
        for alt_selector in get_selector(selector_name, "alternatives"):
            element = card.select_one(alt_selector)
            if element:
                break
    
    # Özel durumlar
    if selector_name == 'price' and element:
        # Fiyat için özel işlem
        price_whole = card.select_one(SELECTORS['price']['main'])
        if price_whole:
            try:
                whole = price_whole.text.strip().replace(",", "").replace(".", "")
                fraction = card.select_one(SELECTORS['price']['fraction'])
                fraction = fraction.text.strip() if fraction else "00"
                return f"${whole}.{fraction}"
            except:
                pass
        # Alternatif fiyat formatı
        price_text = element.text.strip()
        price_text = re.sub(r'[^\d.]', '', price_text)
        try:
            return f"${float(price_text):.2f}"
        except:
            return "N/A"
    
    # Boolean değerler için özel işlem
    if selector_name in ['prime', 'sponsored']:
        return 'Yes' if element else 'No'
    
    # Stok durumu için özel işlem
    if selector_name == 'stock':
        if not element:
            return 'In Stock'
        return element.text.strip()
    
    # Genel durum
    if element:
        # URL özel durumu
        if selector_name == 'url':
            url = element.get('href', '')
            if url:
                if not url.startswith('http'):
                    url = 'https://www.amazon.com' + url
                if '/dp/' in url:
                    asin = card.get('data-asin', '')
                    url = f"https://www.amazon.com/dp/{asin}"
                return url
            return ''
        
        return element.text.strip()
    
    return 'N/A' if is_required(selector_name) else ''

def main():
    # data klasöründeki HTML dosyasını bul
    data_dir = 'data'
    html_files = [f for f in os.listdir(data_dir) if f.endswith('.html')]
    
    if not html_files:
        print("HTML dosyası bulunamadı!")
        return
    
    # En son oluşturulan HTML dosyasını kullan
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