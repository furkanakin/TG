#!/usr/bin/env python3
"""
İstek akışını test et
"""

import asyncio
import time
import os
from database import db_manager
from telethon_client import telethon_manager

async def test_request_flow():
    """İstek akışını test et"""
    print("🧪 İstek Akışı Testi")
    print("=" * 50)
    
    # 1. Kanal ekle
    user_id = "test_user_123"
    channel_link = "https://t.me/+test999999999"
    
    print("1️⃣ Kanal ekleniyor...")
    channel_id = db_manager.add_channel(channel_link, 5, 2, user_id)  # 2 dakika
    print(f"   Kanal ID: {channel_id}")
    
    if not channel_id:
        print("❌ Kanal eklenemedi!")
        return
    
    # 2. Session dosyalarını al
    print("2️⃣ Session dosyaları alınıyor...")
    session_files = []
    for file in os.listdir("Sessions"):
        if file.endswith(".session"):
            session_files.append(file)
    
    print(f"   Bulunan session dosyaları: {len(session_files)}")
    for sf in session_files:
        print(f"   - {sf}")
    
    # 3. İstek havuzunu oluştur
    print("3️⃣ İstek havuzu oluşturuluyor...")
    success = db_manager.create_request_pool(channel_id, session_files, [])
    print(f"   İstek havuzu: {'✅' if success else '❌'}")
    
    # 4. Bekleyen istekleri kontrol et
    print("4️⃣ Bekleyen istekler kontrol ediliyor...")
    pending_requests = db_manager.get_pending_requests(limit=10)
    print(f"   Bekleyen istek sayısı: {len(pending_requests)}")
    
    for req in pending_requests:
        print(f"   - {req['account_name']} -> {req['channel_link']} ({req['scheduled_time']})")
    
    # 5. İstekleri işle
    print("5️⃣ İstekler işleniyor...")
    processed_count = await telethon_manager.process_pending_requests(limit=5)
    print(f"   İşlenen istek sayısı: {processed_count}")
    
    # 6. Sonuçları kontrol et
    print("6️⃣ Sonuçlar kontrol ediliyor...")
    all_requests = db_manager.get_pending_requests(limit=100)
    
    for req in all_requests:
        status_emoji = "✅" if req['status'] == 'Gönderildi' else "⏳" if req['status'] == 'Bekliyor' else "❌"
        print(f"   {status_emoji} {req['account_name']} -> {req['status']}")

if __name__ == "__main__":
    asyncio.run(test_request_flow())
