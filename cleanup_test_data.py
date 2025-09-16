#!/usr/bin/env python3
"""
Test verilerini temizleme scripti
Veritabanındaki test verilerini temizler
"""

import os
import sqlite3
from database import db_manager

def cleanup_test_data():
    """Test verilerini temizler"""
    print("🧹 Test Verileri Temizleniyor...")
    print("=" * 50)
    
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Test kanallarını sil
            cursor.execute("DELETE FROM channels WHERE user_id LIKE 'test_%'")
            test_channels_deleted = cursor.rowcount
            print(f"✅ {test_channels_deleted} test kanalı silindi")
            
            # Test isteklerini sil
            cursor.execute("""
                DELETE FROM request_pool 
                WHERE channel_id IN (
                    SELECT id FROM channels WHERE user_id LIKE 'test_%'
                )
            """)
            test_requests_deleted = cursor.rowcount
            print(f"✅ {test_requests_deleted} test isteği silindi")
            
            # Test hesaplarını sil
            cursor.execute("DELETE FROM accounts WHERE session_file LIKE 'test%'")
            test_accounts_deleted = cursor.rowcount
            print(f"✅ {test_accounts_deleted} test hesabı silindi")
            
            # Test kullanıcı durumlarını sil
            cursor.execute("DELETE FROM user_states WHERE user_id LIKE 'test_%'")
            test_states_deleted = cursor.rowcount
            print(f"✅ {test_states_deleted} test kullanıcı durumu silindi")
            
            conn.commit()
            
            print(f"\n🎉 Temizlik tamamlandı!")
            print(f"Toplam silinen kayıt: {test_channels_deleted + test_requests_deleted + test_accounts_deleted + test_states_deleted}")
            
    except Exception as e:
        print(f"❌ Temizlik hatası: {e}")

def show_current_data():
    """Mevcut verileri gösterir"""
    print("\n📊 Mevcut Veriler:")
    print("=" * 30)
    
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Kanallar
            cursor.execute("SELECT COUNT(*) FROM channels")
            channel_count = cursor.fetchone()[0]
            print(f"📺 Kanallar: {channel_count}")
            
            # İstekler
            cursor.execute("SELECT COUNT(*) FROM request_pool")
            request_count = cursor.fetchone()[0]
            print(f"📋 İstekler: {request_count}")
            
            # Hesaplar
            cursor.execute("SELECT COUNT(*) FROM accounts")
            account_count = cursor.fetchone()[0]
            print(f"👤 Hesaplar: {account_count}")
            
            # Kullanıcı durumları
            cursor.execute("SELECT COUNT(*) FROM user_states")
            state_count = cursor.fetchone()[0]
            print(f"🔄 Kullanıcı durumları: {state_count}")
            
    except Exception as e:
        print(f"❌ Veri okuma hatası: {e}")

def check_sessions():
    """Session dosyalarını kontrol eder"""
    print("\n📁 Session Dosyaları:")
    print("=" * 30)
    
    sessions_dir = "Sessions"
    if not os.path.exists(sessions_dir):
        print("❌ Sessions klasörü bulunamadı!")
        return
    
    session_files = []
    for file in os.listdir(sessions_dir):
        if file.endswith('.session'):
            session_files.append(file)
    
    if session_files:
        print(f"✅ {len(session_files)} session dosyası bulundu:")
        for i, file in enumerate(session_files, 1):
            file_path = os.path.join(sessions_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  {i}. {file} ({file_size} bytes)")
    else:
        print("⚠️ Hiç session dosyası bulunamadı!")
        print("💡 Sessions klasörüne .session dosyalarınızı koyun")

if __name__ == "__main__":
    print("🧹 Telegram Bot Test Verileri Temizleme")
    print("=" * 60)
    
    # Mevcut verileri göster
    show_current_data()
    
    # Session dosyalarını kontrol et
    check_sessions()
    
    # Temizlik yap
    cleanup_test_data()
    
    # Temizlik sonrası verileri göster
    print("\n📊 Temizlik Sonrası Veriler:")
    show_current_data()
    
    print("\n✅ Temizlik işlemi tamamlandı!")
    print("Artık gerçek session dosyalarınızla çalışabilirsiniz.")
