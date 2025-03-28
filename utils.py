import logging
import os
from datetime import datetime

def setup_logger(name):
    # Log dizini oluştur
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Log dosyası adı
    log_file = f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log'
    
    # Logger oluştur
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Dosya handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Handler'ları ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 