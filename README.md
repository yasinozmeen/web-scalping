# Amazon Ürün Veri Çekme Aracı

Bu proje, Amazon'dan belirli bir arama sonucuna göre ürün verilerini çeken basit bir web scraping aracıdır.

## Özellikler

- Amazon'da arama yapma
- Arama sonuçlarından temel ürün verilerini çekme:
  - ASIN (Amazon Ürün Kimliği)
  - Index (Ürün Sıra Numarası)
  - Is Organic (Organik/Sponsorlu Sonuç Bilgisi)
- HTML içeriğini kaydetme
- Verileri JSON formatında saklama

## Gereksinimler

```
playwright==1.42.0
python-dotenv==1.0.1
lxml==5.1.0
```

## Kurulum

1. Projeyi klonlayın
2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```
3. Playwright tarayıcılarını yükleyin:
```bash
playwright install
```
4. `.env` dosyası oluşturun ve Bright Data bilgilerinizi ekleyin:
```
BRIGHT_DATA_AUTH=your_auth
BRIGHT_DATA_HOST=your_host
BRIGHT_DATA_PORT=your_port
```

## Kullanım

Programı çalıştırmak için aşağıdaki komutları kullanabilirsiniz:

```bash
# Varsayılan arama (red car) için:
python scraper.py

# Özel bir arama terimi için:
python scraper.py --search "iphone"
# veya
python scraper.py -s "iphone"
```

Program şu adımları gerçekleştirir:
1. Amazon.com'a bağlanır
2. Belirtilen ürünü arar (varsayılan: "red car")
3. Arama sonuçlarının HTML'ini kaydeder
4. Ürün verilerini çeker
5. Verileri JSON formatında kaydeder

## Çıktı Formatı

```json
{
  "asin": "B0CRMZHDG8",
  "index": "3",
  "is_organic": false
}
```

## Dosya Yapısı

- `scraper.py`: Ana program dosyası
- `parser.py`: HTML analiz işlemleri
- `amazon_selectors.py`: XPath seçicileri
- `requirements.txt`: Bağımlılıklar
- `data/`: HTML ve JSON çıktıları

## Not

Bu araç sadece eğitim amaçlıdır. Kullanmadan önce Amazon'un kullanım koşullarını kontrol edin. 