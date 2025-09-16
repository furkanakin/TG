#!/usr/bin/env python3
"""
İstek işleme testi
"""

import asyncio
from database import db_manager
from telethon_client import telethon_manager

async def test_process():
    """İstek işleme testi"""
    print("🔄 İstek İşleme Testi")
    print("=" * 50)
    
    # Bekleyen istekleri al
    pending_requests = db_manager.get_pending_requests(limit=10)
    print(f"Bekleyen istek sayısı: {len(pending_requests)}")
    
    # İstekleri işle
    processed_count = await telethon_manager.process_pending_requests(limit=5)
    print(f"İşlenen istek sayısı: {processed_count}")
    
    # Sonuçları kontrol et
    pending_requests = db_manager.get_pending_requests(limit=10)
    print(f"Kalan bekleyen istek sayısı: {len(pending_requests)}")

if __name__ == "__main__":
    asyncio.run(test_process())
