#!/usr/bin/env python3
"""
Status alanını kontrol et
"""

import sqlite3

def check_status():
    """Status alanını kontrol et"""
    with sqlite3.connect("telegram_bot.db") as conn:
        cursor = conn.cursor()
        
        # Kanal 4'ün isteklerini kontrol et
        cursor.execute("SELECT id, channel_id, account_name, status FROM request_pool WHERE channel_id = 4")
        requests = cursor.fetchall()
        
        print("Kanal 4 istekleri:")
        for req in requests:
            print(f"ID: {req[0]}, Kanal: {req[1]}, Hesap: {req[2]}, Status: '{req[3]}'")

if __name__ == "__main__":
    check_status()
