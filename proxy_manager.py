#!/usr/bin/env python3
"""
Proxy yönetim sınıfı
Proxy dosyasını okur ve hesaplara dağıtır
"""

import os
import random
import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from database import DatabaseManager

logger = logging.getLogger(__name__)

class ProxyManager:
    """Proxy yönetim sınıfı"""
    
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        self.db_manager = DatabaseManager()
        self.proxies = self.load_proxies()
    
    def load_proxies(self) -> List[Dict]:
        """Proxy dosyasını yükler"""
        proxies = []
        
        if not os.path.exists(self.proxy_file):
            logger.warning(f"Proxy dosyası bulunamadı: {self.proxy_file}")
            return proxies
        
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Boş satır ve yorum satırlarını atla
                    if not line or line.startswith('#'):
                        continue
                    
                    # Proxy formatını parse et
                    proxy_info = self.parse_proxy_line(line)
                    if proxy_info:
                        proxies.append(proxy_info)
                    else:
                        logger.warning(f"Geçersiz proxy formatı (satır {line_num}): {line}")
            
            logger.info(f"{len(proxies)} proxy yüklendi")
            return proxies
            
        except Exception as e:
            logger.error(f"Proxy dosyası yüklenemedi: {e}")
            return []
    
    def parse_proxy_line(self, line: str) -> Optional[Dict]:
        """Proxy satırını parse eder"""
        try:
            parts = line.split(':')
            
            if len(parts) < 2:
                return None
            
            proxy_info = {
                'host': parts[0].strip(),
                'port': int(parts[1].strip()),
                'username': None,
                'password': None,
                'type': 'http'  # Varsayılan tip
            }
            
            # Kullanıcı adı ve şifre varsa
            if len(parts) >= 4:
                proxy_info['username'] = parts[2].strip()
                proxy_info['password'] = parts[3].strip()
            
            # Proxy tipi belirtilmişse
            if len(parts) >= 5:
                proxy_info['type'] = parts[4].strip().lower()
            
            return proxy_info
            
        except (ValueError, IndexError) as e:
            logger.error(f"Proxy parse hatası: {e}")
            return None
    
    def get_proxy_string(self, proxy_info: Dict) -> str:
        """Proxy bilgisini string formatına çevirir"""
        if proxy_info['username'] and proxy_info['password']:
            return f"{proxy_info['username']}:{proxy_info['password']}@{proxy_info['host']}:{proxy_info['port']}"
        else:
            return f"{proxy_info['host']}:{proxy_info['port']}"
    
    def get_telethon_proxy(self, proxy_info: Dict) -> Dict:
        """Telethon için proxy formatına çevirir"""
        return {
            'proxy_type': proxy_info['type'],
            'addr': proxy_info['host'],
            'port': proxy_info['port'],
            'username': proxy_info['username'],
            'password': proxy_info['password']
        }
    
    def assign_proxies_to_accounts(self, session_files: List[str]) -> Dict[str, Dict]:
        """Proxy'leri hesaplara atar"""
        if not self.proxies:
            logger.warning("Proxy bulunamadı, proxy olmadan devam ediliyor")
            return {session_file: None for session_file in session_files}
        
        # Proxy'leri döngüsel olarak dağıt
        account_proxy_map = {}
        for i, session_file in enumerate(session_files):
            proxy_index = i % len(self.proxies)
            account_proxy_map[session_file] = self.proxies[proxy_index]
        
        # Veritabanına kaydet
        self.save_proxy_assignments(account_proxy_map)
        
        return account_proxy_map
    
    def save_proxy_assignments(self, account_proxy_map: Dict[str, Dict]) -> None:
        """Proxy atamalarını veritabanına kaydeder"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                for session_file, proxy_info in account_proxy_map.items():
                    if proxy_info:
                        cursor.execute('''
                            INSERT OR REPLACE INTO accounts 
                            (session_file, proxy_address, proxy_type, is_active)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            session_file,
                            self.get_proxy_string(proxy_info),
                            proxy_info['type'],
                            1
                        ))
                    else:
                        cursor.execute('''
                            INSERT OR REPLACE INTO accounts 
                            (session_file, proxy_address, proxy_type, is_active)
                            VALUES (?, ?, ?, ?)
                        ''', (session_file, None, 'http', 1))
                
                conn.commit()
                logger.info("Proxy atamaları veritabanına kaydedildi")
                
        except Exception as e:
            logger.error(f"Proxy atamaları kaydedilemedi: {e}")
    
    def get_account_proxy(self, session_file: str) -> Optional[Dict]:
        """Hesap için proxy bilgisini getirir"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT proxy_address, proxy_type 
                    FROM accounts 
                    WHERE session_file = ? AND is_active = 1
                ''', (session_file,))
                
                row = cursor.fetchone()
                if row and row[0]:
                    # Proxy string'ini parse et
                    proxy_string = row[0]
                    return self.parse_proxy_string(proxy_string, row[1])
                return None
                
        except Exception as e:
            logger.error(f"Hesap proxy bilgisi alınamadı: {e}")
            return None
    
    def parse_proxy_string(self, proxy_string: str, proxy_type: str = 'http') -> Dict:
        """Proxy string'ini parse eder"""
        try:
            if '@' in proxy_string:
                # Kullanıcı adı ve şifre var
                auth_part, host_part = proxy_string.split('@')
                username, password = auth_part.split(':')
                host, port = host_part.split(':')
            else:
                # Sadece host ve port
                host, port = proxy_string.split(':')
                username = password = None
            
            return {
                'host': host,
                'port': int(port),
                'username': username,
                'password': password,
                'type': proxy_type
            }
            
        except Exception as e:
            logger.error(f"Proxy string parse hatası: {e}")
            return None
    
    def test_proxy(self, proxy_info: Dict) -> bool:
        """Proxy'yi test eder"""
        try:
            import requests
            
            proxy_string = self.get_proxy_string(proxy_info)
            proxies = {
                'http': f"http://{proxy_string}",
                'https': f"http://{proxy_string}"
            }
            
            # Test isteği gönder
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Proxy test hatası: {e}")
            return False
    
    def get_random_proxy(self) -> Optional[Dict]:
        """Random proxy döndürür"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def get_proxy_count(self) -> int:
        """Toplam proxy sayısını döndürür"""
        return len(self.proxies)
    
    def reload_proxies(self) -> int:
        """Proxy'leri yeniden yükler"""
        self.proxies = self.load_proxies()
        return len(self.proxies)

# Global proxy manager instance'ı
proxy_manager = ProxyManager()

if __name__ == "__main__":
    # Test
    pm = ProxyManager()
    print(f"✅ {pm.get_proxy_count()} proxy yüklendi")
    
    # Test proxy ataması
    test_sessions = ["user1.session", "user2.session", "user3.session"]
    assignments = pm.assign_proxies_to_accounts(test_sessions)
    
    for session, proxy in assignments.items():
        print(f"Session: {session} -> Proxy: {proxy}")
