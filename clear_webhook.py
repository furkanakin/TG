#!/usr/bin/env python3
"""
Webhook'u temizle ve bot'u yeniden başlat
"""

import requests
import json

def clear_webhook():
    """Webhook'u temizle"""
    bot_token = "8477982423:AAE33t98g_1GC9tF8kNCcU79MaP_g8msqZs"
    
    # Webhook'u sil
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    response = requests.post(url)
    
    print(f"Webhook silme: {response.status_code}")
    print(f"Yanıt: {response.text}")
    
    # Bot bilgilerini al
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url)
    
    print(f"\nBot bilgileri: {response.status_code}")
    print(f"Yanıt: {response.text}")

if __name__ == "__main__":
    clear_webhook()
