#!/usr/bin/env python3
"""
İstek işleme sınıfı
Bekleyen istekleri sürekli kontrol eder ve işler
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict
from database import db_manager
from telethon_client import telethon_manager

logger = logging.getLogger(__name__)

class RequestProcessor:
    """İstek işleme sınıfı"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval  # saniye
        self.is_running = False
        self.process_thread = None
        self.stop_event = threading.Event()
    
    def start(self) -> None:
        """İstek işleyiciyi başlatır"""
        if self.is_running:
            logger.warning("İstek işleyici zaten çalışıyor")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # Ayrı thread'de çalıştır
        self.process_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.process_thread.start()
        
        logger.info("İstek işleyici başlatıldı")
    
    def stop(self) -> None:
        """İstek işleyiciyi durdurur"""
        if not self.is_running:
            logger.warning("İstek işleyici zaten durmuş")
            return
        
        self.is_running = False
        self.stop_event.set()
        
        if self.process_thread:
            self.process_thread.join(timeout=5)
        
        logger.info("İstek işleyici durduruldu")
    
    def _run_loop(self) -> None:
        """Ana döngü - ayrı thread'de çalışır"""
        while self.is_running and not self.stop_event.is_set():
            try:
                # Asyncio event loop oluştur
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # İstekleri işle
                loop.run_until_complete(self._process_cycle())
                
                # Event loop'u kapat
                loop.close()
                
            except Exception as e:
                logger.error(f"İstek işleme döngüsü hatası: {e}")
            
            # Bekle
            self.stop_event.wait(self.check_interval)
    
    async def _process_cycle(self) -> None:
        """Tek işlem döngüsü"""
        try:
            logger.debug("🔄 İstek işleme döngüsü başlatıldı")
            
            # Bekleyen istekleri işle (sadece 1 tane, sıralı)
            processed_count = await telethon_manager.process_pending_requests(limit=1)
            
            if processed_count > 0:
                logger.info(f"✅ {processed_count} istek başarıyla işlendi")
            else:
                logger.debug("📭 İşlenecek istek bulunamadı")
            
            # Eski client'ları temizle (5 dakikadan eski)
            await self._cleanup_old_clients()
            
        except Exception as e:
            logger.error(f"💥 İşlem döngüsü hatası: {e}")
    
    async def _cleanup_old_clients(self) -> None:
        """Eski client'ları temizler"""
        try:
            # 5 dakikadan eski client'ları temizle
            await telethon_manager.cleanup_clients()
        except Exception as e:
            logger.error(f"Client temizleme hatası: {e}")
    
    def get_status(self) -> Dict:
        """İşleyici durumunu döndürür"""
        return {
            'is_running': self.is_running,
            'active_clients': telethon_manager.get_active_clients_count(),
            'check_interval': self.check_interval
        }
    
    def force_process(self) -> int:
        """Manuel olarak istekleri işler"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                telethon_manager.process_pending_requests(limit=20)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Manuel işleme hatası: {e}")
            return 0

class RequestScheduler:
    """İstek zamanlayıcı sınıfı"""
    
    def __init__(self):
        self.processor = RequestProcessor()
    
    def start_processing(self) -> None:
        """İstek işlemeyi başlatır"""
        self.processor.start()
        logger.info("İstek zamanlayıcı başlatıldı")
    
    def stop_processing(self) -> None:
        """İstek işlemeyi durdurur"""
        self.processor.stop()
        logger.info("İstek zamanlayıcı durduruldu")
    
    def get_processing_status(self) -> Dict:
        """İşleme durumunu döndürür"""
        return self.processor.get_status()
    
    def force_process_requests(self) -> int:
        """Manuel olarak istekleri işler"""
        return self.processor.force_process()
    
    def get_channel_stats(self, channel_id: int) -> Dict:
        """Kanal istatistiklerini döndürür"""
        return db_manager.get_request_stats(channel_id)
    
    def get_pending_requests_count(self) -> int:
        """Bekleyen istek sayısını döndürür"""
        try:
            requests = db_manager.get_pending_requests(limit=1000)
            return len(requests)
        except Exception as e:
            logger.error(f"Bekleyen istek sayısı alınamadı: {e}")
            return 0

# Global scheduler instance'ı
request_scheduler = RequestScheduler()

if __name__ == "__main__":
    # Test
    scheduler = RequestScheduler()
    
    print("İstek zamanlayıcı test ediliyor...")
    print(f"Durum: {scheduler.get_processing_status()}")
    
    # Manuel işleme testi
    processed = scheduler.force_process_requests()
    print(f"Manuel işlenen istek: {processed}")
    
    # Bekleyen istek sayısı
    pending = scheduler.get_pending_requests_count()
    print(f"Bekleyen istek sayısı: {pending}")
