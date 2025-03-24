SELECTORS = {
    "product_card": {
        "main": '//div[contains(@class, "s-result-item") and contains(@class, "s-asin")]',
        "required": True,
        "description": "Ürün kartı seçicisi",
        "xpath": True,
        "attributes": {
            "asin": "data-asin",
            "index": "data-index"
        }
    },
    
    "is_organic": {
        "main": './/div[contains(@class, "s-result-item") and not(contains(@data-component-type, "sp-sponsored"))]',
        "required": False,
        "description": "Organik sonuç mu",
        "xpath": True,
        "attribute": "data-component-type"
    }
}

def get_selector(selector_name):
    """Seçiciyi döndürür"""
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
    return SELECTORS[selector_name]["main"]

def get_attributes(selector_name):
    """Seçicinin özniteliklerini döndürür"""
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
    return SELECTORS[selector_name].get("attributes", None)

def get_attribute(selector_name):
    """Seçicinin özniteliğini döndürür"""
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
    return SELECTORS[selector_name].get("attribute", None)

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

def is_xpath_selector(selector_name):
    """
    Seçicinin XPath olup olmadığını kontrol eder.
    
    Args:
        selector_name (str): Seçici adı
    
    Returns:
        bool: Seçici XPath ise True, değilse False
    """
    if selector_name not in SELECTORS:
        raise ValueError(f"Seçici bulunamadı: {selector_name}")
        
    return SELECTORS[selector_name].get("xpath", False) 