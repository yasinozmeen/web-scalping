import sqlite3
import aiosqlite
from datetime import datetime
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="amazon_scraper.db"):
        self.db_path = db_path
        logger.info(f"🗄️ Veritabanı başlatılıyor: {db_path}")
        self.init_db()
        logger.info("✅ Veritabanı başlatıldı")
    
    def init_db(self):
        """Veritabanı tablolarını oluştur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Sonuçlar tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asin TEXT UNIQUE,
                        keyword TEXT,
                        found BOOLEAN,
                        found_variant TEXT,
                        page INTEGER,
                        page_position INTEGER,
                        total_position INTEGER,
                        sponsored BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("✅ Veritabanı tabloları oluşturuldu")
        except Exception as e:
            logger.error(f"❌ Veritabanı başlatma hatası: {str(e)}", exc_info=True)
            raise
    
    async def save_result(self, result):
        """Sonucu veritabanına kaydet"""
        try:
            logger.info(f"💾 Sonuç kaydediliyor: ASIN={result['asin']}")
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.cursor()
                try:
                    await cursor.execute('''
                        INSERT OR REPLACE INTO results 
                        (asin, keyword, found, found_variant, page, page_position, 
                         total_position, sponsored, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        result['asin'],
                        result['keyword'],
                        result['found'],
                        result['found_variant'],
                        result['page'],
                        result['page_position'],
                        result['total_position'],
                        result['sponsored'],
                        datetime.now()
                    ))
                    await db.commit()
                    logger.info(f"✅ Sonuç kaydedildi: ASIN={result['asin']}")
                except Exception as e:
                    logger.error(f"❌ Veritabanı kayıt hatası: ASIN={result['asin']}, Hata={str(e)}", exc_info=True)
                    await db.rollback()
                    raise
        except Exception as e:
            logger.error(f"❌ Veritabanı bağlantı hatası: {str(e)}", exc_info=True)
            raise
    
    async def get_result(self, asin):
        """ASIN'e göre sonucu getir"""
        try:
            logger.info(f"🔍 Sonuç aranıyor: ASIN={asin}")
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.cursor()
                await cursor.execute('''
                    SELECT * FROM results WHERE asin = ?
                ''', (asin,))
                row = await cursor.fetchone()
                
                if row:
                    result = {
                        'id': row[0],
                        'asin': row[1],
                        'keyword': row[2],
                        'found': bool(row[3]),
                        'found_variant': row[4],
                        'page': row[5],
                        'page_position': row[6],
                        'total_position': row[7],
                        'sponsored': bool(row[8]),
                        'created_at': row[9],
                        'updated_at': row[10]
                    }
                    logger.info(f"✅ Sonuç bulundu: ASIN={asin}")
                    return result
                    
                logger.warning(f"❌ Sonuç bulunamadı: ASIN={asin}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Veritabanı okuma hatası: ASIN={asin}, Hata={str(e)}", exc_info=True)
            raise
            
    async def get_stats(self):
        """İstatistikleri getir"""
        try:
            logger.info("📊 İstatistikler alınıyor...")
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.cursor()
                await cursor.execute('''
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as found_count,
                        AVG(CASE WHEN found = 1 THEN total_position ELSE NULL END) as avg_position
                    FROM results
                ''')
                row = await cursor.fetchone()
                
                stats = {
                    "total_requests": row[0],
                    "found_count": row[1],
                    "avg_position": round(row[2], 2) if row[2] else None
                }
                logger.info(f"✅ İstatistikler alındı: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"❌ İstatistik alma hatası: {str(e)}", exc_info=True)
            raise 