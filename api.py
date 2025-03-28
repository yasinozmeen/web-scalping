import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from database import Database
from scraper_queue import ScraperQueue
from utils import setup_logger

# Logging yapılandırması
logger = setup_logger('api')

app = FastAPI(title="Amazon Scraper API")

# Veritabanı ve kuyruk örnekleri
db = Database()
queue = ScraperQueue()

class ScrapeRequest(BaseModel):
    asin: str
    keyword: str

@app.on_event("startup")
async def startup_event():
    """API başlatıldığında worker'ları başlat"""
    try:
        logger.info("API başlatılıyor...")
        await queue.start_workers()
        logger.info("API başlatıldı")
    except Exception as e:
        logger.error(f"API başlatılırken hata: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """API kapatıldığında worker'ları durdur"""
    try:
        logger.info("API kapatılıyor...")
        await queue.stop_workers()
        logger.info("API kapatıldı")
    except Exception as e:
        logger.error(f"API kapatılırken hata: {str(e)}")
        raise

@app.post("/scrape")
async def scrape_product(request: ScrapeRequest):
    """Yeni bir scraping görevi ekle"""
    try:
        # ASIN kontrolü
        if not request.asin or len(request.asin) < 10:
            raise HTTPException(status_code=400, detail="Geçersiz ASIN")
        
        # Keyword kontrolü
        if not request.keyword or len(request.keyword) < 2:
            raise HTTPException(status_code=400, detail="Geçersiz anahtar kelime")
        
        # Veritabanında sonuç var mı kontrol et
        existing_result = await db.get_result(request.asin)
        if existing_result:
            logger.info(f"Sonuç zaten mevcut - ASIN: {request.asin}")
            return {"status": "completed", "result": existing_result}
        
        # Kuyruğa ekle
        await queue.add_task(request.asin, request.keyword)
        logger.info(f"Görev kuyruğa eklendi - ASIN: {request.asin}")
        
        return {
            "status": "pending",
            "message": "Görev kuyruğa eklendi",
            "asin": request.asin
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scraping görevi eklenirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail="Sunucu hatası")

@app.get("/result/{asin}")
async def get_result(asin: str):
    """ASIN için sonuçları getir"""
    try:
        result = await db.get_result(asin)
        if not result:
            logger.warning(f"Sonuç bulunamadı - ASIN: {asin}")
            raise HTTPException(status_code=404, detail="Sonuç bulunamadı")
        
        logger.info(f"Sonuç getirildi - ASIN: {asin}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sonuç getirilirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail="Sunucu hatası")

@app.get("/stats")
async def get_stats():
    """İstatistikleri getir"""
    try:
        stats = await db.get_stats()
        logger.info("İstatistikler getirildi")
        return stats
        
    except Exception as e:
        logger.error(f"İstatistikler getirilirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail="Sunucu hatası")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 