SELECTORS = {
    "product_card": {
        "main": 'div[data-asin]:not([data-asin=""]):not(:empty)',
        "required": True,
        "description": "Ürün kartı seçicisi"
    },
    
    "product_container": {
        "main": 'div.s-main-slot',
        "required": True,
        "description": "Tüm ürünleri içeren konteyner"
    },
    
    "title": {
        "main": 'h2 a.a-link-normal span.a-text-normal',
        "alternatives": [
            'h2 a span.a-text-normal',
            'h2 a.a-text-normal',
            'h2 a span',
            'h2 a'
        ],
        "required": True,
        "description": "Ürün başlığı"
    },
    
    "price": {
        "main": 'span.a-price:not(.a-text-price) span.a-price-whole',
        "alternatives": [
            'span.a-price:not(.a-text-price) span.a-offscreen',
            'span.a-color-base span.a-offscreen',
            'span.a-price span.a-price-whole'
        ],
        "required": True,
        "description": "Ürün fiyatı"
    },
    
    "original_price": {
        "main": 'span.a-price.a-text-price span.a-offscreen',
        "required": False,
        "description": "İndirim öncesi fiyat"
    },
    
    "image": {
        "main": 'img.s-image[src]',
        "required": False,
        "description": "Ürün görseli",
        "attribute": "src"
    },
    
    "badge": {
        "main": 'span[id*="BEST_SELLER"]',
        "alternatives": [
            'span[id*="AMAZON_CHOICE"]',
            'span.a-badge-label',
            'span.a-badge-text'
        ],
        "required": False,
        "description": "Ürün rozeti (Best Seller, Amazon Choice vb.)"
    },
    
    "rating": {
        "main": 'i.a-icon-star-small span.a-icon-alt',
        "alternatives": [
            'i.a-icon-star span.a-icon-alt',
            'span.a-icon-alt:not(:contains("Previous")):not(:contains("Next"))'
        ],
        "required": False,
        "description": "Ürün puanı"
    },
    
    "review_count": {
        "main": 'span.a-size-base.s-underline-text',
        "alternatives": [
            'span[aria-label*="stars"] ~ span.a-size-base',
            'a.a-link-normal span.a-size-base'
        ],
        "required": False,
        "description": "Değerlendirme sayısı"
    },
    
    "prime": {
        "main": 'i.a-icon-prime,span.a-icon-prime',
        "alternatives": [
            'span[aria-label*="Prime"]',
            'i[aria-label*="Prime"]'
        ],
        "required": False,
        "description": "Prime uygunluğu",
        "is_boolean": True
    },
    
    "delivery": {
        "main": 'span[aria-label*="delivery"]',
        "alternatives": [
            'span[aria-label*="FREE delivery"]',
            'span[aria-label*="FREE Delivery"]'
        ],
        "required": False,
        "description": "Teslimat bilgisi"
    },
    
    "stock": {
        "main": 'span.a-color-price[aria-label*="stock"]',
        "alternatives": [
            'span[aria-label*="in stock"]',
            'span[aria-label*="out of stock"]'
        ],
        "required": False,
        "description": "Stok durumu"
    },
    
    "sponsored": {
        "main": 'span.puis-label-text,span.s-label-popover-default',
        "required": True,
        "description": "Sponsorlu ürün",
        "is_boolean": True
    },
    
    "url": {
        "main": 'a[href*="/dp/"]',
        "alternatives": [
            'h2 a[href*="/dp/"]',
            'a.a-link-normal[href*="/dp/"]'
        ],
        "required": True,
        "description": "Ürün URL'i",
        "attribute": "href"
    }
}

def get_selector(selector_name, selector_type="main"):
    """
    Belirtilen seçiciyi döndürür.
    
    Args:
        selector_name (str): Seçici adı
        selector_type (str): Seçici tipi (main veya alternatives)
    
    Returns:
        str or list: Seçici veya seçici listesi
    """
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
        
    selector = SELECTORS[selector_name]
    
    if selector_type == "main":
        return selector["main"]
    elif selector_type == "alternatives":
        return selector.get("alternatives", [])
    elif selector_type == "all":
        all_selectors = [selector["main"]]
        if "alternatives" in selector:
            all_selectors.extend(selector["alternatives"])
        return all_selectors
    else:
        raise ValueError(f"Geçersiz seçici tipi: {selector_type}")

def is_required(selector_name):
    """
    Seçicinin zorunlu olup olmadığını döndürür.
    
    Args:
        selector_name (str): Seçici adı
    
    Returns:
        bool: Seçici zorunlu ise True, değilse False
    """
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
        
    return SELECTORS[selector_name]["required"]

def get_description(selector_name):
    """
    Seçicinin açıklamasını döndürür.
    
    Args:
        selector_name (str): Seçici adı
    
    Returns:
        str: Seçici açıklaması
    """
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
        
    return SELECTORS[selector_name]["description"]

def is_boolean_selector(selector_name):
    """
    Seçicinin boolean değer döndürüp döndürmediğini kontrol eder.
    
    Args:
        selector_name (str): Seçici adı
    
    Returns:
        bool: Seçici boolean değer döndürüyorsa True, değilse False
    """
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
        
    return SELECTORS[selector_name].get("is_boolean", False)

def get_attribute(selector_name):
    """
    Seçicinin hangi özniteliği kullanacağını döndürür.
    
    Args:
        selector_name (str): Seçici adı
    
    Returns:
        str or None: Öznitelik adı veya None
    """
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
        
    return SELECTORS[selector_name].get("attribute", None) 