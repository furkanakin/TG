#!/usr/bin/env python3
"""
Loglama test dosyası
Log mesajlarının düzgün çalışıp çalışmadığını test eder
"""

import logging
import asyncio
from telethon_client import telethon_manager
from request_processor import request_scheduler

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_logging():
    """Loglama testi"""
    print("🧪 Loglama Testi Başlatılıyor")
    print("=" * 50)
    
    # Farklı log seviyelerini test et
    logger.debug("🔍 Debug mesajı - Bu görünmemeli (INFO seviyesi)")
    logger.info("ℹ️ Info mesajı - Bu görünmeli")
    logger.warning("⚠️ Warning mesajı - Bu görünmeli")
    logger.error("❌ Error mesajı - Bu görünmeli")
    
    print("\n📊 Loglama testi tamamlandı!")
    print("Eğer yukarıdaki mesajları görüyorsanız loglama çalışıyor.")

async def test_telethon_logging():
    """Telethon loglama testi"""
    print("\n🔗 Telethon Loglama Testi")
    print("=" * 50)
    
    # Test session dosyası oluştur
    import os
    sessions_dir = "Sessions"
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
    
    test_session = "test_logging.session"
    session_path = os.path.join(sessions_dir, test_session)
    
    with open(session_path, 'w') as f:
        f.write("Test session data for logging")
    
    print(f"✅ Test session oluşturuldu: {test_session}")
    
    # Telethon manager'ı test et
    try:
        # Client oluşturma testi (başarısız olacak ama logları göreceğiz)
        logger.info("📱 Telethon client oluşturma testi başlatılıyor...")
        client = await telethon_manager.create_client(test_session)
        
        if client:
            logger.info("✅ Client başarıyla oluşturuldu")
            await client.disconnect()
        else:
            logger.warning("⚠️ Client oluşturulamadı (beklenen)")
            
    except Exception as e:
        logger.error(f"❌ Telethon test hatası: {e}")
    
    # Test dosyasını temizle
    if os.path.exists(session_path):
        os.remove(session_path)
        print(f"🗑️ Test session temizlendi: {test_session}")

def test_request_processor_logging():
    """Request processor loglama testi"""
    print("\n⚙️ Request Processor Loglama Testi")
    print("=" * 50)
    
    try:
        # İşleyici durumunu kontrol et
        status = request_scheduler.get_processing_status()
        logger.info(f"📊 İşleyici durumu: {status}")
        
        # Bekleyen istek sayısını kontrol et
        pending_count = request_scheduler.get_pending_requests_count()
        logger.info(f"📋 Bekleyen istek sayısı: {pending_count}")
        
        # Manuel işleme testi
        logger.info("🔄 Manuel istek işleme testi başlatılıyor...")
        processed = request_scheduler.force_process_requests()
        logger.info(f"✅ Manuel işlenen istek sayısı: {processed}")
        
    except Exception as e:
        logger.error(f"❌ Request processor test hatası: {e}")

async def main():
    """Ana test fonksiyonu"""
    print("🧪 Telegram Bot Loglama Test Sistemi")
    print("=" * 60)
    
    # Temel loglama testi
    test_logging()
    
    # Telethon loglama testi
    await test_telethon_logging()
    
    # Request processor loglama testi
    test_request_processor_logging()
    
    print("\n" + "=" * 60)
    print("🎉 Tüm loglama testleri tamamlandı!")
    print("Eğer yukarıdaki log mesajlarını görüyorsanız sistem hazır.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
