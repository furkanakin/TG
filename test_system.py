#!/usr/bin/env python3
"""
Sistem test dosyası
Tüm bileşenleri test eder
"""

import os
import asyncio
import logging
from database import db_manager
from proxy_manager import proxy_manager
from telethon_client import telethon_manager
from request_processor import request_scheduler

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database():
    """Veritabanı testi"""
    print("=" * 50)
    print("🗄️ Veritabanı Testi")
    print("=" * 50)
    
    try:
        # Test kanal ekleme
        channel_id = db_manager.add_channel("https://t.me/test_channel", 10, 60, "123456789")
        print(f"✅ Test kanalı eklendi: {channel_id}")
        
        # Test kanal getirme
        channel = db_manager.get_channel(channel_id)
        print(f"✅ Kanal bilgisi alındı: {channel['channel_link']}")
        
        # Test kullanıcı kanalları
        channels = db_manager.get_user_channels("123456789")
        print(f"✅ Kullanıcı kanalları: {len(channels)} adet")
        
        # Test istatistikler
        stats = db_manager.get_request_stats(channel_id)
        print(f"✅ İstek istatistikleri: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Veritabanı testi başarısız: {e}")
        return False

def test_proxy_manager():
    """Proxy manager testi"""
    print("\n" + "=" * 50)
    print("🌐 Proxy Manager Testi")
    print("=" * 50)
    
    try:
        # Proxy sayısını kontrol et
        proxy_count = proxy_manager.get_proxy_count()
        print(f"✅ Yüklenen proxy sayısı: {proxy_count}")
        
        if proxy_count > 0:
            # Test proxy string
            proxy = proxy_manager.proxies[0]
            proxy_string = proxy_manager.get_proxy_string(proxy)
            print(f"✅ Proxy string: {proxy_string}")
            
            # Test telethon proxy
            telethon_proxy = proxy_manager.get_telethon_proxy(proxy)
            print(f"✅ Telethon proxy: {telethon_proxy}")
        
        # Test session-proxy ataması
        test_sessions = ["user1.session", "user2.session", "user3.session"]
        assignments = proxy_manager.assign_proxies_to_accounts(test_sessions)
        print(f"✅ Proxy atamaları: {len(assignments)} adet")
        
        return True
        
    except Exception as e:
        print(f"❌ Proxy manager testi başarısız: {e}")
        return False

async def test_telethon():
    """Telethon testi"""
    print("\n" + "=" * 50)
    print("📱 Telethon Testi")
    print("=" * 50)
    
    try:
        # Session dosyalarını kontrol et
        sessions_dir = "Sessions"
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
            print(f"✅ Sessions klasörü oluşturuldu: {sessions_dir}")
        
        # Test session dosyaları oluştur
        test_sessions = ["test1.session", "test2.session"]
        for session_file in test_sessions:
            session_path = os.path.join(sessions_dir, session_file)
            if not os.path.exists(session_path):
                with open(session_path, 'w') as f:
                    f.write("Test session data")
                print(f"✅ Test session oluşturuldu: {session_file}")
        
        # Telethon manager testi
        print("✅ Telethon manager başlatıldı")
        
        # Client sayısını kontrol et
        client_count = telethon_manager.get_active_clients_count()
        print(f"✅ Aktif client sayısı: {client_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Telethon testi başarısız: {e}")
        return False

def test_request_processor():
    """İstek işleyici testi"""
    print("\n" + "=" * 50)
    print("⚙️ İstek İşleyici Testi")
    print("=" * 50)
    
    try:
        # İşleyici durumunu kontrol et
        status = request_scheduler.get_processing_status()
        print(f"✅ İşleyici durumu: {status}")
        
        # Bekleyen istek sayısını kontrol et
        pending_count = request_scheduler.get_pending_requests_count()
        print(f"✅ Bekleyen istek sayısı: {pending_count}")
        
        # Manuel işleme testi
        processed = request_scheduler.force_process_requests()
        print(f"✅ Manuel işlenen istek: {processed}")
        
        return True
        
    except Exception as e:
        print(f"❌ İstek işleyici testi başarısız: {e}")
        return False

def test_integration():
    """Entegrasyon testi"""
    print("\n" + "=" * 50)
    print("🔗 Entegrasyon Testi")
    print("=" * 50)
    
    try:
        # Test kanal oluştur
        channel_id = db_manager.add_channel("https://t.me/integration_test", 5, 30, "999999999")
        print(f"✅ Entegrasyon test kanalı oluşturuldu: {channel_id}")
        
        # Session dosyalarını al
        session_files = ["test1.session", "test2.session"]
        
        # Proxy'leri al
        proxy_manager.reload_proxies()
        proxies = [proxy_manager.get_proxy_string(p) for p in proxy_manager.proxies]
        
        # İstek havuzunu oluştur
        success = db_manager.create_request_pool(channel_id, session_files, proxies)
        print(f"✅ İstek havuzu oluşturuldu: {success}")
        
        # İstek istatistiklerini kontrol et
        stats = db_manager.get_request_stats(channel_id)
        print(f"✅ İstek istatistikleri: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Entegrasyon testi başarısız: {e}")
        return False

async def main():
    """Ana test fonksiyonu"""
    print("🧪 Telegram Bot Sistemi Test Başlatılıyor")
    print("=" * 60)
    
    tests = [
        ("Veritabanı", test_database),
        ("Proxy Manager", test_proxy_manager),
        ("Telethon", test_telethon),
        ("İstek İşleyici", test_request_processor),
        ("Entegrasyon", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} testi hata: {e}")
            results.append((test_name, False))
    
    # Sonuçları göster
    print("\n" + "=" * 60)
    print("📊 Test Sonuçları")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print(f"\nToplam: {passed}/{total} test başarılı")
    
    if passed == total:
        print("🎉 Tüm testler başarılı! Sistem hazır.")
    else:
        print("⚠️ Bazı testler başarısız. Lütfen hataları kontrol edin.")

if __name__ == "__main__":
    asyncio.run(main())
