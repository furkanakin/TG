#!/usr/bin/env python3
"""
Session dosyalarını test etmek için yardımcı script
"""

import os
import glob
from telegram_bot import SessionManager

def create_test_sessions():
    """Test için örnek session dosyaları oluşturur"""
    sessions_dir = "Sessions"
    
    # Sessions klasörünü oluştur
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
        print(f"📁 Sessions klasörü oluşturuldu: {sessions_dir}")
    
    # Test session dosyaları oluştur
    test_files = [
        "user1.session",
        "user2.session", 
        "admin.session",
        "test_account.session",
        "demo_user.session"
    ]
    
    created_files = []
    for file_name in test_files:
        file_path = os.path.join(sessions_dir, file_name)
        with open(file_path, 'w') as f:
            f.write(f"Test session data for {file_name}")
        created_files.append(file_name)
        print(f"✅ Test dosyası oluşturuldu: {file_name}")
    
    return created_files

def test_session_manager():
    """SessionManager'ı test eder"""
    print("=" * 50)
    print("🧪 Session Manager Test")
    print("=" * 50)
    
    # SessionManager oluştur
    session_manager = SessionManager()
    
    # Session sayısını al
    count = session_manager.count_session_files()
    print(f"📊 Toplam session dosyası: {count}")
    
    # Session dosyalarını listele
    files = session_manager.get_session_files()
    print(f"📋 Session dosyaları: {files}")
    
    # Detaylı bilgi al
    info = session_manager.get_session_info()
    print(f"📈 Detaylı bilgi: {info}")
    
    return count, files, info

def main():
    """Ana test fonksiyonu"""
    print("🤖 Telegram Bot Session Test")
    print("=" * 40)
    
    # Test session dosyaları oluştur
    print("\n1️⃣ Test session dosyaları oluşturuluyor...")
    created_files = create_test_sessions()
    
    # SessionManager'ı test et
    print("\n2️⃣ SessionManager test ediliyor...")
    count, files, info = test_session_manager()
    
    # Sonuçları göster
    print("\n3️⃣ Test Sonuçları:")
    print(f"✅ Oluşturulan dosya sayısı: {len(created_files)}")
    print(f"✅ Bulunan session sayısı: {count}")
    print(f"✅ Session dosyaları: {files}")
    print(f"✅ Toplam boyut: {info['total_size_mb']} MB")
    
    if count == len(created_files):
        print("\n🎉 Test başarılı! SessionManager doğru çalışıyor.")
    else:
        print(f"\n⚠️ Test başarısız! Beklenen: {len(created_files)}, Bulunan: {count}")

if __name__ == "__main__":
    main()
