#!/usr/bin/env python3
"""
Kanal güncelleme testi
Aynı kanalı tekrar eklemeyi test eder
"""

import asyncio
from database import db_manager

def test_channel_update():
    """Kanal güncelleme testi"""
    print("🧪 Kanal Güncelleme Testi")
    print("=" * 50)
    
    user_id = "test_user_123"
    channel_link = "https://t.me/+uro2qpwhl5ZiNDhk"
    
    # İlk kanal ekleme
    print("1️⃣ İlk kanal ekleniyor...")
    channel_id1 = db_manager.add_channel(channel_link, 10, 30, user_id)
    print(f"   Kanal ID: {channel_id1}")
    
    # Aynı kanalı tekrar ekleme (güncelleme)
    print("2️⃣ Aynı kanal tekrar ekleniyor (güncelleme)...")
    channel_id2 = db_manager.add_channel(channel_link, 20, 60, user_id)
    print(f"   Kanal ID: {channel_id2}")
    
    # Kontrol
    if channel_id1 == channel_id2:
        print("✅ Başarılı! Kanal güncellendi (aynı ID)")
        
        # Kanal bilgilerini kontrol et
        channel = db_manager.get_channel(channel_id1)
        if channel:
            print(f"   📊 İstek sayısı: {channel['total_requests']} (20 olmalı)")
            print(f"   ⏱️ Süre: {channel['duration_minutes']} dk (60 olmalı)")
            print(f"   📅 Durum: {channel['status']} (active olmalı)")
    else:
        print("❌ Hata! Farklı ID'ler oluştu")
    
    # Kullanıcının kanallarını listele
    print("\n3️⃣ Kullanıcının kanalları:")
    channels = db_manager.get_user_channels(user_id)
    print(f"   Toplam kanal sayısı: {len(channels)}")
    
    for i, ch in enumerate(channels, 1):
        print(f"   {i}. {ch['channel_link']} - {ch['total_requests']} istek, {ch['duration_minutes']} dk")

if __name__ == "__main__":
    test_channel_update()
