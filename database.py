#!/usr/bin/env python3
"""
Veritabanı yönetim sınıfı
SQLite veritabanı ile kanal, istek havuzu ve hesap yönetimi
"""

import sqlite3
import os
import logging
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Veritabanı yönetim sınıfı"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        if not self.db_path:
            # Konteyner içinde kalıcı klasör
            data_dir = os.path.join(os.getcwd(), 'data')
            # /app çalışırken bu /app/data olacaktır
            if not os.path.isdir(data_dir):
                try:
                    os.makedirs(data_dir, exist_ok=True)
                except Exception:
                    pass
            self.db_path = os.path.join(data_dir, 'telegram_bot.db')
        self.init_database()
    
    def init_database(self) -> None:
        """Veritabanını başlatır ve tabloları oluşturur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Kanal tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_link TEXT NOT NULL,
                        total_requests INTEGER NOT NULL,
                        duration_minutes INTEGER NOT NULL,
                        allow_repeat BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        user_id TEXT NOT NULL,
                        UNIQUE(channel_link, user_id)
                    )
                ''')
                
                # Mevcut tablolara eksik sütunları ekle
                self.add_missing_columns()
                
                # İstek havuzu tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS request_pool (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id INTEGER NOT NULL,
                        account_name TEXT NOT NULL,
                        scheduled_time TIMESTAMP NOT NULL,
                        status TEXT DEFAULT 'Bekliyor',
                        proxy_address TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channels (id)
                    )
                ''')
                
                # Hesap-Proxy ilişki tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_file TEXT NOT NULL UNIQUE,
                        proxy_address TEXT,
                        proxy_type TEXT DEFAULT 'http',
                        is_active BOOLEAN DEFAULT 1,
                        last_used TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Kullanıcı durumu tablosu (form doldurma süreci için)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_states (
                        user_id TEXT PRIMARY KEY,
                        current_state TEXT,
                        temp_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Hesap-Kanal istek geçmişi tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS account_channel_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_name TEXT NOT NULL,
                        channel_link TEXT NOT NULL,
                        request_count INTEGER DEFAULT 1,
                        last_request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(account_name, channel_link)
                    )
                ''')
                
                # Admin yönetimi tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL UNIQUE,
                        username TEXT,
                        first_name TEXT,
                        added_by TEXT,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                conn.commit()
                logger.info("Veritabanı tabloları başarıyla oluşturuldu")
                
        except Exception as e:
            logger.error(f"Veritabanı başlatılamadı: {e}")
            raise
    
    def add_missing_columns(self) -> None:
        """Mevcut tablolara eksik sütunları ekler"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # channels tablosuna allow_repeat sütunu ekle
                try:
                    cursor.execute('ALTER TABLE channels ADD COLUMN allow_repeat BOOLEAN DEFAULT 1')
                    logger.info("allow_repeat sütunu eklendi")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.info("allow_repeat sütunu zaten mevcut")
                    else:
                        logger.warning(f"allow_repeat sütunu eklenemedi: {e}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Eksik sütunlar eklenemedi: {e}")
    
    def purge_account(self, account_name: str) -> None:
        """Hesabı ve ilgili planlanan istekleri veritabanından temizler"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # request_pool'dan sil
                cursor.execute(
                    "DELETE FROM request_pool WHERE account_name = ?",
                    (account_name,)
                )
                
                # accounts tablosundan sil (kolon adı session_file)
                cursor.execute(
                    "DELETE FROM accounts WHERE session_file = ?",
                    (account_name,)
                )
                
                # İsteğe bağlı: geçmiş tablosundan da kaldır
                try:
                    cursor.execute(
                        "DELETE FROM account_channel_requests WHERE account_name = ?",
                        (account_name,)
                    )
                except Exception:
                    # Tablo olmayabilir; sessiz geç
                    pass
                
                conn.commit()
                logger.info(f"Hesap temizlendi: {account_name}")
        except Exception as e:
            logger.error(f"Hesap temizlenemedi ({account_name}): {e}")
    
    def add_admin(self, user_id: str, username: str = None, first_name: str = None, added_by: str = None) -> bool:
        """Yeni admin ekler"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO admins 
                    (user_id, username, first_name, added_by, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (user_id, username, first_name, added_by))
                
                conn.commit()
                logger.info(f"Admin eklendi: {user_id} ({first_name})")
                return True
                
        except Exception as e:
            logger.error(f"Admin eklenirken hata: {e}")
            return False
    
    def remove_admin(self, user_id: str) -> bool:
        """Admin'i kaldırır"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('UPDATE admins SET is_active = 0 WHERE user_id = ?', (user_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Admin kaldırıldı: {user_id}")
                    return True
                else:
                    logger.warning(f"Admin bulunamadı: {user_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Admin kaldırılırken hata: {e}")
            return False
    
    def get_all_admins(self) -> List[Dict]:
        """Tüm aktif adminleri döndürür"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT user_id, username, first_name, added_by, added_at
                    FROM admins 
                    WHERE is_active = 1
                    ORDER BY added_at ASC
                ''')
                
                admins = []
                for row in cursor.fetchall():
                    admins.append({
                        'user_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'added_by': row[3],
                        'added_at': row[4]
                    })
                
                return admins
                
        except Exception as e:
            logger.error(f"Adminler alınırken hata: {e}")
            return []
    
    def is_admin_db(self, user_id: str) -> bool:
        """Kullanıcının admin olup olmadığını kontrol eder (veritabanından)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM admins 
                    WHERE user_id = ? AND is_active = 1
                ''', (user_id,))
                
                return cursor.fetchone()[0] > 0
                
        except Exception as e:
            logger.error(f"Admin kontrolü hatası: {e}")
            return False
    
    def add_channel(self, channel_link: str, total_requests: int, duration_minutes: int, user_id: str, allow_repeat: bool = True) -> int:
        """Yeni kanal ekler veya mevcut kanalı günceller"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Önce kanalın var olup olmadığını kontrol et
                cursor.execute('''
                    SELECT id FROM channels 
                    WHERE channel_link = ? AND user_id = ?
                ''', (channel_link, user_id))
                
                existing_channel = cursor.fetchone()
                
                if existing_channel:
                    # Kanal mevcut, güncelle
                    channel_id = existing_channel[0]
                    cursor.execute('''
                        UPDATE channels 
                        SET total_requests = ?, duration_minutes = ?, allow_repeat = ?, status = 'active', created_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (total_requests, duration_minutes, allow_repeat, channel_id))
                    
                    # Eski istekleri temizle
                    cursor.execute('DELETE FROM request_pool WHERE channel_id = ?', (channel_id,))
                    
                    conn.commit()
                    logger.info(f"Kanal güncellendi: {channel_link} (ID: {channel_id})")
                    return channel_id
                else:
                    # Yeni kanal ekle
                    cursor.execute('''
                        INSERT INTO channels (channel_link, total_requests, duration_minutes, allow_repeat, user_id)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (channel_link, total_requests, duration_minutes, allow_repeat, user_id))
                    
                    channel_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f"Kanal eklendi: {channel_link} (ID: {channel_id})")
                    return channel_id
                
        except Exception as e:
            logger.error(f"Kanal eklenemedi: {e}")
            return None
    
    def get_channel(self, channel_id: int) -> Optional[Dict]:
        """Kanal bilgilerini getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM channels WHERE id = ?', (channel_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'channel_link': row[1],
                        'total_requests': row[2],
                        'duration_minutes': row[3],
                        'allow_repeat': row[4],
                        'created_at': row[5],
                        'status': row[6],
                        'user_id': row[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Kanal bilgisi alınamadı: {e}")
            return None
    
    def get_user_channels(self, user_id: str) -> List[Dict]:
        """Kullanıcının kanallarını getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM channels 
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                rows = cursor.fetchall()
                channels = []
                for row in rows:
                    channels.append({
                        'id': row[0],
                        'channel_link': row[1],
                        'total_requests': row[2],
                        'duration_minutes': row[3],
                        'allow_repeat': row[4],
                        'created_at': row[5],
                        'status': row[6],
                        'user_id': row[7]
                    })
                return channels
                
        except Exception as e:
            logger.error(f"Kullanıcı kanalları alınamadı: {e}")
            return []
    
    def create_request_pool(self, channel_id: int, session_files: List[str], proxies: List[str]) -> bool:
        """İstek havuzunu oluşturur"""
        try:
            channel = self.get_channel(channel_id)
            if not channel:
                return False
            
            # Kullanılabilir hesapları al
            available_accounts = self.get_available_accounts_for_channel(
                channel['channel_link'], 
                channel.get('allow_repeat', True), 
                session_files
            )
            
            if not available_accounts:
                logger.warning(f"Kanal için kullanılabilir hesap bulunamadı: {channel['channel_link']}")
                return False
            
            # İstek sayısını toplam hesap sayısı ile sınırla
            max_requests = len(available_accounts)
            actual_requests = min(channel['total_requests'], max_requests)
            
            if actual_requests < channel['total_requests']:
                logger.warning(f"İstek sayısı sınırlandırıldı: {channel['total_requests']} -> {actual_requests} (Toplam hesap sayısı: {max_requests})")
            
            # Proxy dağıtımı
            account_proxy_map = self.distribute_proxies(available_accounts, proxies)
            
            # Global istek sıralama sistemi
            start_time = self.get_next_available_time()
            min_interval = 5  # Minimum 5 saniye aralık
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Mevcut istekleri temizle
                cursor.execute('DELETE FROM request_pool WHERE channel_id = ?', (channel_id,))
                
                # Yeni istekleri sıralı olarak oluştur
                for i in range(actual_requests):
                    # Her istek arasında minimum 5 saniye fark
                    scheduled_time = start_time + timedelta(seconds=i * min_interval)
                    
                    # Random hesap seç (sadece kullanılabilir hesaplardan)
                    account_name = random.choice(available_accounts)
                    proxy_address = account_proxy_map.get(account_name, "")
                    
                    cursor.execute('''
                        INSERT INTO request_pool 
                        (channel_id, account_name, scheduled_time, proxy_address, status)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (channel_id, account_name, scheduled_time, proxy_address, 'Bekliyor'))
                
                conn.commit()
                logger.info(f"İstek havuzu oluşturuldu: {actual_requests} istek (sıralı, sınırlandırılmış)")
                return True
                
        except Exception as e:
            logger.error(f"İstek havuzu oluşturulamadı: {e}")
            return False
    
    def get_next_available_time(self) -> datetime:
        """Son istekten sonraki uygun zamanı döndürür"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # En son planlanan isteği bul
                cursor.execute('''
                    SELECT MAX(scheduled_time) FROM request_pool 
                    WHERE status = 'Bekliyor'
                ''')
                
                result = cursor.fetchone()
                if result and result[0]:
                    # Son istekten 5 saniye sonra
                    last_time = datetime.fromisoformat(result[0])
                    return last_time + timedelta(seconds=5)
                else:
                    # İlk istek, şimdi başla
                    return datetime.now()
                    
        except Exception as e:
            logger.error(f"Son istek zamanı alınamadı: {e}")
            return datetime.now()
    
    def distribute_proxies(self, session_files: List[str], proxies: List[str]) -> Dict[str, str]:
        """Proxy'leri hesaplara dağıtır"""
        account_proxy_map = {}
        
        if not proxies:
            return account_proxy_map
        
        # Proxy'leri döngüsel olarak dağıt
        for i, session_file in enumerate(session_files):
            proxy_index = i % len(proxies)
            account_proxy_map[session_file] = proxies[proxy_index]
        
        return account_proxy_map
    
    def get_pending_requests(self, limit: int = 10) -> List[Dict]:
        """Bekleyen istekleri getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT rp.*, c.channel_link 
                    FROM request_pool rp
                    JOIN channels c ON rp.channel_id = c.id
                    WHERE rp.status = 'Bekliyor' 
                    AND rp.scheduled_time <= ?
                    ORDER BY rp.scheduled_time ASC
                    LIMIT ?
                ''', (datetime.now(), limit))
                
                rows = cursor.fetchall()
                requests = []
                for row in rows:
                    requests.append({
                        'id': row[0],
                        'channel_id': row[1],
                        'account_name': row[2],
                        'scheduled_time': row[3],
                        'status': row[4],
                        'proxy_address': row[5],
                        'created_at': row[6],
                        'channel_link': row[7]
                    })
                return requests
                
        except Exception as e:
            logger.error(f"Bekleyen istekler alınamadı: {e}")
            return []
    
    def update_request_status(self, request_id: int, status: str) -> bool:
        """İstek durumunu günceller"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE request_pool 
                    SET status = ? 
                    WHERE id = ?
                ''', (status, request_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"İstek durumu güncellenemedi: {e}")
            return False
    
    def set_user_state(self, user_id: str, state: str, temp_data: Dict = None) -> bool:
        """Kullanıcı durumunu ayarlar"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                temp_data_json = json.dumps(temp_data) if temp_data else None
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_states 
                    (user_id, current_state, temp_data, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, state, temp_data_json))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Kullanıcı durumu ayarlanamadı: {e}")
            return False
    
    def get_user_state(self, user_id: str) -> Tuple[str, Dict]:
        """Kullanıcı durumunu getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT current_state, temp_data 
                    FROM user_states 
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    state = row[0]
                    temp_data = json.loads(row[1]) if row[1] else {}
                    return state, temp_data
                return None, {}
                
        except Exception as e:
            logger.error(f"Kullanıcı durumu alınamadı: {e}")
            return None, {}
    
    def clear_user_state(self, user_id: str) -> bool:
        """Kullanıcı durumunu temizler"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_states WHERE user_id = ?', (user_id,))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Kullanıcı durumu temizlenemedi: {e}")
            return False
    
    def get_request_stats(self, channel_id: int) -> Dict:
        """İstek istatistiklerini getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT status, COUNT(*) 
                    FROM request_pool 
                    WHERE channel_id = ?
                    GROUP BY status
                ''', (channel_id,))
                
                stats = {'Bekliyor': 0, 'Gönderildi': 0, 'Atlandı': 0}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                return stats
                
        except Exception as e:
            logger.error(f"İstek istatistikleri alınamadı: {e}")
            return {'Bekliyor': 0, 'Gönderildi': 0, 'Atlandı': 0}
    
    def get_planned_requests(self, channel_id: int, limit: int = 10) -> List[Dict]:
        """Kanal için planlanan istekleri döndürür"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, account_name, scheduled_time, status
                    FROM request_pool 
                    WHERE channel_id = ? AND status = 'Bekliyor'
                    ORDER BY scheduled_time ASC
                    LIMIT ?
                ''', (channel_id, limit))
                
                requests = []
                for row in cursor.fetchall():
                    request_id, account_name, scheduled_time, status = row
                    # Session dosya adından telefon numarasını çıkar
                    phone_number = account_name.replace('.session', '')
                    requests.append({
                        'id': request_id,
                        'account_name': account_name,
                        'phone_number': phone_number,
                        'scheduled_time': scheduled_time,
                        'status': status
                    })
                
                return requests
                
        except Exception as e:
            logger.error(f"Planlanan istekler alınamadı: {e}")
            return []
    
    def get_global_planned_requests(self, limit: int = 30) -> List[Dict]:
        """Tüm kanallar için planlanan istekleri döndürür"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT rp.id, rp.account_name, rp.scheduled_time, rp.status, c.channel_link
                    FROM request_pool rp
                    JOIN channels c ON rp.channel_id = c.id
                    WHERE rp.status = 'Bekliyor'
                    ORDER BY rp.scheduled_time ASC
                    LIMIT ?
                ''', (limit,))
                
                requests = []
                for row in cursor.fetchall():
                    request_id, account_name, scheduled_time, status, channel_link = row
                    # Session dosya adından telefon numarasını çıkar
                    phone_number = account_name.replace('.session', '')
                    requests.append({
                        'id': request_id,
                        'account_name': account_name,
                        'phone_number': phone_number,
                        'scheduled_time': scheduled_time,
                        'status': status,
                        'channel_link': channel_link
                    })
                
                return requests
                
        except Exception as e:
            logger.error(f"Global planlanan istekler alınamadı: {e}")
            return []
    
    def record_account_channel_request(self, account_name: str, channel_link: str) -> None:
        """Hesap-kanal istek geçmişini kaydeder"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO account_channel_requests 
                    (account_name, channel_link, request_count, last_request_time)
                    VALUES (?, ?, 
                        COALESCE((SELECT request_count + 1 FROM account_channel_requests 
                                 WHERE account_name = ? AND channel_link = ?), 1),
                        CURRENT_TIMESTAMP)
                ''', (account_name, channel_link, account_name, channel_link))
                
                conn.commit()
                logger.info(f"Hesap-kanal istek geçmişi kaydedildi: {account_name} -> {channel_link}")
                
        except Exception as e:
            logger.error(f"Hesap-kanal istek geçmişi kaydedilemedi: {e}")
    
    def get_account_channel_requests(self, account_name: str, channel_link: str) -> bool:
        """Hesabın daha önce bu kanala istek atıp atmadığını kontrol eder"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM account_channel_requests 
                    WHERE account_name = ? AND channel_link = ?
                ''', (account_name, channel_link))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"Hesap-kanal istek geçmişi kontrol edilemedi: {e}")
            return False
    
    def get_available_accounts_for_channel(self, channel_link: str, allow_repeat: bool, session_files: List[str]) -> List[str]:
        """Kanal için kullanılabilir hesapları döndürür"""
        try:
            if allow_repeat:
                # Tekrar isteklere izin veriliyorsa tüm hesapları döndür
                return session_files
            
            # Tekrar isteklere izin verilmiyorsa, daha önce istek atmamış hesapları döndür
            available_accounts = []
            for session_file in session_files:
                account_name = session_file.replace('.session', '')
                if not self.get_account_channel_requests(account_name, channel_link):
                    available_accounts.append(session_file)
            
            return available_accounts
            
        except Exception as e:
            logger.error(f"Kullanılabilir hesaplar alınamadı: {e}")
            return session_files

# Global veritabanı instance'ı
db_manager = DatabaseManager()

if __name__ == "__main__":
    # Test
    db = DatabaseManager()
    print("✅ Veritabanı başarıyla oluşturuldu")
    
    # Test kanal ekleme
    channel_id = db.add_channel("https://t.me/test_channel", 10, 60, "123456789")
    print(f"Test kanalı eklendi: {channel_id}")
    
    # Test istatistikler
    stats = db.get_request_stats(channel_id)
    print(f"İstek istatistikleri: {stats}")
