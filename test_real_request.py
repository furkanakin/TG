#!/usr/bin/env python3
"""
Gerçek istek testi
Sistemin gerçekten çalışıp çalışmadığını test eder
"""

import asyncio
import logging
from database import db_manager
from request_processor import request_scheduler

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_real_request():
    """Gerçek istek testi"""
    print("🧪 Gerçek İstek Testi Başlatılıyor")
    print("=" * 60)
    
    try:
        # Test kanalı oluştur
        channel_id = db_manager.add_channel(
            "https://t.me/+test123456789", 
            3,  # 3 istek
            5,  # 5 dakika
            "test_user_456"
        )
        
        if not channel_id:
            print("❌ Test kanalı oluşturulamadı!")
            return
        
        print(f"✅ Test kanalı oluşturuldu: ID={channel_id}")
        
        # Test session dosyaları oluştur
        import os
        sessions_dir = "Sessions"
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
        
        test_sessions = ["test1.session", "test2.session", "test3.session"]
        for session_file in test_sessions:
            session_path = os.path.join(sessions_dir, session_file)
            with open(session_path, 'w') as f:
                f.write(f"Test session data for {session_file}")
            print(f"✅ Test session oluşturuldu: {session_file}")
        
        # Proxy listesi oluştur (boş)
        proxies = []
        
        # İstek havuzunu oluştur
        print("🔄 İstek havuzu oluşturuluyor...")
        success = db_manager.create_request_pool(channel_id, test_sessions, proxies)
        
        if success:
            print("✅ İstek havuzu oluşturuldu")
            
            # İstek istatistiklerini göster
            stats = db_manager.get_request_stats(channel_id)
            print(f"📊 İstek istatistikleri: {stats}")
            
            # Bekleyen istekleri göster
            pending_requests = db_manager.get_pending_requests(10)
            print(f"📋 Bekleyen istek sayısı: {len(pending_requests)}")
            
            for i, req in enumerate(pending_requests, 1):
                print(f"  {i}. {req['account_name']} -> {req['channel_link']} (Zaman: {req['scheduled_time']})")
            
            print("\n🚀 İstek işleme başlatılıyor...")
            print("=" * 60)
            
            # İstek işleyiciyi başlat
            request_scheduler.start_processing()
            
            # 10 saniye bekle
            print("⏳ 10 saniye bekleniyor...")
            await asyncio.sleep(10)
            
            # İstek işleyiciyi durdur
            request_scheduler.stop_processing()
            
            # Son istatistikleri göster
            final_stats = db_manager.get_request_stats(channel_id)
            print(f"\n📊 Final istatistikler: {final_stats}")
            
        else:
            print("❌ İstek havuzu oluşturulamadı!")
        
        # Test dosyalarını temizle
        print("\n🗑️ Test dosyaları temizleniyor...")
        for session_file in test_sessions:
            session_path = os.path.join(sessions_dir, session_file)
            if os.path.exists(session_path):
                os.remove(session_path)
                print(f"✅ Test session temizlendi: {session_file}")
        
        print("\n🎉 Test tamamlandı!")
        
    except Exception as e:
        logger.error(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_request())
