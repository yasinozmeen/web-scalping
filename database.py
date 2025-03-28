import sqlite3
import aiosqlite
from typing import Dict, Optional
import os
from utils import setup_logger

# Logging yapılandırması
logger = setup_logger('database')

class Database:
    def __init__(self, db_path: str = "amazon_scraper.db"):
        self.db_path = db_path
        self.init_db()
        logger.info(f"Veritabanı başlatıldı: {db_path}")

    def init_db(self):
        """Veritabanını oluştur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asin TEXT NOT NULL,
                        keyword TEXT NOT NULL,
                        found BOOLEAN NOT NULL,
                        found_variant BOOLEAN NOT NULL,
                        page INTEGER,
                        page_position INTEGER,
                        total_position INTEGER,
                        sponsored BOOLEAN NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Veritabanı tablosu oluşturuldu")
        except Exception as e:
            logger.error(f"Veritabanı oluşturulurken hata: {str(e)}")
            raise

    async def save_result(self, result: Dict):
        """Sonucu veritabanına kaydet"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.cursor()
                await cursor.execute("""
                    INSERT OR REPLACE INTO results (
                        asin, keyword, found, found_variant, page,
                        page_position, total_position, sponsored, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    result["asin"],
                    result["keyword"],
                    result["found"],
                    result["found_variant"],
                    result["page"],
                    result["page_position"],
                    result["total_position"],
                    result["sponsored"]
                ))
                await db.commit()
                logger.debug(f"Sonuç kaydedildi - ASIN: {result['asin']}")
        except Exception as e:
            logger.error(f"Sonuç kaydedilirken hata: {str(e)}")
            raise

    async def get_result(self, asin: str) -> Optional[Dict]:
        """ASIN için sonucu getir"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.cursor()
                await cursor.execute("""
                    SELECT * FROM results WHERE asin = ?
                """, (asin,))
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "asin": row[1],
                        "keyword": row[2],
                        "found": bool(row[3]),
                        "found_variant": bool(row[4]),
                        "page": row[5],
                        "page_position": row[6],
                        "total_position": row[7],
                        "sponsored": bool(row[8]),
                        "created_at": row[9],
                        "updated_at": row[10]
                    }
                return None
        except Exception as e:
            logger.error(f"Sonuç getirilirken hata: {str(e)}")
            raise

    async def get_stats(self) -> Dict:
        """İstatistikleri getir"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.cursor()
                
                # Toplam istek sayısı
                await cursor.execute("SELECT COUNT(*) FROM results")
                total_requests = (await cursor.fetchone())[0]
                
                # Bulunan ürün sayısı
                await cursor.execute("SELECT COUNT(*) FROM results WHERE found = 1")
                found_count = (await cursor.fetchone())[0]
                
                # Ortalama pozisyon
                await cursor.execute("""
                    SELECT AVG(total_position) 
                    FROM results 
                    WHERE found = 1 AND total_position > 0
                """)
                avg_position = (await cursor.fetchone())[0] or 0
                
                return {
                    "total_requests": total_requests,
                    "found_count": found_count,
                    "not_found_count": total_requests - found_count,
                    "average_position": round(avg_position, 2)
                }
        except Exception as e:
            logger.error(f"İstatistikler getirilirken hata: {str(e)}")
            raise 