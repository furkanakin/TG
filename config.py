#!/usr/bin/env python3
"""
Telegram Bot Konfigürasyon Dosyası
Bu dosyada bot API ve admin bilgileri saklanır
"""

import os
import json
from typing import List, Dict, Any

# Sabitlenen kimlik bilgileri: Bu değerler kullanılır, dosya yapılandırmasına ihtiyaç yok
# DİKKAT: Bu yaklaşım token'ı repoda düz metin olarak saklar.
# İstenirse daha sonra ortam değişkenlerine taşınabilir.
FIXED_BOT_API: str = "8477982423:AAE33t98g_1GC9tF8kNCcU79MaP_g8msqZs"
FIXED_ADMIN_IDS: List[str] = ["1113025571"]

class BotConfig:
    """Telegram Bot konfigürasyon sınıfı"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Konfigürasyon dosyasını yükler"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️ Konfigürasyon dosyası okunamadı: {e}")
                return self.create_default_config()
        else:
            return self.create_default_config()
    
    def create_default_config(self) -> Dict[str, Any]:
        """Varsayılan konfigürasyon oluşturur"""
        default_config = {
            "bot_api": "8477982423:AAE33t98g_1GC9tF8kNCcU79MaP_g8msqZs",
            "admin_ids": ["1113025571"],
            "webhook_url": "",
            "webhook_port": 8443,
            "debug_mode": True,
            "max_file_size": 20,  # MB
            "allowed_file_types": ["jpg", "jpeg", "png", "gif", "mp4", "mp3", "pdf", "txt", "doc", "docx"],
            "bot_settings": {
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "disable_notification": False
            }
        }
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Konfigürasyonu dosyaya kaydeder"""
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Konfigürasyon kaydedilemedi: {e}")
            return False
    
    def get_bot_api(self) -> str:
        """Bot API token'ını döndürür"""
        return self.config.get("bot_api", "")
    
    def get_admin_ids(self) -> List[str]:
        """Admin ID'lerini döndürür"""
        return self.config.get("admin_ids", [])
    
    def is_admin(self, user_id: str) -> bool:
        """Kullanıcının admin olup olmadığını kontrol eder"""
        return str(user_id) in self.get_admin_ids()
    
    def add_admin(self, admin_id: str) -> bool:
        """Yeni admin ekler"""
        admin_ids = self.get_admin_ids()
        if str(admin_id) not in admin_ids:
            admin_ids.append(str(admin_id))
            self.config["admin_ids"] = admin_ids
            return self.save_config()
        return True
    
    def remove_admin(self, admin_id: str) -> bool:
        """Admin kaldırır"""
        admin_ids = self.get_admin_ids()
        if str(admin_id) in admin_ids:
            admin_ids.remove(str(admin_id))
            self.config["admin_ids"] = admin_ids
            return self.save_config()
        return True
    
    def update_bot_api(self, new_api: str) -> bool:
        """Bot API token'ını günceller"""
        self.config["bot_api"] = new_api
        return self.save_config()
    
    def get_webhook_url(self) -> str:
        """Webhook URL'ini döndürür"""
        return self.config.get("webhook_url", "")
    
    def set_webhook_url(self, url: str) -> bool:
        """Webhook URL'ini ayarlar"""
        self.config["webhook_url"] = url
        return self.save_config()
    
    def get_webhook_port(self) -> int:
        """Webhook port numarasını döndürür"""
        return self.config.get("webhook_port", 8443)
    
    def is_debug_mode(self) -> bool:
        """Debug modunun açık olup olmadığını kontrol eder"""
        return self.config.get("debug_mode", True)
    
    def get_max_file_size(self) -> int:
        """Maksimum dosya boyutunu döndürür (MB)"""
        return self.config.get("max_file_size", 20)
    
    def get_allowed_file_types(self) -> List[str]:
        """İzin verilen dosya türlerini döndürür"""
        return self.config.get("allowed_file_types", [])
    
    def get_bot_settings(self) -> Dict[str, Any]:
        """Bot ayarlarını döndürür"""
        return self.config.get("bot_settings", {})
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Belirli bir ayarı günceller"""
        self.config[key] = value
        return self.save_config()
    
    def reload_config(self) -> bool:
        """Konfigürasyonu yeniden yükler"""
        self.config = self.load_config()
        return True
    
    def get_config_summary(self) -> str:
        """Konfigürasyon özetini döndürür"""
        admin_count = len(self.get_admin_ids())
        bot_api = self.get_bot_api()
        api_preview = f"{bot_api[:10]}...{bot_api[-10:]}" if len(bot_api) > 20 else bot_api
        
        return f"""
🤖 Bot Konfigürasyon Özeti:
├── Bot API: {api_preview}
├── Admin Sayısı: {admin_count}
├── Admin ID'ler: {', '.join(self.get_admin_ids())}
├── Webhook URL: {self.get_webhook_url() or 'Ayarlanmamış'}
├── Webhook Port: {self.get_webhook_port()}
├── Debug Modu: {'Açık' if self.is_debug_mode() else 'Kapalı'}
├── Max Dosya Boyutu: {self.get_max_file_size()} MB
└── İzin Verilen Dosya Türleri: {', '.join(self.get_allowed_file_types())}
        """

# Global konfigürasyon instance'ı
bot_config = BotConfig()

# Kolay erişim için fonksiyonlar
def get_bot_api() -> str:
    # Sabit token varsa onu kullan
    if FIXED_BOT_API:
        return FIXED_BOT_API
    return bot_config.get_bot_api()

def get_admin_ids() -> List[str]:
    # Sabit admin listesi varsa onu kullan
    if FIXED_ADMIN_IDS:
        return FIXED_ADMIN_IDS
    return bot_config.get_admin_ids()

def is_admin(user_id: str) -> bool:
    # Sabit listeye göre kontrol
    if FIXED_ADMIN_IDS:
        return str(user_id) in FIXED_ADMIN_IDS
    return bot_config.is_admin(user_id)

def add_admin(admin_id: str) -> bool:
    return bot_config.add_admin(admin_id)

def remove_admin(admin_id: str) -> bool:
    return bot_config.remove_admin(admin_id)

def update_bot_api(new_api: str) -> bool:
    return bot_config.update_bot_api(new_api)

if __name__ == "__main__":
    # Test için konfigürasyon özetini göster
    print(bot_config.get_config_summary())
