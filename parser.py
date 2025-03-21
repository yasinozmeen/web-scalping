from bs4 import BeautifulSoup
import json
import os

def extract_product_data(html_file_path):
    # HTML dosyasını oku
    with open(html_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # BeautifulSoup objesi oluştur
    soup = BeautifulSoup(content, 'html.parser')
    
    # Tüm ürün kartlarını bul
    product_cards = soup.select('div[data-asin]:not([data-asin=""])')
    products = []
    
    for card in product_cards:
        product = {}
        
        # ASIN
        product['asin'] = card.get('data-asin', '')
        
        # Index
        product['index'] = card.get('data-index', '')
        
        # Title
        title_element = card.select_one('h2 span')
        product['title'] = title_element.text.strip() if title_element else ''
        
        # Sale Price
        sale_price_element = card.select_one('span.a-price span.a-offscreen')
        product['sale_price'] = sale_price_element.text.strip() if sale_price_element else ''
        
        # List Price
        list_price_element = card.select_one('span.a-price.a-text-price span.a-offscreen')
        product['list_price'] = list_price_element.text.strip() if list_price_element else ''
        
        # Badge ve Kategori
        badge_element = card.select_one('span[id*="BEST_SELLER"], span[id*="AMAZON_CHOICE"]')
        if badge_element:
            product['badge'] = badge_element.get('id', '').split('_')[0]
            product['badge_category'] = badge_element.text.strip()
        else:
            product['badge'] = ''
            product['badge_category'] = ''
        
        # Is Organic
        product['is_organic'] = 'true' if card.get('data-dib-organic') else 'false'
        
        # Image URL
        img_element = card.select_one('img[src]')
        product['image_url'] = img_element.get('src', '') if img_element else ''
        
        # Yorum Ortalaması
        rating_element = card.select_one('i span')
        if rating_element:
            rating_text = rating_element.text.strip()
            product['rating'] = rating_text.split(' ')[0] if rating_text else ''
        else:
            product['rating'] = ''
        
        # Yorum Sayısı
        review_count_element = card.select_one('span[aria-label*="out of"] ~ div span')
        product['review_count'] = review_count_element.text.strip() if review_count_element else ''
        
        products.append(product)
    
    return products

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