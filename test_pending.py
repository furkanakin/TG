#!/usr/bin/env python3
"""
Bekleyen istekleri test et
"""

from database import db_manager

def test_pending():
    """Bekleyen istekleri test et"""
    print("🔍 Bekleyen İstekler Testi")
    print("=" * 50)
    
    # Bekleyen istekleri al
    pending_requests = db_manager.get_pending_requests(limit=10)
    print(f"Bekleyen istek sayısı: {len(pending_requests)}")
    
    for req in pending_requests:
        print(f"- ID: {req['id']}, Kanal: {req['channel_id']}, Hesap: {req['account_name']}, Zaman: {req['scheduled_time']}, Durum: {req['status']}")

if __name__ == "__main__":
    test_pending()
