#!/usr/bin/env python3
"""
Telethon Client yönetim sınıfı
Session dosyaları ile Telegram hesaplarına bağlanır ve kanal katılım istekleri gönderir
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError, ChannelPrivateError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from database import db_manager
from proxy_manager import proxy_manager

logger = logging.getLogger(__name__)

class TelethonManager:
    """Telethon client yönetim sınıfı"""
    
    def __init__(self, api_id: str = None, api_hash: str = None):
        self.api_id = api_id or 2040  # Global API ID
        self.api_hash = api_hash or "b18441a1ff607e10a989891a5462e627"  # Global API Hash
        self.clients = {}  # session_file -> client mapping
        self.sessions_dir = "Sessions"
        
    async def create_client(self, session_file: str, proxy_info: Dict = None) -> Optional[TelegramClient]:
        """Session dosyası için client oluşturur"""
        try:
            session_path = os.path.join(self.sessions_dir, session_file)
            
            if not os.path.exists(session_path):
                logger.error(f"Session dosyası bulunamadı: {session_path}")
                return None
            
            # Proxy ayarları
            proxy = None
            if proxy_info:
                proxy = proxy_manager.get_telethon_proxy(proxy_info)
            
            # Client oluştur
            client = TelegramClient(
                session_path,
                self.api_id,
                self.api_hash,
                proxy=proxy
            )
            
            # Bağlantıyı test et
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.warning(f"Session yetkilendirilmemiş: {session_file}")
                await client.disconnect()
                return None
            
            logger.info(f"Client oluşturuldu: {session_file}")
            return client
            
        except Exception as e:
            logger.error(f"Client oluşturulamadı ({session_file}): {e}")
            return None
    
    async def join_channel(self, client: TelegramClient, channel_link: str) -> Tuple[bool, str]:
        """Kanala katılım isteği gönderir"""
        try:
            # Link formatını düzenle
            if channel_link.startswith('@'):
                channel_link = channel_link[1:]
            elif not channel_link.startswith('https://t.me/'):
                channel_link = f"https://t.me/{channel_link}"
            
            # Kanal linkini parse et
            if 't.me/' in channel_link:
                channel_identifier = channel_link.split('t.me/')[-1]
            else:
                return False, "Geçersiz kanal linki"
            
            # Katılım isteği gönder
            try:
                # Gizli kanal linki kontrolü (+ ile başlıyorsa)
                if channel_identifier.startswith('+'):
                    # Gizli kanal için ImportChatInviteRequest kullan
                    invite_hash = channel_identifier[1:]  # + işaretini kaldır
                    logger.info(f"🔗 Gizli kanala katılım isteği gönderiliyor: {channel_link} (Hash: {invite_hash})")
                    await client(ImportChatInviteRequest(invite_hash))
                    logger.info(f"✅ Gizli kanala katılım isteği başarılı: {channel_link}")
                    return True, "Gizli kanala katılım isteği gönderildi"
                else:
                    # Normal kanal için JoinChannelRequest kullan
                    logger.info(f"🔗 Normal kanala katılım isteği gönderiliyor: {channel_link} (Username: {channel_identifier})")
                    await client(JoinChannelRequest(channel_identifier))
                    logger.info(f"✅ Normal kanala katılım isteği başarılı: {channel_link}")
                    return True, "Kanal katılım isteği gönderildi"
                
            except ChannelPrivateError:
                logger.warning(f"❌ Kanal özel veya erişim yok: {channel_link}")
                return False, "Kanal özel veya erişim yok"
            except FloodWaitError as e:
                logger.warning(f"⏳ Rate limit: {e.seconds} saniye bekle - {channel_link}")
                return False, f"Rate limit: {e.seconds} saniye bekle"
            except Exception as e:
                error_msg = str(e)
                # "You have successfully requested" mesajı aslında başarılı
                if "You have successfully requested" in error_msg:
                    logger.info(f"✅ Kanal katılım isteği başarılı ({channel_link}): {error_msg}")
                    return True, "Başarılı"
                else:
                    logger.error(f"❌ Kanal katılım hatası ({channel_link}): {error_msg}")
                    return False, f"Hata: {error_msg}"
                
        except Exception as e:
            logger.error(f"Kanal katılım hatası: {e}")
            return False, f"Bağlantı hatası: {str(e)}"
    
    async def process_request(self, request_data: Dict) -> bool:
        """Tek bir isteği işler"""
        request_id = request_data['id']
        account_name = request_data['account_name']
        channel_link = request_data['channel_link']
        proxy_address = request_data.get('proxy_address')
        
        logger.info(f"🚀 İstek işleniyor: ID={request_id}, Hesap={account_name}, Kanal={channel_link}")
        
        try:
            # Client'ı al veya oluştur
            client = self.clients.get(account_name)
            if not client:
                logger.info(f"📱 Yeni client oluşturuluyor: {account_name}")
                
                # Proxy bilgisini al
                proxy_info = None
                if proxy_address:
                    proxy_info = proxy_manager.parse_proxy_string(proxy_address)
                    logger.info(f"🌐 Proxy kullanılıyor: {proxy_address}")
                
                # Yeni client oluştur
                client = await self.create_client(account_name, proxy_info)
                if not client:
                    logger.warning(f"⚠️ İlk proxy başarısız, alternatif deneniyor: {account_name}")
                    # Proxy başarısız, alternatif proxy dene
                    proxy_info = proxy_manager.get_random_proxy()
                    if proxy_info:
                        logger.info(f"🔄 Alternatif proxy deneniyor: {proxy_manager.get_proxy_string(proxy_info)}")
                        client = await self.create_client(account_name, proxy_info)
                
                if not client:
                    logger.error(f"❌ Client oluşturulamadı: {account_name}")
                    db_manager.update_request_status(request_id, "Atlandı")
                    return False
                else:
                    logger.info(f"✅ Client başarıyla oluşturuldu: {account_name}")
                    self.clients[account_name] = client
            else:
                logger.info(f"♻️ Mevcut client kullanılıyor: {account_name}")
            
            # Kanala katılım isteği gönder
            logger.info(f"📤 Katılım isteği gönderiliyor: {account_name} -> {channel_link}")
            success, message = await self.join_channel(client, channel_link)
            
            if success:
                db_manager.update_request_status(request_id, "Gönderildi")
                # İstek geçmişini kaydet
                db_manager.record_account_channel_request(account_name, channel_link)
                logger.info(f"✅ İstek başarılı: {account_name} -> {channel_link}")
                return True
            else:
                # FROZEN hesabı tespit et ve temizle
                error_text = str(message or "")
                if "FROZEN" in error_text or "FROZEN_METHOD_INVALID" in error_text:
                    logger.error(f"🧊 Hesap frozen tespit edildi: {account_name}")
                    try:
                        # Client bağlantısını kesin
                        try:
                            await client.disconnect()
                        except Exception:
                            pass
                        # Haritada da kapat
                        if account_name in self.clients:
                            del self.clients[account_name]
                        
                        # Session dosyasını Frozens klasörüne taşı
                        sessions_root = self.sessions_dir
                        frozens_dir = os.path.join(sessions_root, "Frozens")
                        os.makedirs(frozens_dir, exist_ok=True)
                        src_path = os.path.join(sessions_root, account_name)
                        dst_path = os.path.join(frozens_dir, account_name)
                        try:
                            # Windows'ta kilidi kaldırmak için yeniden adlandırmayı zorla
                            if os.path.exists(dst_path):
                                os.remove(dst_path)
                        except Exception:
                            pass
                        try:
                            os.replace(src_path, dst_path)
                            logger.info(f"📁 Session taşındı -> {dst_path}")
                        except Exception as move_err:
                            logger.error(f"Session taşınamadı ({account_name}): {move_err}")
                        
                        # Veritabanını temizle
                        db_manager.purge_account(account_name)
                    except Exception as clean_err:
                        logger.error(f"Frozen hesap temizleme hatası ({account_name}): {clean_err}")
                
                db_manager.update_request_status(request_id, "Atlandı")
                logger.warning(f"❌ İstek başarısız: {account_name} -> {channel_link} ({message})")
                return False
                
        except Exception as e:
            logger.error(f"💥 İstek işlenirken hata ({account_name} -> {channel_link}): {e}")
            db_manager.update_request_status(request_id, "Atlandı")
            return False
    
    async def process_pending_requests(self, limit: int = 1) -> int:
        """Bekleyen istekleri işler (sıralı olarak)"""
        try:
            # Bekleyen istekleri al (sadece 1 tane)
            requests = db_manager.get_pending_requests(limit)
            
            if not requests:
                logger.debug("📭 Bekleyen istek bulunamadı")
                return 0
            
            logger.info(f"📋 {len(requests)} bekleyen istek işlenecek (sıralı)")
            
            # İstekleri sıralı olarak işle (paralel değil)
            successful = 0
            for request in requests:
                logger.info(f"📝 İstek işleniyor: {request['account_name']} -> {request['channel_link']} (Zaman: {request['scheduled_time']})")
                
                # İstek zamanını kontrol et
                scheduled_time = datetime.fromisoformat(request['scheduled_time'])
                now = datetime.now()
                
                if scheduled_time > now:
                    # Henüz zamanı gelmemiş, bekle
                    wait_seconds = (scheduled_time - now).total_seconds()
                    logger.info(f"⏳ İstek zamanı bekleniyor: {wait_seconds:.1f} saniye")
                    await asyncio.sleep(wait_seconds)
                
                # İsteği işle
                result = await self.process_request(request)
                if result:
                    successful += 1
                
                # Her istekten sonra minimum 5 saniye bekle
                logger.info("⏳ Minimum 5 saniye bekleme...")
                await asyncio.sleep(5)
            
            logger.info(f"📊 İstek sonuçları: {successful} başarılı, {len(requests) - successful} başarısız")
            return successful
            
        except Exception as e:
            logger.error(f"💥 İstek işleme genel hatası: {e}")
            return 0
    
    async def cleanup_clients(self):
        """Kullanılmayan client'ları temizler"""
        try:
            for session_file, client in list(self.clients.items()):
                try:
                    await client.disconnect()
                    del self.clients[session_file]
                    logger.info(f"Client temizlendi: {session_file}")
                except Exception as e:
                    logger.error(f"Client temizleme hatası ({session_file}): {e}")
                    
        except Exception as e:
            logger.error(f"Client temizleme genel hatası: {e}")
    
    async def test_session(self, session_file: str) -> Tuple[bool, str]:
        """Session dosyasını test eder"""
        try:
            client = await self.create_client(session_file)
            if not client:
                return False, "Client oluşturulamadı"
            
            # Kullanıcı bilgilerini al
            me = await client.get_me()
            if me:
                await client.disconnect()
                return True, f"Kullanıcı: {me.first_name} (@{me.username or 'N/A'})"
            else:
                await client.disconnect()
                return False, "Kullanıcı bilgisi alınamadı"
                
        except Exception as e:
            logger.error(f"Session test hatası ({session_file}): {e}")
            return False, f"Hata: {str(e)}"
    
    async def get_session_info(self, session_file: str) -> Optional[Dict]:
        """Session bilgilerini getirir"""
        try:
            client = await self.create_client(session_file)
            if not client:
                return None
            
            me = await client.get_me()
            if me:
                await client.disconnect()
                return {
                    'id': me.id,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'username': me.username,
                    'phone': me.phone
                }
            else:
                await client.disconnect()
                return None
                
        except Exception as e:
            logger.error(f"Session bilgi hatası ({session_file}): {e}")
            return None
    
    def get_active_clients_count(self) -> int:
        """Aktif client sayısını döndürür"""
        return len(self.clients)
    
    async def close_all_clients(self):
        """Tüm client'ları kapatır"""
        await self.cleanup_clients()

# Global telethon manager instance'ı
telethon_manager = TelethonManager()

if __name__ == "__main__":
    # Test
    async def test():
        tm = TelethonManager()
        
        # Session dosyalarını test et
        session_files = ["user1.session", "user2.session"]
        for session_file in session_files:
            success, message = await tm.test_session(session_file)
            print(f"Session {session_file}: {success} - {message}")
        
        await tm.close_all_clients()
    
    # Global instance
    telethon_manager = TelethonManager(api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627")
    
    if __name__ == "__main__":
        asyncio.run(test())
