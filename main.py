#!/usr/bin/env python3
"""
Ana Python uygulaması - Telegram Bot
Bu dosya hem yerel olarak hem de Docker container'da çalışacak
"""

import os
import sys
import logging
from datetime import datetime
from telegram_bot import TelegramBot
from request_processor import request_scheduler

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Ana uygulama fonksiyonu"""
    print("=" * 60)
    print("🤖 Telegram Bot Uygulaması Başlatıldı")
    print("=" * 60)
    
    # Çevre değişkenlerini kontrol et
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python Versiyonu: {sys.version}")
    print(f"📁 Çalışma Dizini: {os.getcwd()}")
    
    # Docker container'da mı çalışıyor kontrol et
    if os.path.exists('/.dockerenv'):
        print("🐳 Docker Container'da çalışıyor")
    else:
        print("💻 Yerel olarak çalışıyor")
    
    # Sessions klasörünü kontrol et
    sessions_dir = "Sessions"
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
        print(f"📁 Sessions klasörü oluşturuldu: {sessions_dir}")
    else:
        print(f"📁 Sessions klasörü mevcut: {sessions_dir}")
    
    # Konfigürasyon dosyasını kontrol et
    config_file = "bot_config.json"
    if not os.path.exists(config_file):
        print(f"⚠️ Konfigürasyon dosyası bulunamadı: {config_file}")
        print("💡 Lütfen config.py dosyasını çalıştırarak konfigürasyonu oluşturun")
        return
    
    print("\n✅ Uygulama başarıyla başlatıldı!")
    print("🤖 Telegram Bot çalışıyor...")
    print("⚙️ İstek işleyici başlatılıyor...")
    print("📊 Loglar konsol çıktısında görünecek")
    print("🔄 Botu durdurmak için Ctrl+C tuşlayın")
    print("=" * 60)
    
    try:
        # İstek işleyiciyi başlat
        request_scheduler.start_processing()
        
        # Telegram Bot'u başlat
        bot = TelegramBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Bot kapatılıyor...")
        logger.info("Bot kullanıcı tarafından durduruldu")
        
        # İstek işleyiciyi durdur
        request_scheduler.stop_processing()
        print("⚙️ İstek işleyici durduruldu")
        
    except Exception as e:
        print(f"❌ Bot hatası: {e}")
        logger.error(f"Bot hatası: {e}")
        
        # İstek işleyiciyi durdur
        request_scheduler.stop_processing()

if __name__ == "__main__":
    main()
