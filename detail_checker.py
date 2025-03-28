import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def check_asin_details(asin):
    print(f"\n🔍 ASIN {asin} için detay sayfası kontrol ediliyor...")
    
    # Chrome ayarları
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Arka planda çalıştır
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Tarayıcıyı başlat
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Amazon ürün sayfasına git
        url = f"https://www.amazon.com/dp/{asin}"
        print(f"📌 URL: {url}")
        driver.get(url)
        time.sleep(3)  # Sayfa yüklemesi için bekle
        
        # Sayfanın HTML'ini al
        html = driver.page_source
        
        print("\n🔎 Varyasyon Bilgileri Aranıyor...")
        
        # Varyasyon seçeneklerini kontrol et
        variation_elements = driver.find_elements(By.CSS_SELECTOR, '#variation_color_name, #variation_size_name')
        
        if variation_elements:
            print("\n✅ Varyasyon seçenekleri bulundu!")
            
            for element in variation_elements:
                variation_type = element.get_attribute('id').replace('variation_', '').replace('_name', '')
                print(f"\n📦 {variation_type.capitalize()} Varyasyonları:")
                
                # Varyasyon seçeneklerini bul
                options = element.find_elements(By.CSS_SELECTOR, 'li')
                
                for option in options:
                    try:
                        asin_data = option.get_attribute('data-defaultasin')
                        title = option.get_attribute('title')
                        print(f"   - ASIN: {asin_data or 'N/A'}")
                        print(f"     Başlık: {title or 'N/A'}")
                    except:
                        continue
            
            # Parent ASIN'i bulmaya çalış
            try:
                parent_element = driver.find_element(By.CSS_SELECTOR, '[data-parent-asin]')
                parent_asin = parent_element.get_attribute('data-parent-asin')
                if parent_asin:
                    print(f"\n👑 Parent ASIN: {parent_asin}")
            except:
                print("\n❌ Parent ASIN bulunamadı")
                
        else:
            print("\n❌ Varyasyon seçenekleri bulunamadı!")
            print("Bu ürün tek bir varyasyona sahip olabilir veya hiç varyasyonu olmayabilir.")
        
    except Exception as e:
        print(f"\n❌ Hata: {str(e)}")
    
    finally:
        print("\n🔄 Tarayıcı kapatılıyor...")
        driver.quit()

if __name__ == "__main__":
    test_asin = "B0CRMZHDG8"  # Stanley Quencher örneği
    check_asin_details(test_asin) 