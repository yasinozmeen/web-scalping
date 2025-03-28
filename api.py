import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from database import Database
from scraper_queue import ScraperQueue
import logging
import sys
from contextlib import asynccontextmanager

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger(__name__)

# Global değişkenler
db = None
queue = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, queue
    logger.info("🚀 API başlatılıyor...")
    db = Database()
    queue = ScraperQueue()
    await queue.start_workers()
    logger.info("✅ API başlatıldı")
    yield
    # Shutdown
    logger.info("🛑 API kapatılıyor...")
    await queue.stop_workers()
    logger.info("✅ API kapatıldı")

app = FastAPI(title="Amazon Scraper API", lifespan=lifespan)

class ScrapeRequest(BaseModel):
    asin: str
    keyword: str

@app.post("/scrape")
async def scrape_product(request: ScrapeRequest):
    """Ürün scraping isteği al"""
    try:
        logger.info(f"📥 Yeni istek: ASIN={request.asin}, Keyword={request.keyword}")
        
        # Mevcut sonucu kontrol et
        result = await db.get_result(request.asin)
        if result:
            logger.info(f"✅ Mevcut sonuç bulundu: {result}")
            return {"message": "Sonuç zaten mevcut", "status": "completed", "result": result}
        
        # Yeni scraping görevi ekle
        await queue.add_task(request.asin, request.keyword)
        logger.info(f"✅ Yeni görev eklendi: ASIN={request.asin}")
        return {"message": "İşlem kuyruğa eklendi", "status": "pending", "asin": request.asin}
        
    except Exception as e:
        logger.error(f"❌ Scraping hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"500: İşlem hatası - {str(e)}")

@app.get("/result/{asin}")
async def get_result(asin: str):
    """ASIN için sonucu getir"""
    try:
        logger.info(f"🔍 Sonuç aranıyor: ASIN={asin}")
        result = await db.get_result(asin)
        if not result:
            logger.warning(f"❌ Sonuç bulunamadı: ASIN={asin}")
            raise HTTPException(status_code=404, detail="404: Sonuç bulunamadı")
            
        logger.info(f"✅ Sonuç bulundu: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sonuç getirme hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"500: İşlem hatası - {str(e)}")

@app.get("/stats")
async def get_stats():
    """İstatistikleri getir"""
    try:
        logger.info("📊 İstatistikler istendi")
        stats = await db.get_stats()
        logger.info(f"✅ İstatistikler alındı: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ İstatistik hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"500: İşlem hatası - {str(e)}")

if __name__ == "__main__":
    try:
        logger.info("🚀 API başlatılıyor...")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        logger.info("👋 API kapatılıyor...")
    except Exception as e:
        logger.error(f"❌ API hatası: {str(e)}", exc_info=True)
        sys.exit(1) 