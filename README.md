# Amazon Ürün Veri Toplama Aracı

Bu Python scripti, Amazon'dan ürün verilerini otomatik olarak toplar ve JSON formatında kaydeder.

## Özellikler

- Amazon ürün sayfalarından veri toplama
- Ürün başlığı, fiyat, puan ve stok durumu bilgilerini çekme
- Proxy desteği
- Otomatik veri kaydetme (JSON formatında)
- Hata yönetimi ve yeniden deneme mekanizması

## Gereksinimler

- Python 3.7+
- Playwright
- python-dotenv

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Playwright'ı başlatın:
```bash
playwright install
```

3. `.env` dosyası oluşturun ve proxy bilgilerinizi ekleyin:
```
PROXY_SERVER=proxy_address:port
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

## Kullanım

Scripti çalıştırmak için:

```bash
python amazon_scraper.py
```

## Çıktı

Toplanan veriler `product_data.json` dosyasına kaydedilir. Örnek çıktı formatı:

```json
{
    "title": "Ürün Adı",
    "price": "100.00 TL",
    "rating": "4.5",
    "availability": "Stokta",
    "url": "https://www.amazon.com/...",
    "timestamp": "2024-02-20 12:00:00"
}
```

## Güvenlik

- Proxy bilgilerinizi güvenli bir şekilde `.env` dosyasında saklayın
- `.env` dosyasını asla GitHub'a yüklemeyin
- Amazon'un kullanım koşullarına uygun olarak kullanın

## Lisans

MIT License 