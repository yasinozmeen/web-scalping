import os
import json
import re
from bs4 import BeautifulSoup
from amazon_selectors import (
    SELECTORS, get_selector, is_required, 
    is_boolean_selector, get_attribute
)

class TestResult:
    def __init__(self):
        self.found = 0
        self.successful = 0
        self.failed = 0
        self.examples = []
        self.errors = []

def validate_price(text):
    """Fiyat formatını doğrular"""
    price_pattern = r'^\d+(?:,\d{3})*(?:\.\d{2})?$'
    text = text.strip().replace('$', '')
    return bool(re.match(price_pattern, text))

def validate_url(text):
    """URL formatını doğrular"""
    url_pattern = r'^/[^/].*$|^https?://.*$'
    return bool(re.match(url_pattern, text))

def validate_rating(text):
    """Puanlama formatını doğrular"""
    rating_pattern = r'^[\d.]+ out of \d+ stars$'
    return bool(re.match(rating_pattern, text))

def validate_boolean(element):
    """Boolean seçiciler için doğrulama"""
    return element is not None

def test_selector(soup, selector_name, test_results):
    """Belirtilen seçiciyi test eder"""
    selectors = get_selector(selector_name, "all")
    elements = []
    
    for selector in selectors:
        elements.extend(soup.select(selector))
    
    test_results.found = len(elements)
    
    if is_required(selector_name) and not elements:
        test_results.errors.append(f"Zorunlu seçici '{selector_name}' hiç eleman bulamadı!")
        return
    
    attribute = get_attribute(selector_name)
    
    for element in elements:
        if attribute:
            value = element.get(attribute, "")
            if value:
                test_results.successful += 1
                test_results.examples.append(value)
            else:
                test_results.failed += 1
                test_results.errors.append(f"'{attribute}' özniteliği bulunamadı")
            continue
        
        if selector_name == "price":
            text = element.get_text().strip()
            if validate_price(text):
                test_results.successful += 1
                test_results.examples.append(text)
            else:
                test_results.failed += 1
                test_results.errors.append(f"Geçersiz fiyat formatı: {text}")
        
        elif selector_name == "url":
            href = element.get("href", "")
            if validate_url(href):
                test_results.successful += 1
                test_results.examples.append(href)
            else:
                test_results.failed += 1
                test_results.errors.append(f"Geçersiz URL formatı: {href}")
        
        elif selector_name == "rating":
            text = element.get_text().strip()
            if validate_rating(text):
                test_results.successful += 1
                test_results.examples.append(text)
            else:
                test_results.failed += 1
                test_results.errors.append(f"Geçersiz puanlama formatı: {text}")
        
        elif is_boolean_selector(selector_name):
            if validate_boolean(element):
                test_results.successful += 1
            else:
                test_results.failed += 1
                test_results.errors.append("Geçersiz boolean değer")
        
        else:
            text = element.get_text().strip()
            if text:
                test_results.successful += 1
                test_results.examples.append(text)
            else:
                test_results.failed += 1
                test_results.errors.append("Boş metin")

def run_all_tests():
    """Tüm seçicileri test eder"""
    data_dir = "data"
    html_files = [f for f in os.listdir(data_dir) if f.endswith(".html")]
    
    if not html_files:
        print("Test için HTML dosyası bulunamadı!")
        return
    
    latest_html = max(html_files, key=lambda x: os.path.getmtime(os.path.join(data_dir, x)))
    html_path = os.path.join(data_dir, latest_html)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, "html.parser")
    results = {}
    
    for selector_name in SELECTORS:
        test_results = TestResult()
        test_selector(soup, selector_name, test_results)
        results[selector_name] = {
            "found": test_results.found,
            "successful": test_results.successful,
            "failed": test_results.failed,
            "examples": test_results.examples[:3],
            "errors": test_results.errors
        }
    
    # Sonuçları JSON dosyasına kaydet
    results_path = os.path.join(data_dir, "selector_test_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Sonuçları ekrana yazdır
    print("\nSeçici Test Sonuçları:")
    print("-" * 50)
    
    for selector_name, result in results.items():
        status = "✅" if not result["errors"] else "❌"
        print(f"{status} {selector_name}:")
        print(f"   Bulunan: {result['found']}")
        print(f"   Başarılı: {result['successful']}")
        print(f"   Başarısız: {result['failed']}")
        
        if result["errors"]:
            print(f"   Hatalar: {', '.join(result['errors'])}")
        
        print()

if __name__ == "__main__":
    run_all_tests() 