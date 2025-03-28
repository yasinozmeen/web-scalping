import asyncio
import datetime
from typing import Dict, Optional
from scraper import process_asin_async
from database import Database
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('queue.log')
    ]
)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        logger.info(f"🚦 Rate limiter başlatıldı: {requests_per_minute} istek/dakika")

    async def acquire(self):
        now = datetime.datetime.now()
        self.requests = [req for req in self.requests if (now - req).total_seconds() < 60]
        
        if len(self.requests) >= self.requests_per_minute:
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                logger.warning(f"⚠️ Rate limit aşıldı, {wait_time:.2f} saniye bekleniyor...")
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)
        logger.debug(f"✅ Rate limit kontrolü başarılı: {len(self.requests)}/{self.requests_per_minute}")

class ScraperQueue:
    def __init__(self, num_workers: int = 10):
        self.queue = asyncio.Queue()
        self.workers = []
        self.num_workers = num_workers
        self.rate_limiter = RateLimiter()
        self.db = Database()
        self.is_running = False
        logger.info(f"🔄 Scraper kuyruğu başlatıldı: {num_workers} worker")

    async def add_task(self, asin: str, keyword: str):
        """Kuyruğa yeni görev ekle"""
        await self.queue.put((asin, keyword))
        logger.info(f"📥 Görev kuyruğa eklendi: ASIN={asin}, Keyword={keyword}")
        logger.info(f"📊 Kuyruk durumu: {self.queue.qsize()} görev bekliyor")

    async def worker(self):
        """Worker işlemi"""
        while self.is_running:
            try:
                asin, keyword = await self.queue.get()
                logger.info(f"🔄 Worker başladı: ASIN={asin}, Keyword={keyword}")
                
                try:
                    # Rate limiter'ı uygula
                    logger.debug(f"🚦 Rate limit kontrolü yapılıyor: ASIN={asin}")
                    await self.rate_limiter.acquire()
                    
                    # ASIN'i işle
                    logger.info(f"🔍 ASIN işleniyor: ASIN={asin}")
                    result = await process_asin_async(asin, keyword)
                    logger.info(f"✅ Sonuç alındı: {result}")
                    
                    # Veritabanına kaydet
                    logger.info(f"💾 Sonuç kaydediliyor: ASIN={asin}")
                    await self.db.save_result(result)
                    logger.info(f"✅ Sonuç kaydedildi: ASIN={asin}")
                    
                except Exception as e:
                    logger.error(f"❌ İşlem hatası: ASIN={asin}, Hata={str(e)}", exc_info=True)
                    # Hata durumunda boş sonuç kaydet
                    logger.warning(f"⚠️ Boş sonuç kaydediliyor: ASIN={asin}")
                    await self.db.save_result({
                        'asin': asin,
                        'keyword': keyword,
                        'found': False,
                        'found_variant': None,
                        'page': None,
                        'page_position': None,
                        'total_position': None,
                        'sponsored': False
                    })
                
                finally:
                    self.queue.task_done()
                    logger.info(f"✅ Worker tamamlandı: ASIN={asin}")
                    logger.info(f"📊 Kuyruk durumu: {self.queue.qsize()} görev bekliyor")
                    
            except asyncio.CancelledError:
                logger.warning("⚠️ Worker iptal edildi")
                break
            except Exception as e:
                logger.error(f"❌ Worker hatası: {str(e)}", exc_info=True)
                continue

    async def start_workers(self):
        """Worker'ları başlat"""
        self.is_running = True
        for i in range(self.num_workers):
            worker = asyncio.create_task(self.worker())
            self.workers.append(worker)
            logger.info(f"🚀 Worker {i+1} başlatıldı")
        logger.info(f"✅ Tüm worker'lar başlatıldı: {self.num_workers} worker aktif")

    async def stop_workers(self):
        """Worker'ları durdur"""
        logger.info("🛑 Worker'lar durduruluyor...")
        self.is_running = False
        for i, worker in enumerate(self.workers):
            worker.cancel()
            logger.info(f"🛑 Worker {i+1} durduruldu")
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("✅ Tüm worker'lar durduruldu") 