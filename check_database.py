#!/usr/bin/env python3
"""
Veritabanını kontrol et
"""

import sqlite3
from database import db_manager

def check_database():
    """Veritabanını kontrol et"""
    print("🔍 Veritabanı Kontrolü")
    print("=" * 50)
    
    # Veritabanına bağlan
    with sqlite3.connect("telegram_bot.db") as conn:
        cursor = conn.cursor()
        
        # Kanalları kontrol et
        print("1️⃣ Kanallar:")
        cursor.execute("SELECT * FROM channels")
        channels = cursor.fetchall()
        print(f"   Toplam kanal: {len(channels)}")
        for ch in channels:
            print(f"   - ID: {ch[0]}, Link: {ch[1]}, İstek: {ch[2]}, Süre: {ch[3]}, Durum: {ch[5]}")
        
        # İstek havuzunu kontrol et
        print("\n2️⃣ İstek Havuzu:")
        cursor.execute("SELECT * FROM request_pool")
        requests = cursor.fetchall()
        print(f"   Toplam istek: {len(requests)}")
        for req in requests:
            print(f"   - ID: {req[0]}, Kanal: {req[1]}, Hesap: {req[2]}, Zaman: {req[3]}, Durum: {req[5]}")
        
        # Hesapları kontrol et
        print("\n3️⃣ Hesaplar:")
        cursor.execute("SELECT * FROM accounts")
        accounts = cursor.fetchall()
        print(f"   Toplam hesap: {len(accounts)}")
        for acc in accounts:
            print(f"   - Session: {acc[0]}, Proxy: {acc[1]}, Aktif: {acc[3]}")

if __name__ == "__main__":
    check_database()
