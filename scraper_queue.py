import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils import setup_logger
from scraper import scrape_product
from database import Database

# Logging yapılandırması
logger = setup_logger('queue')

class RateLimiter:
    def __init__(self, requests_per_minute: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests: List[datetime] = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = datetime.now()
            # Son bir dakikadaki istekleri filtrele
            self.requests = [req for req in self.requests if now - req < timedelta(minutes=1)]
            
            if len(self.requests) >= self.requests_per_minute:
                # En eski isteğin üzerinden geçen süreyi hesapla
                wait_time = 60 - (now - self.requests[0]).total_seconds()
                if wait_time > 0:
                    logger.debug(f"Rate limit aşıldı. {wait_time:.2f} saniye bekleniyor...")
                    await asyncio.sleep(wait_time)
            
            self.requests.append(now)

class ScraperQueue:
    def __init__(self, num_workers: int = 10):
        self.queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.rate_limiter = RateLimiter()
        self.db = Database()
        self.num_workers = num_workers
        self.is_running = False

    async def add_task(self, asin: str, keyword: str):
        """Kuyruğa yeni görev ekle"""
        try:
            await self.queue.put((asin, keyword))
            logger.info(f"Görev eklendi - ASIN: {asin}, Keyword: {keyword}")
        except Exception as e:
            logger.error(f"Görev eklenirken hata: {str(e)}")

    async def worker(self):
        """Worker işlemi"""
        while self.is_running:
            try:
                # Kuyruktan görev al
                asin, keyword = await self.queue.get()
                logger.debug(f"Worker görevi aldı - ASIN: {asin}, Keyword: {keyword}")
                
                try:
                    # Rate limit uygula
                    await self.rate_limiter.acquire()
                    
                    # Scraper'ı çalıştır
                    result = await scrape_product(asin, keyword)
                    
                    # Sonucu veritabanına kaydet
                    await self.db.save_result(result)
                    logger.info(f"Sonuç kaydedildi - ASIN: {asin}")
                    
                except Exception as e:
                    logger.error(f"Görev işlenirken hata: {str(e)}")
                    # Hata durumunda boş sonuç kaydet
                    await self.db.save_result({
                        "asin": asin,
                        "keyword": keyword,
                        "found": False,
                        "found_variant": False,
                        "page": 0,
                        "page_position": 0,
                        "total_position": 0,
                        "sponsored": False
                    })
                finally:
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info("Worker iptal edildi")
                break
            except Exception as e:
                logger.error(f"Worker'da beklenmeyen hata: {str(e)}")
                await asyncio.sleep(1)  # Hata durumunda kısa bir bekleme

    async def start_workers(self):
        """Worker'ları başlat"""
        self.is_running = True
        logger.info(f"{self.num_workers} worker başlatılıyor...")
        
        for _ in range(self.num_workers):
            worker = asyncio.create_task(self.worker())
            self.workers.append(worker)
        
        logger.info("Tüm worker'lar başlatıldı")

    async def stop_workers(self):
        """Worker'ları durdur"""
        self.is_running = False
        logger.info("Worker'lar durduruluyor...")
        
        # Tüm worker'ları iptal et
        for worker in self.workers:
            worker.cancel()
        
        # Worker'ların tamamlanmasını bekle
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Tüm worker'lar durduruldu") 