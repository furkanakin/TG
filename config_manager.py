#!/usr/bin/env python3
"""
Telegram Bot Konfigürasyon Yöneticisi
Bu dosya ile bot ayarlarını kolayca yönetebilirsiniz
"""

import json
import os
from typing import List, Dict, Any

class ConfigManager:
    """Konfigürasyon yönetimi için yardımcı sınıf"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
    
    def add_bot_api(self, bot_api: str) -> bool:
        """Yeni bot API ekler (virgülle ayrılmış)"""
        try:
            # Mevcut konfigürasyonu oku
            config = self.load_config()
            
            # Bot API'leri virgülle ayır
            new_apis = [api.strip() for api in bot_api.split(',') if api.strip()]
            
            # Mevcut API'leri al
            existing_apis = config.get("bot_apis", [])
            if isinstance(existing_apis, str):
                existing_apis = [existing_apis]
            
            # Yeni API'leri ekle
            for api in new_apis:
                if api not in existing_apis:
                    existing_apis.append(api)
            
            config["bot_apis"] = existing_apis
            return self.save_config(config)
            
        except Exception as e:
            print(f"❌ Bot API eklenemedi: {e}")
            return False
    
    def add_admin_ids(self, admin_ids: str) -> bool:
        """Yeni admin ID'leri ekler (virgülle ayrılmış)"""
        try:
            # Mevcut konfigürasyonu oku
            config = self.load_config()
            
            # Admin ID'leri virgülle ayır
            new_admins = [admin.strip() for admin in admin_ids.split(',') if admin.strip()]
            
            # Mevcut admin'leri al
            existing_admins = config.get("admin_ids", [])
            
            # Yeni admin'leri ekle
            for admin in new_admins:
                if admin not in existing_admins:
                    existing_admins.append(admin)
            
            config["admin_ids"] = existing_admins
            return self.save_config(config)
            
        except Exception as e:
            print(f"❌ Admin ID'leri eklenemedi: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """Konfigürasyon dosyasını yükler"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️ Konfigürasyon dosyası okunamadı: {e}")
                return {}
        return {}
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Konfigürasyonu dosyaya kaydeder"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Konfigürasyon kaydedilemedi: {e}")
            return False
    
    def show_config(self) -> str:
        """Mevcut konfigürasyonu gösterir"""
        config = self.load_config()
        
        bot_apis = config.get("bot_apis", [])
        if isinstance(bot_apis, str):
            bot_apis = [bot_apis]
        
        admin_ids = config.get("admin_ids", [])
        
        result = "🤖 Mevcut Bot Konfigürasyonu:\n"
        result += "=" * 40 + "\n"
        
        result += f"📱 Bot API'leri ({len(bot_apis)} adet):\n"
        for i, api in enumerate(bot_apis, 1):
            api_preview = f"{api[:10]}...{api[-10:]}" if len(api) > 20 else api
            result += f"  {i}. {api_preview}\n"
        
        result += f"\n👑 Admin ID'leri ({len(admin_ids)} adet):\n"
        for i, admin in enumerate(admin_ids, 1):
            result += f"  {i}. {admin}\n"
        
        return result
    
    def reset_config(self) -> bool:
        """Konfigürasyonu sıfırlar"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            print("✅ Konfigürasyon sıfırlandı")
            return True
        except Exception as e:
            print(f"❌ Konfigürasyon sıfırlanamadı: {e}")
            return False

def main():
    """Ana fonksiyon - interaktif konfigürasyon yöneticisi"""
    manager = ConfigManager()
    
    while True:
        print("\n" + "="*50)
        print("🤖 Telegram Bot Konfigürasyon Yöneticisi")
        print("="*50)
        print("1. Mevcut konfigürasyonu göster")
        print("2. Bot API ekle")
        print("3. Admin ID ekle")
        print("4. Konfigürasyonu sıfırla")
        print("5. Çıkış")
        
        choice = input("\nSeçiminizi yapın (1-5): ").strip()
        
        if choice == "1":
            print(manager.show_config())
        
        elif choice == "2":
            bot_api = input("Bot API'yi girin (virgülle ayırarak birden fazla ekleyebilirsiniz): ").strip()
            if bot_api:
                if manager.add_bot_api(bot_api):
                    print("✅ Bot API başarıyla eklendi!")
                else:
                    print("❌ Bot API eklenemedi!")
            else:
                print("⚠️ Boş API girildi!")
        
        elif choice == "3":
            admin_ids = input("Admin ID'lerini girin (virgülle ayırarak birden fazla ekleyebilirsiniz): ").strip()
            if admin_ids:
                if manager.add_admin_ids(admin_ids):
                    print("✅ Admin ID'leri başarıyla eklendi!")
                else:
                    print("❌ Admin ID'leri eklenemedi!")
            else:
                print("⚠️ Boş Admin ID girildi!")
        
        elif choice == "4":
            confirm = input("Konfigürasyonu sıfırlamak istediğinizden emin misiniz? (evet/hayır): ").strip().lower()
            if confirm in ["evet", "e", "yes", "y"]:
                if manager.reset_config():
                    print("✅ Konfigürasyon sıfırlandı!")
                else:
                    print("❌ Konfigürasyon sıfırlanamadı!")
            else:
                print("❌ İşlem iptal edildi!")
        
        elif choice == "5":
            print("👋 Çıkılıyor...")
            break
        
        else:
            print("❌ Geçersiz seçim! Lütfen 1-5 arası bir sayı girin.")

if __name__ == "__main__":
    main()
