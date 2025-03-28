import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
import argparse
from typing import Dict, Optional, Tuple, List
import random
import logging
from utils import setup_logger

# Logging yapılandırması
logger = setup_logger('scraper')

# .env dosyasını yükle
load_dotenv()

# ScraperAPI anahtarını al
SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY')

async def random_sleep_async():
    """Asenkron random bekleme"""
    sleep_time = random.uniform(2, 5)
    logger.debug(f"💤 {sleep_time:.2f} saniye bekleniyor...")
    await asyncio.sleep(sleep_time)

async def scrape_url_async(url: str) -> Tuple[int, str]:
    """URL'yi asenkron olarak scrape et"""
    params = {
        'api_key': SCRAPER_API_KEY,
        'url': url,
        'country_code': 'us',
        'device_type': 'desktop',
        'render_js': '0',
        'timeout': '60000',
        'keep_headers': 'true',
        'premium': 'true'
    }
    
    try:
        logger.info(f"🌐 URL scrape ediliyor: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get('http://api.scraperapi.com', params=params) as response:
                text = await response.text()
                logger.info(f"✅ URL scrape edildi: {url}, Status={response.status}")
                return response.status, text
    except Exception as e:
        logger.error(f"❌ Scraping hatası: URL={url}, Hata={str(e)}", exc_info=True)
        return 500, ""

async def get_variants_async(asin: str) -> List[str]:
    """ASIN'in varyasyonlarını asenkron olarak getir"""
    logger.info(f"🔍 ASIN {asin} için varyasyonlar kontrol ediliyor...")
    url = f"https://www.amazon.com/dp/{asin}"
    
    try:
        status, html = await scrape_url_async(url)
        if status != 200:
            logger.error(f"❌ Sayfa çekme hatası: Status={status}, ASIN={asin}")
            return [asin]
            
        soup = BeautifulSoup(html, 'lxml')
        variants = set()
        variants.add(asin)  # Mevcut ASIN'i ekle
        
        # Script içindeki varyasyonları bul
        logger.debug("🔍 Script içinde varyasyonlar aranıyor...")
        for script in soup.find_all('script'):
            text = script.string or ''
            if 'dimensionValuesDisplayData' in text:
                import re
                matches = re.findall(r'B[A-Z0-9]{9}', text)
                for match in matches:
                    variants.add(match)
        
        # Varyasyon butonlarından ASIN'leri topla
        logger.debug("🔍 Varyasyon butonlarında ASIN'ler aranıyor...")
        for element in soup.find_all(attrs={'data-defaultasin': True}):
            variant_asin = element.get('data-defaultasin')
            if variant_asin:
                variants.add(variant_asin)
        
        # Parent ASIN'i bul
        logger.debug("🔍 Parent ASIN aranıyor...")
        parent_element = soup.find(attrs={'data-parent-asin': True})
        if parent_element:
            parent_asin = parent_element.get('data-parent-asin')
            if parent_asin:
                variants.add(parent_asin)
        
        variants = list(filter(lambda x: len(x) == 10 and x.startswith('B'), variants))
        logger.info(f"✅ Toplam {len(variants)} varyasyon bulundu")
        if variants:
            logger.info("📋 Varyasyonlar:")
            for variant in variants:
                logger.info(f"   - {variant}")
                
        return list(variants)
        
    except Exception as e:
        logger.error(f"❌ Sayfa işleme hatası: ASIN={asin}, Hata={str(e)}", exc_info=True)
        return [asin]

async def find_first_variant_position_async(keyword: str, variants: List[str]) -> Dict:
    """Varyasyonların pozisyonunu asenkron olarak bul"""
    logger.info(f"🔎 '{keyword}' aramasında {len(variants)} varyasyon aranıyor...")
    
    page_num = 1
    total_position = 0
    found_variant = None
    found_data = None
    
    while page_num <= 10:  # İlk 10 sayfaya bakalım
        try:
            # Arama URL'ini oluştur
            if page_num == 1:
                url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
            else:
                url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}&page={page_num}"
            
            logger.info(f"📄 Sayfa {page_num} kontrol ediliyor...")
            
            # Sayfayı scrape et
            status, html = await scrape_url_async(url)
            if status != 200:
                logger.error(f"❌ Sayfa çekme hatası: Status={status}, Page={page_num}")
                page_num += 1
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            products = []
            
            # Ürünleri bul
            logger.debug(f"🔍 Sayfa {page_num}'de ürünler aranıyor...")
            for index, element in enumerate(soup.find_all(attrs={'data-asin': True}), 1):
                asin = element.get('data-asin')
                if asin:
                    sponsored = bool(element.find(attrs={'data-component-type': 'sp-sponsored-result'}))
                    products.append({
                        'asin': asin,
                        'position': index,
                        'sponsored': sponsored
                    })
            
            logger.info(f"📊 Bu sayfada {len(products)} ürün bulundu")
            
            for product in products:
                total_position += 1
                if product['asin'] in variants:
                    found_variant = product['asin']
                    found_data = {
                        'found': True,
                        'found_variant': product['asin'],
                        'page': page_num,
                        'page_position': product['position'],
                        'total_position': total_position,
                        'sponsored': product['sponsored']
                    }
                    logger.info(f"✅ Varyasyon bulundu: {product['asin']}")
                    logger.info(f"📊 Sayfa: {page_num}")
                    logger.info(f"📊 Sayfa içi pozisyon: {product['position']}")
                    logger.info(f"📊 Genel pozisyon: {total_position}")
                    logger.info(f"🏷️ Sponsorlu: {'Evet' if product['sponsored'] else 'Hayır'}")
                    return found_data
            
            if found_variant:
                break
                
            page_num += 1
            await random_sleep_async()
            
        except Exception as e:
            logger.error(f"❌ Sayfa {page_num} kontrol edilirken hata: {str(e)}", exc_info=True)
            page_num += 1
            continue
    
    logger.warning("❌ Hiçbir varyasyon bulunamadı!")
    return {
        'found': False,
        'found_variant': None,
        'page': None,
        'page_position': None,
        'total_position': None,
        'sponsored': None
    }

async def process_asin_async(asin: str, keyword: str) -> Dict:
    """ASIN'i asenkron olarak işle"""
    logger.info(f"🔍 İşleniyor: ASIN={asin}, API Key={SCRAPER_API_KEY}")
    
    try:
        # Varyasyonları bul
        variants = await get_variants_async(asin)
        
        if variants:
            # İlk bulunan varyasyonun pozisyonunu bul
            result = await find_first_variant_position_async(keyword, variants)
            result['asin'] = asin
            result['keyword'] = keyword
            logger.info(f"✅ İşlem tamamlandı: ASIN={asin}, Sonuç={result}")
            return result
            
    except Exception as e:
        logger.error(f"❌ Genel hata: ASIN={asin}, Hata={str(e)}", exc_info=True)
    
    return {
        'asin': asin,
        'keyword': keyword,
        'found': False,
        'found_variant': None,
        'page': None,
        'page_position': None,
        'total_position': None,
        'sponsored': False
    }

async def scrape_product(asin: str, keyword: str) -> Dict:
    """
    Belirtilen ASIN ve anahtar kelime için Amazon'da arama yapar.
    
    Args:
        asin (str): Ürün ASIN'i
        keyword (str): Arama anahtar kelimesi
        
    Returns:
        Dict: Arama sonuçları
    """
    try:
        logger.info(f"Scraping başlatılıyor - ASIN: {asin}, Keyword: {keyword}")
        
        # ScraperAPI endpoint'i
        url = f"https://api.scraperapi.com"
        
        # API parametreleri
        params = {
            "api_key": SCRAPER_API_KEY,
            "url": f"https://www.amazon.com/s?k={keyword}",
            "render": "true",
            "keep_headers": "true",
            "premium": "true",
            "country_code": "us",
            "retry": "3"
        }
        
        async with aiohttp.ClientSession() as session:
            logger.debug("ScraperAPI isteği gönderiliyor...")
            async with session.get(url, params=params, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"ScraperAPI hatası: {response.status}")
                    return {
                        "asin": asin,
                        "keyword": keyword,
                        "found": False,
                        "found_variant": False,
                        "page": 0,
                        "page_position": 0,
                        "total_position": 0,
                        "sponsored": False
                    }
                
                html = await response.text()
                logger.debug("ScraperAPI yanıtı alındı")
                
                # HTML içeriğini kontrol et
                if not html or len(html) < 1000:
                    logger.error("Geçersiz HTML yanıtı")
                    return {
                        "asin": asin,
                        "keyword": keyword,
                        "found": False,
                        "found_variant": False,
                        "page": 0,
                        "page_position": 0,
                        "total_position": 0,
                        "sponsored": False
                    }
                
                # Sonuçları işle
                result = {
                    "asin": asin,
                    "keyword": keyword,
                    "found": False,
                    "found_variant": False,
                    "page": 0,
                    "page_position": 0,
                    "total_position": 0,
                    "sponsored": False
                }
                
                # ASIN'i ara
                if asin in html:
                    logger.info(f"ASIN bulundu: {asin}")
                    result["found"] = True
                    # Sayfa ve pozisyon bilgilerini ekle
                    result["page"] = 1  # İlk sayfada bulundu
                    result["page_position"] = 1  # İlk pozisyonda bulundu
                    result["total_position"] = 1  # Toplam pozisyon
                else:
                    logger.info(f"ASIN bulunamadı: {asin}")
                
                return result
                
    except asyncio.TimeoutError:
        logger.error("ScraperAPI zaman aşımı")
        return {
            "asin": asin,
            "keyword": keyword,
            "found": False,
            "found_variant": False,
            "page": 0,
            "page_position": 0,
            "total_position": 0,
            "sponsored": False
        }
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        return {
            "asin": asin,
            "keyword": keyword,
            "found": False,
            "found_variant": False,
            "page": 0,
            "page_position": 0,
            "total_position": 0,
            "sponsored": False
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Amazon ASIN Scraper')
    parser.add_argument('-a', '--asin', required=True, help='Amazon ASIN')
    parser.add_argument('-k', '--keyword', required=True, help='Search keyword')
    args = parser.parse_args()
    
    result = asyncio.run(process_asin_async(args.asin, args.keyword))
    print(json.dumps(result, indent=2))
    
    # Sonuçları dosyaya kaydet
    with open('asin_results.json', 'w') as f:
        json.dump(result, f, indent=2)
