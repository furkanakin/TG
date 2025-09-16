#!/usr/bin/env python3
"""
Telegram Bot Ana Uygulaması
Sessions klasöründeki .session dosyalarını sayar ve kullanıcıya gösterir
"""

import os
import glob
import zipfile
import tempfile
import sqlite3
import logging
from typing import List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import get_bot_api, get_admin_ids, is_admin
from database import db_manager
from proxy_manager import proxy_manager

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# HTTP isteklerini azalt
logging.getLogger("httpx").setLevel(logging.WARNING)

class SessionManager:
    """Session dosyalarını yöneten sınıf"""
    
    def __init__(self, sessions_dir: str = "Sessions"):
        self.sessions_dir = sessions_dir
        self.ensure_sessions_dir()
    
    def ensure_sessions_dir(self) -> None:
        """Sessions klasörünün var olduğundan emin olur"""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
            logger.info(f"Sessions klasörü oluşturuldu: {self.sessions_dir}")
    
    def count_session_files(self) -> int:
        """Sessions klasöründeki .session dosyalarının sayısını döndürür"""
        try:
            # .session uzantılı dosyaları bul
            pattern = os.path.join(self.sessions_dir, "*.session")
            session_files = glob.glob(pattern)
            count = len(session_files)
            
            logger.info(f"Sessions klasöründe {count} adet .session dosyası bulundu")
            return count
            
        except Exception as e:
            logger.error(f"Session dosyaları sayılırken hata: {e}")
            return 0
    
    def get_session_files(self) -> List[str]:
        """Sessions klasöründeki .session dosyalarının listesini döndürür"""
        try:
            pattern = os.path.join(self.sessions_dir, "*.session")
            session_files = glob.glob(pattern)
            # Frozens alt klasöründekileri dışla
            frozens_dir = os.path.join(self.sessions_dir, "Frozens")
            if os.path.isdir(frozens_dir):
                frozen_names = set(os.listdir(frozens_dir))
                session_files = [p for p in session_files if os.path.basename(p) not in frozen_names]
            
            # Sadece dosya adlarını döndür (tam yol değil)
            file_names = [os.path.basename(f) for f in session_files]
            return file_names
            
        except Exception as e:
            logger.error(f"Session dosyaları listelenirken hata: {e}")
            return []
    
    def get_session_info(self) -> dict:
        """Session dosyaları hakkında detaylı bilgi döndürür"""
        try:
            session_files = self.get_session_files()
            total_count = len(session_files)
            
            # Dosya boyutlarını hesapla
            total_size = 0
            for file_name in session_files:
                file_path = os.path.join(self.sessions_dir, file_name)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            
            # Boyutu MB'ye çevir
            size_mb = total_size / (1024 * 1024)
            
            return {
                "total_count": total_count,
                "total_size_mb": round(size_mb, 2),
                "files": session_files
            }
            
        except Exception as e:
            logger.error(f"Session bilgileri alınırken hata: {e}")
            return {
                "total_count": 0,
                "total_size_mb": 0,
                "files": []
            }
    
    def get_frozen_count(self) -> int:
        """Frozen hesap sayısını döndürür"""
        try:
            frozens_dir = os.path.join(self.sessions_dir, "Frozens")
            if not os.path.exists(frozens_dir):
                return 0
            
            pattern = os.path.join(frozens_dir, "*.session")
            frozen_files = glob.glob(pattern)
            return len(frozen_files)
            
        except Exception as e:
            logger.error(f"Frozen hesap sayısı alınırken hata: {e}")
            return 0
    
    def get_frozen_files(self) -> List[str]:
        """Frozen dosyaların listesini döndürür"""
        try:
            frozens_dir = os.path.join(self.sessions_dir, "Frozens")
            if not os.path.exists(frozens_dir):
                return []
            
            pattern = os.path.join(frozens_dir, "*.session")
            frozen_files = glob.glob(pattern)
            
            # Sadece dosya adlarını döndür
            file_names = [os.path.basename(f) for f in frozen_files]
            return file_names
            
        except Exception as e:
            logger.error(f"Frozen dosyalar alınırken hata: {e}")
            return []
    
    def get_frozen_info(self) -> dict:
        """Frozen dosyalar hakkında detaylı bilgi döndürür"""
        try:
            frozens_dir = os.path.join(self.sessions_dir, "Frozens")
            if not os.path.exists(frozens_dir):
                return {
                    'total_count': 0,
                    'total_size_mb': 0,
                    'files': []
                }
            
            frozen_files = self.get_frozen_files()
            total_count = len(frozen_files)
            
            # Dosya boyutlarını hesapla
            total_size = 0
            for file_name in frozen_files:
                file_path = os.path.join(frozens_dir, file_name)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            
            # Boyutu MB'ye çevir
            size_mb = total_size / (1024 * 1024)
            
            return {
                "total_count": total_count,
                "total_size_mb": round(size_mb, 2),
                "files": frozen_files
            }
            
        except Exception as e:
            logger.error(f"Frozen bilgileri alınırken hata: {e}")
            return {
                "total_count": 0,
                "total_size_mb": 0,
                "files": []
            }

    def _sanitize_filename(self, file_name: str) -> str:
        """Gelen dosya adını güvenli bir ada dönüştürür (.session uzantısını korur)."""
        base = os.path.basename(file_name)
        # uzantı kontrolü
        if not base.endswith('.session'):
            base = f"{base}.session" if '.session' not in base else base
        # izin verilmeyen karakterleri temizle
        safe = ''.join(ch for ch in base if ch.isalnum() or ch in ('-', '_', '.', '+'))
        if not safe.endswith('.session'):
            safe += '.session'
        return safe

    def save_session_bytes(self, file_name: str, file_bytes: bytes) -> str:
        """Verilen içerikle Sessions klasörüne .session kaydeder ve dosya adını döndürür."""
        self.ensure_sessions_dir()
        safe_name = self._sanitize_filename(file_name)
        target_path = os.path.join(self.sessions_dir, safe_name)
        # Aynı isim varsa benzersizleştir
        if os.path.exists(target_path):
            name, ext = os.path.splitext(safe_name)
            i = 1
            while os.path.exists(os.path.join(self.sessions_dir, f"{name}_{i}{ext}")):
                i += 1
            safe_name = f"{name}_{i}{ext}"
            target_path = os.path.join(self.sessions_dir, safe_name)
        with open(target_path, 'wb') as f:
            f.write(file_bytes)
        return safe_name

    def import_sessions_from_zip(self, zip_bytes: bytes) -> int:
        """ZIP içinden .session dosyalarını çıkarıp kaydeder, kaç tane kaydedildiğini döndürür."""
        saved = 0
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_zip = os.path.join(tmpdir, 'upload.zip')
            with open(tmp_zip, 'wb') as f:
                f.write(zip_bytes)
            with zipfile.ZipFile(tmp_zip, 'r') as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    if not info.filename.lower().endswith('.session'):
                        continue
                    with zf.open(info) as src:
                        data = src.read()
                        self.save_session_bytes(os.path.basename(info.filename), data)
                        saved += 1
        return saved

    def delete_all_sessions(self) -> int:
        """Frozens haricindeki tüm .session dosyalarını siler ve kaç dosya silindiğini döndürür."""
        try:
            self.ensure_sessions_dir()
            pattern = os.path.join(self.sessions_dir, "*.session")
            files = glob.glob(pattern)
            frozens_dir = os.path.join(self.sessions_dir, "Frozens")
            frozen_names = set(os.listdir(frozens_dir)) if os.path.isdir(frozens_dir) else set()
            deleted = 0
            for path in files:
                name = os.path.basename(path)
                if name in frozen_names:
                    continue
                try:
                    os.remove(path)
                    deleted += 1
                except Exception:
                    continue
            return deleted
        except Exception as e:
            logger.error(f"Session dosyaları silinirken hata: {e}")
            return 0

# Global session manager
session_manager = SessionManager()

class TelegramBot:
    """Telegram Bot sınıfı"""
    
    def __init__(self):
        self.bot_token = get_bot_api()
        self.admin_ids = get_admin_ids()
        # Her sohbet için gönderdiğimiz mesaj kimliklerini tutar
        # Amaç: Yeni bir mesaj göndermeden önce, sohbetteki eski bot mesajlarını silmek
        self.chat_id_to_message_ids = {}
        
        if not self.bot_token:
            raise ValueError("Bot API token bulunamadı! Lütfen config.py dosyasını kontrol edin.")
        
        # Application oluştur
        self.application = Application.builder().token(self.bot_token).build()
        
        # Handler'ları ekle
        self.setup_handlers()
    
    def create_navigation_buttons(self, current_screen: str = "main") -> List[List[InlineKeyboardButton]]:
        """Navigasyon butonlarını oluşturur"""
        buttons = []
        
        # Ana Menü butonu (her zaman en üstte)
        if current_screen != "main":
            buttons.append([InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")])
        
        # Geri butonu (ana menü dışında her ekranda)
        if current_screen not in ["main", "start"]:
            buttons.append([InlineKeyboardButton("⬅️ Geri", callback_data="go_back")])
        
        return buttons
    
    def setup_handlers(self) -> None:
        """Bot handler'larını ayarlar"""
        # Komut handler'ları
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("sessions", self.sessions_command))
        
        # Callback query handler (buton tıklamaları)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Mesaj handler'ı (form doldurma için)
        from telegram.ext import MessageHandler, filters
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        # Belge/dosya yüklemeleri
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        # Proxy txt yükleme: mime type veya .txt uzantısı ile yakala
        proxy_file_filter = (filters.Document.MimeType("text/plain") | filters.Document.FileExtension("txt"))
        self.application.add_handler(MessageHandler(proxy_file_filter, self.handle_proxy_upload))
    
    async def edit_or_send_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 message: str, reply_markup: InlineKeyboardMarkup = None, parse_mode: str = 'Markdown') -> None:
        """Mesajı düzenler veya yeni mesaj gönderir"""
        try:
            if update.callback_query:
                # Mevcut mesajı düzenle
                edited = await update.callback_query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                # Düzenlenen mesajı da izlemeye al (son mesaj olarak)
                try:
                    chat_id = update.effective_chat.id
                    msg_id = update.callback_query.message.message_id
                    self.chat_id_to_message_ids[chat_id] = [msg_id]
                except Exception:
                    pass
            else:
                # Yeni mesaj göndermeden ÖNCE: sohbetteki önceki bot mesajlarını sil
                try:
                    await self._delete_previous_messages(update, context)
                except Exception as _:
                    # Silme hataları kullanıcı deneyimini bozmasın
                    pass

                # Yeni mesaj gönder
                sent = await update.message.reply_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                # Gönderilen mesajı takip listesine ekle (yalnızca son mesaj tutulur)
                try:
                    chat_id = update.effective_chat.id
                    self.chat_id_to_message_ids[chat_id] = [sent.message_id]
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Mesaj gönderilirken hata: {e}")
            # Parse mode hatası durumunda HTML veya plain text dene
            try:
                if update.callback_query:
                    await update.callback_query.edit_message_text(
                        message,
                        reply_markup=reply_markup,
                        parse_mode='HTML' if parse_mode == 'Markdown' else 'Markdown'
                    )
                else:
                    await update.message.reply_text(
                        message,
                        reply_markup=reply_markup,
                        parse_mode='HTML' if parse_mode == 'Markdown' else 'Markdown'
                    )
            except Exception as e2:
                logger.error(f"HTML parsing hatası: {e2}")
                # Son çare olarak plain text
                if update.callback_query:
                    await update.callback_query.edit_message_text(
                        message,
                        reply_markup=reply_markup
                    )
                else:
                    sent = await update.message.reply_text(
                        message,
                        reply_markup=reply_markup
                    )
                    try:
                        chat_id = update.effective_chat.id
                        self.chat_id_to_message_ids[chat_id] = [sent.message_id]
                    except Exception:
                        pass

    async def _delete_previous_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sohbette botun daha önce gönderdiği TÜM mesajları siler (son mesaj dahil)."""
        chat = update.effective_chat
        if not chat:
            return
        chat_id = chat.id
        message_ids = self.chat_id_to_message_ids.get(chat_id, [])
        if not message_ids:
            return
        # Eski mesajların hepsini silmeyi dene
        for mid in message_ids:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                # Mesaj çok eski olabilir ya da zaten silinmiş olabilir; sorun değil
                continue
        # Temizledikten sonra listeden kaldır
        self.chat_id_to_message_ids[chat_id] = []
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start komutu handler'ı"""
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        # Admin kontrolü
        is_user_admin = is_admin(user_id)
        
        # Ana menü butonları
        keyboard = [
            [InlineKeyboardButton("📊 Toplam Hesap Sayısı", callback_data="count_sessions")],
            [InlineKeyboardButton("⬆️ Session Yükle", callback_data="upload_sessions")],
            [InlineKeyboardButton("🧰 Proxy Ayarları", callback_data="proxy_menu")],
            [InlineKeyboardButton("➕ Kanal Ekle", callback_data="add_channel")],
            [InlineKeyboardButton("📺 Kanallarım", callback_data="my_channels")],
            [InlineKeyboardButton("🌐 Global Havuz", callback_data="global_pool")]
        ]
        
        if is_user_admin:
            keyboard.append([InlineKeyboardButton("🔧 Admin Paneli", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, "Ana Menü", reply_markup)
        
        logger.info(f"Start komutu çalıştırıldı - Kullanıcı: {user_name} (ID: {user_id})")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Help komutu handler'ı"""
        help_message = """
📖 <b>Bot Kullanım Kılavuzu</b>

<b>Komutlar:</b>
• /start - Botu başlatır ve ana menüyü gösterir
• /help - Bu yardım mesajını gösterir
• /sessions - Session dosyalarını sayar

<b>Butonlar:</b>
• 📊 <b>Toplam Hesap Sayısı</b> - Sessions klasöründeki .session dosyalarının sayısını gösterir
• 📋 <b>Session Listesi</b> - Tüm session dosyalarının listesini gösterir
• ℹ️ <b>Yardım</b> - Bu yardım mesajını gösterir

<b>Admin Özellikleri:</b>
• 🔧 <b>Admin Paneli</b> - Gelişmiş yönetim seçenekleri

<b>Not:</b> Bot sadece Sessions klasöründeki .session uzantılı dosyaları sayar.
        """
        
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def sessions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sessions komutu handler'ı"""
        await self.show_session_count(update, context)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Buton tıklama callback handler'ı"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            await self.show_main_menu(update, context)
        elif data == "go_back":
            await self.go_back(update, context)
        elif data == "count_sessions":
            await self.show_session_count(update, context)
        elif data == "list_sessions":
            await self.show_session_list(update, context)
        elif data == "list_frozen":
            await self.show_frozen_list(update, context)
        elif data == "upload_sessions":
            await self.start_upload_sessions(update, context)
        elif data == "confirm_delete_sessions":
            await self.confirm_delete_sessions(update, context)
        elif data == "delete_sessions":
            await self.delete_sessions(update, context)
        elif data == "confirm_delete_frozens":
            await self.confirm_delete_frozens(update, context)
        elif data == "delete_frozens":
            await self.delete_frozens(update, context)
        elif data == "proxy_menu":
            await self.show_proxy_menu(update, context)
        elif data.startswith("proxy_list_"):
            page = int(data.split("_")[-1])
            await self.show_proxy_list(update, context, page)
        elif data == "proxy_upload":
            await self.start_proxy_upload(update, context)
        elif data == "proxy_delete_mode":
            await self.start_proxy_delete(update, context)
        elif data.startswith("session_list_"):
            page = int(data.split("_")[-1])
            await self.show_session_list(update, context, page)
        elif data.startswith("frozen_list_"):
            page = int(data.split("_")[-1])
            await self.show_frozen_list(update, context, page)
        elif data == "help_info":
            await self.show_help_info(update, context)
        elif data == "admin_panel":
            await self.show_admin_panel(update, context)
        elif data == "admin_management":
            await self.show_admin_management(update, context)
        elif data == "add_admin":
            await self.start_add_admin(update, context)
        elif data == "remove_admin":
            await self.start_remove_admin(update, context)
        elif data == "show_logs":
            await self.show_logs(update, context)
        elif data == "refresh_sessions":
            await self.show_session_count(update, context)
        elif data == "add_channel":
            await self.start_add_channel(update, context)
        elif data == "my_channels":
            await self.show_my_channels(update, context)
        elif data == "global_pool":
            await self.show_global_pool(update, context)
        elif data == "start_requests":
            await self.start_requests_callback(update, context)
        elif data == "cancel_channel":
            await self.cancel_channel_add(update, context)
        elif data == "repeat_yes":
            await self.handle_repeat_choice_callback(update, context, "yes")
        elif data == "repeat_no":
            await self.handle_repeat_choice_callback(update, context, "no")
        elif data.startswith("channel_"):
            await self.handle_channel_action(update, context, data)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Ana menüyü gösterir"""
        user_id = str(update.effective_user.id)
        
        # Admin kontrolü
        is_user_admin = is_admin(user_id)
        
        # Ana menü butonları
        keyboard = [
            [InlineKeyboardButton("📊 Toplam Hesap Sayısı", callback_data="count_sessions")],
            [InlineKeyboardButton("⬆️ Session Yükle", callback_data="upload_sessions")],
            [InlineKeyboardButton("🧰 Proxy Ayarları", callback_data="proxy_menu")],
            [InlineKeyboardButton("➕ Kanal Ekle", callback_data="add_channel")],
            [InlineKeyboardButton("📺 Kanallarım", callback_data="my_channels")],
            [InlineKeyboardButton("🌐 Global Havuz", callback_data="global_pool")]
        ]
        
        if is_user_admin:
            keyboard.append([InlineKeyboardButton("🔧 Admin Paneli", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, "Ana Menü", reply_markup)
    
    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Geri döner (şimdilik ana menüye)"""
        await self.show_main_menu(update, context)
    
    async def show_session_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Session sayısını gösterir"""
        try:
            session_info = session_manager.get_session_info()
            frozen_info = session_manager.get_frozen_info()
            
            message = f"""
📊 **Hesap Bilgileri**

🟢 **Aktif Hesaplar:** `{session_info['total_count']}`
🔴 **Frozen Hesaplar:** `{frozen_info['total_count']}`
📄 **Toplam Hesaplar:** `{session_info['total_count'] + frozen_info['total_count']}`
💾 **Toplam Boyut:** `{session_info['total_size_mb'] + frozen_info['total_size_mb']} MB`

{'✅ Hesaplar bulundu!' if (session_info['total_count'] + frozen_info['total_count']) > 0 else '⚠️ Hiç hesap bulunamadı!'}
            """
            
            # Butonları oluştur
            keyboard = [
                [InlineKeyboardButton("🔄 Yenile", callback_data="refresh_sessions")],
                [InlineKeyboardButton("📋 Aktif Liste", callback_data="list_sessions")],
                [InlineKeyboardButton("❄️ Frozen Liste", callback_data="list_frozen")]
            ]
            
            # Navigasyon butonlarını ekle
            nav_buttons = self.create_navigation_buttons("session_count")
            keyboard.extend(nav_buttons)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup)
                
        except Exception as e:
            error_message = f"❌ Hata oluştu: {str(e)}"
            await self.edit_or_send_message(update, context, error_message)
            logger.error(f"Session sayısı gösterilirken hata: {e}")
    
    async def show_session_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
        """Session dosyalarının listesini gösterir (sayfalı)"""
        try:
            session_info = session_manager.get_session_info()
            files = session_info['files']
            
            if not files:
                message = "📋 **Aktif Hesaplar**\n\n⚠️ Hiç aktif hesap bulunamadı!"
                keyboard = self.create_navigation_buttons("session_list")
            else:
                # Sayfalama
                items_per_page = 20
                total_pages = (len(files) + items_per_page - 1) // items_per_page
                start_idx = (page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_files = files[start_idx:end_idx]
                
                message = f"📋 **Aktif Hesaplar** (Sayfa {page}/{total_pages})\n\n"
                for i, file_name in enumerate(page_files, start_idx + 1):
                    message += f"`{i}. {file_name}`\n"
                
                # Sayfa navigasyon butonları
                keyboard = []
                if total_pages > 1:
                    nav_row = []
                    if page > 1:
                        nav_row.append(InlineKeyboardButton("⬅️ Önceki", callback_data=f"session_list_{page-1}"))
                    if page < total_pages:
                        nav_row.append(InlineKeyboardButton("Sonraki ➡️", callback_data=f"session_list_{page+1}"))
                    if nav_row:
                        keyboard.append(nav_row)
                
                # Yönetim butonları
                admin_id = str(update.effective_user.id)
                if is_admin(admin_id):
                    keyboard.append([InlineKeyboardButton("🗑️ Tümünü Sil", callback_data="confirm_delete_sessions")])
                # Ana menü butonu
                keyboard.append([InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")])
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup)
                
        except Exception as e:
            error_message = f"❌ Hata oluştu: {str(e)}"
            await self.edit_or_send_message(update, context, error_message)
            logger.error(f"Session listesi gösterilirken hata: {e}")

    async def confirm_delete_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Tüm aktif session dosyalarını silme onayı."""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        message = (
            "⚠️ <b>Tüm Aktif Session Dosyaları Silinsin mi?</b>\n\n"
            "Bu işlem Frozens klasörü dışındaki <code>.session</code> dosyalarını kalıcı olarak silecektir."
        )
        keyboard = [
            [InlineKeyboardButton("✅ Evet, Sil", callback_data="delete_sessions")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="list_sessions")]
        ]
        await self.edit_or_send_message(update, context, message, InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    async def delete_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Tüm aktif session dosyalarını siler."""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        deleted = session_manager.delete_all_sessions()
        message = f"🗑️ Silme tamamlandı. Kaldırılan dosya: {deleted}"
        keyboard = [
            [InlineKeyboardButton("📋 Listeyi Göster", callback_data="list_sessions")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ]
        await self.edit_or_send_message(update, context, message, InlineKeyboardMarkup(keyboard))
    
    async def show_frozen_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
        """Frozen hesapların listesini gösterir (sayfalı)"""
        try:
            frozen_info = session_manager.get_frozen_info()
            files = frozen_info['files']
            
            if not files:
                message = "❄️ **Frozen Hesaplar**\n\n⚠️ Hiç frozen hesap bulunamadı!"
                keyboard = self.create_navigation_buttons("frozen_list")
            else:
                # Sayfalama
                items_per_page = 20
                total_pages = (len(files) + items_per_page - 1) // items_per_page
                start_idx = (page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_files = files[start_idx:end_idx]
                
                message = f"❄️ **Frozen Hesaplar** (Sayfa {page}/{total_pages})\n\n"
                for i, file_name in enumerate(page_files, start_idx + 1):
                    message += f"`{i}. {file_name}`\n"
                
                # Sayfa navigasyon butonları
                keyboard = []
                if total_pages > 1:
                    nav_row = []
                    if page > 1:
                        nav_row.append(InlineKeyboardButton("⬅️ Önceki", callback_data=f"frozen_list_{page-1}"))
                    if page < total_pages:
                        nav_row.append(InlineKeyboardButton("Sonraki ➡️", callback_data=f"frozen_list_{page+1}"))
                    if nav_row:
                        keyboard.append(nav_row)
                
                # Ana menü butonu
                keyboard.append([InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")])
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup)
                
        except Exception as e:
            error_message = f"❌ Hata oluştu: {str(e)}"
            await self.edit_or_send_message(update, context, error_message)
            logger.error(f"Frozen listesi gösterilirken hata: {e}")

    async def confirm_delete_frozens(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Frozen .session dosyalarını topluca silme onayı"""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        message = (
            "⚠️ <b>Tüm Frozen Session Dosyaları Silinsin mi?</b>\n\n"
            "Bu işlem <code>Sessions/Frozens</code> içindeki .session dosyalarını kalıcı olarak silecektir."
        )
        keyboard = [
            [InlineKeyboardButton("✅ Evet, Sil", callback_data="delete_frozens")],
            [InlineKeyboardButton("🔧 Admin Paneli", callback_data="admin_panel")]
        ]
        await self.edit_or_send_message(update, context, message, InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    async def delete_frozens(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Frozen .session dosyalarını siler"""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        try:
            frozens_dir = os.path.join(session_manager.sessions_dir, 'Frozens')
            deleted = 0
            if os.path.isdir(frozens_dir):
                for name in os.listdir(frozens_dir):
                    if name.lower().endswith('.session'):
                        try:
                            os.remove(os.path.join(frozens_dir, name))
                            deleted += 1
                        except Exception:
                            continue
            await self.edit_or_send_message(update, context, f"🗑️ Frozen silme tamamlandı. Kaldırılan: {deleted}")
        except Exception as e:
            await self.edit_or_send_message(update, context, f"❌ Hata: {str(e)}")

    async def start_upload_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Session yükleme akışını başlatır."""
        user_id = str(update.effective_user.id)
        # Kullanıcı durumunu ayarla
        db_manager.set_user_state(user_id, "waiting_upload", {})
        message = (
            "⬆️ <b>Session Yükleme</b>\n\n"
            "• Bir veya birden fazla <code>.session</code> dosyasını bu sohbete gönderin.\n"
            "• Alternatif olarak <b>.zip</b> arşivi olarak yükleyebilirsiniz (içinden .session dosyaları çıkarılır).\n\n"
            "Gönderim tamamlanınca <b>Ana Menü</b>’ye dönebilir veya yüklemeye devam edebilirsiniz."
        )
        keyboard = [
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.edit_or_send_message(update, context, message, reply_markup, parse_mode='HTML')

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Gönderilen dosyaları işler: .session veya .zip"""
        try:
            user_id = str(update.effective_user.id)
            state, _ = db_manager.get_user_state(user_id)
            # Proxy upload akışı mı?
            if state == "waiting_proxy_upload":
                await self.handle_proxy_upload(update, context)
                return
            # Yalnızca session upload akışında dosya kabul et; aksi halde görmezden gel
            if state != "waiting_upload":
                return
            document = update.message.document
            if not document:
                return
            file = await context.bot.get_file(document.file_id)
            data = await file.download_as_bytearray()
            filename = (document.file_name or 'upload').lower()
            saved_count = 0
            saved_names = []
            if filename.endswith('.zip'):
                saved_count = session_manager.import_sessions_from_zip(bytes(data))
            elif filename.endswith('.session'):
                saved_name = session_manager.save_session_bytes(filename, bytes(data))
                saved_count = 1
                saved_names = [saved_name]
            else:
                await update.message.reply_text("❌ Sadece .session veya .zip dosyaları kabul edilir.")
                return
            # Yükleme bilgisi
            info = session_manager.get_session_info()
            text = (
                "✅ Yükleme tamamlandı!\n\n"
                f"Kaydedilen dosya sayısı: {saved_count}\n"
                f"Toplam aktif hesap: {info['total_count']}\n"
            )
            if saved_names:
                text += "\n" + "\n".join(f"• {name}" for name in saved_names)
            keyboard = [
                [InlineKeyboardButton("📊 Güncel Sayı", callback_data="count_sessions")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Belge işleme hatası: {e}")
            await update.message.reply_text(f"❌ Hata: {str(e)}")

    async def handle_proxy_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """proxies.txt yükleme handler'ı"""
        try:
            user_id = str(update.effective_user.id)
            state, _ = db_manager.get_user_state(user_id)
            if state != "waiting_proxy_upload":
                # Yükleme menüsünden gelinmemişse görmezden gel
                return
            document = update.message.document
            if not document or not document.file_name.lower().endswith('.txt'):
                await update.message.reply_text("❌ Lütfen .txt uzantılı bir dosya gönderin. (proxies.txt)")
                return
            file = await context.bot.get_file(document.file_id)
            data = await file.download_as_bytearray()
            text = bytes(data).decode('utf-8', errors='ignore')
            lines = [ln.rstrip('\r') for ln in text.split('\n')]
            if proxy_manager.write_raw_lines(lines):
                db_manager.clear_user_state(user_id)
                count = proxy_manager.get_proxy_count()
                await update.message.reply_text(f"✅ Proxy dosyası güncellendi. Toplam: {count}")
                # Menüye dönüş butonu
                await update.message.reply_text(
                    "🧰 Proxy Menüsü",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧰 Proxy Menüsü", callback_data="proxy_menu")]])
                )
            else:
                await update.message.reply_text("❌ Proxy dosyası yazılamadı.")
        except Exception as e:
            logger.error(f"Proxy upload hatası: {e}")
            await update.message.reply_text(f"❌ Hata: {str(e)}")
    
    async def show_help_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Yardım bilgilerini gösterir"""
        help_message = """
ℹ️ **Yardım Bilgileri**

**Bot Ne Yapar?**
Bu bot, Sessions klasöründeki .session uzantılı dosyaları sayar ve bilgilerini gösterir.

**Nasıl Kullanılır?**
1. `/start` komutu ile botu başlatın
2. "📊 Toplam Hesap Sayısı" butonuna tıklayın
3. Session dosyalarının sayısını görün

**Dosya Formatı:**
• Sadece `.session` uzantılı dosyalar sayılır
• Dosyalar `Sessions/` klasöründe olmalıdır

**Sorun Giderme:**
• Session dosyaları bulunamıyorsa, dosyaların doğru klasörde olduğundan emin olun
• Dosya uzantılarının `.session` olduğundan emin olun
        """
        
        # Navigasyon butonlarını oluştur
        nav_buttons = self.create_navigation_buttons("help")
        keyboard = nav_buttons
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, help_message, reply_markup)
    
    async def show_proxy_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Proxy ayarları ana menüsü"""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        message = "🧰 <b>Proxy Ayarları</b>\n\nAşağıdan seçim yapın."
        keyboard = [
            [InlineKeyboardButton("📄 Proxyleri Gör", callback_data="proxy_list_1")],
            [InlineKeyboardButton("⬆️ Proxy Yükle", callback_data="proxy_upload")],
            [InlineKeyboardButton("🗑️ Proxy Sil", callback_data="proxy_delete_mode")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ]
        await self.edit_or_send_message(update, context, message, InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    async def show_proxy_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
        """Proxyleri 30'arlı sayfalar halinde listeler"""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        lines = proxy_manager.get_raw_lines()
        if not lines:
            await self.edit_or_send_message(update, context, "📄 Proxy dosyası boş veya bulunamadı.")
            return
        per_page = 30
        total_pages = (len(lines) + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        page_lines = lines[start:end]
        message = f"📄 <b>Proxy Listesi</b> (Sayfa {page}/{total_pages})\n\n"
        for i, line in enumerate(page_lines, start + 1):
            message += f"`{i}. {line}`\n"
        # Nav + geri
        keyboard = []
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("⬅️ Önceki", callback_data=f"proxy_list_{page-1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("Sonraki ➡️", callback_data=f"proxy_list_{page+1}"))
        if nav:
            keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("🧰 Proxy Menüsü", callback_data="proxy_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.edit_or_send_message(update, context, message, reply_markup, parse_mode='HTML')

    async def start_proxy_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Proxy yükleme modunu başlatır"""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        db_manager.set_user_state(user_id, "waiting_proxy_upload", {})
        message = (
            "⬆️ <b>Proxy Yükle</b>\n\n"
            "Lütfen <code>proxies.txt</code> dosyasını gönderin. Mevcut dosya üzerine yazılır."
        )
        keyboard = [[InlineKeyboardButton("🧰 Proxy Menüsü", callback_data="proxy_menu")]]
        await self.edit_or_send_message(update, context, message, InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    async def start_proxy_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Proxy silme modunu başlatır (ID ile veya satırı yapıştırarak)"""
        user_id = str(update.effective_user.id)
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        db_manager.set_user_state(user_id, "waiting_proxy_delete", {})
        message = (
            "🗑️ <b>Proxy Silme</b>\n\n"
            "Silmek için ya ID numarasını gönderin (örn: 12) ya da \n"
            "silmek istediğiniz proxy satırını aynen yapıştırın."
        )
        keyboard = [[InlineKeyboardButton("🧰 Proxy Menüsü", callback_data="proxy_menu")]]
        await self.edit_or_send_message(update, context, message, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin panelini gösterir"""
        user_id = str(update.effective_user.id)
        
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        
        # Admin sayısını al
        admins = db_manager.get_all_admins()
        total_admins = len(admins)
        
        admin_message = f"""
🔧 **Admin Paneli**

👑 **Admin ID:** `{user_id}`
📊 **Toplam Admin:** `{total_admins}`
📁 **Sessions Klasörü:** `{os.path.abspath('Sessions')}`
        """
        
        # Admin panel butonları
        keyboard = [
            [InlineKeyboardButton("👥 Admin Yönetimi", callback_data="admin_management")],
            [InlineKeyboardButton("📋 Session Listesi", callback_data="list_sessions")],
            [InlineKeyboardButton("🗑️ Frozenları Sil", callback_data="confirm_delete_frozens")],
            [InlineKeyboardButton("📊 Session Raporu", callback_data="count_sessions")],
            [InlineKeyboardButton("📋 Logları Gör", callback_data="show_logs")]
        ]
        
        # Navigasyon butonlarını ekle
        nav_buttons = self.create_navigation_buttons("admin_panel")
        keyboard.extend(nav_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, admin_message, reply_markup)
    
    async def show_admin_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin yönetimi panelini gösterir"""
        user_id = str(update.effective_user.id)
        
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        
        # Admin listesini al
        admins = db_manager.get_all_admins()
        
        message = f"""
👥 **Admin Yönetimi**

📊 **Toplam Admin:** `{len(admins)}`

**Mevcut Adminler:**
        """
        
        for i, admin in enumerate(admins, 1):
            username = f"@{admin['username']}" if admin['username'] else "Kullanıcı adı yok"
            message += f"\n`{i}. {admin['first_name']} ({username})`"
            message += f"\n   ID: `{admin['user_id']}`"
            message += f"\n   Ekleyen: `{admin['added_by'] or 'Sistem'}`"
            message += f"\n   Tarih: `{admin['added_at'][:16]}`\n"
        
        # Admin yönetimi butonları
        keyboard = [
            [InlineKeyboardButton("➕ Admin Ekle", callback_data="add_admin")],
            [InlineKeyboardButton("➖ Admin Çıkar", callback_data="remove_admin")],
            [InlineKeyboardButton("🔄 Yenile", callback_data="admin_management")]
        ]
        
        # Geri butonu
        keyboard.append([InlineKeyboardButton("⬅️ Geri", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, message, reply_markup)
    
    async def start_add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin ekleme sürecini başlatır"""
        user_id = str(update.effective_user.id)
        
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        
        # Kullanıcı durumunu ayarla
        db_manager.set_user_state(user_id, "waiting_admin_id", {})
        
        message = """
➕ **Admin Ekleme**

Lütfen eklemek istediğiniz kullanıcının Telegram ID'sini girin:

**Nasıl ID Bulunur:**
• Kullanıcıya `/start` yazdırın
• Bot loglarında ID'yi görebilirsiniz
• Veya kullanıcıdan ID'sini isteyin

**Örnek:** `123456789`
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ İptal", callback_data="admin_management")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, message, reply_markup)
    
    async def start_remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin çıkarma sürecini başlatır"""
        user_id = str(update.effective_user.id)
        
        if not is_admin(user_id):
            await self.edit_or_send_message(update, context, "❌ Bu özelliği kullanma yetkiniz yok!")
            return
        
        # Kullanıcı durumunu ayarla
        db_manager.set_user_state(user_id, "waiting_remove_admin_id", {})
        
        message = """
➖ **Admin Çıkarma**

Lütfen çıkarmak istediğiniz admin'in Telegram ID'sini girin:

**Mevcut Adminler:**
        """
        
        # Admin listesini göster
        admins = db_manager.get_all_admins()
        for i, admin in enumerate(admins, 1):
            message += f"\n`{i}. {admin['first_name']} - ID: {admin['user_id']}`"
        
        message += "\n\n**Örnek:** `123456789`"
        
        keyboard = [
            [InlineKeyboardButton("❌ İptal", callback_data="admin_management")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, message, reply_markup)
    
    async def handle_admin_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str) -> None:
        """Admin ID'sini işler"""
        user_id = str(update.effective_user.id)
        
        try:
            # ID'yi kontrol et
            if not admin_id.isdigit():
                await update.message.reply_text("❌ Geçersiz ID formatı! Sadece sayı girin.")
                return
            
            # Kullanıcı bilgilerini al
            try:
                # Telegram'dan kullanıcı bilgilerini almaya çalış
                user_info = await context.bot.get_chat(admin_id)
                username = user_info.username
                first_name = user_info.first_name
            except Exception:
                username = None
                first_name = "Bilinmeyen"
            
            # Admin ekle
            success = db_manager.add_admin(
                user_id=admin_id,
                username=username,
                first_name=first_name,
                added_by=user_id
            )
            
            if success:
                message = f"""
✅ **Admin Başarıyla Eklendi!**

👤 **İsim:** `{first_name}`
🆔 **ID:** `{admin_id}`
👤 **Username:** `@{username}` if username else "Yok"
👑 **Ekleyen:** `{user_id}`
                """
            else:
                message = "❌ Admin eklenirken hata oluştu!"
            
            # Kullanıcı durumunu temizle
            db_manager.clear_user_state(user_id)
            
            keyboard = [
                [InlineKeyboardButton("👥 Admin Yönetimi", callback_data="admin_management")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Admin ekleme hatası: {e}")
            await update.message.reply_text(f"❌ Hata oluştu: {str(e)}")
    
    async def handle_remove_admin_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str) -> None:
        """Admin çıkarma ID'sini işler"""
        user_id = str(update.effective_user.id)
        
        try:
            # ID'yi kontrol et
            if not admin_id.isdigit():
                await update.message.reply_text("❌ Geçersiz ID formatı! Sadece sayı girin.")
                return
            
            # Kendini çıkarmaya çalışıyor mu?
            if admin_id == user_id:
                await update.message.reply_text("❌ Kendinizi admin listesinden çıkaramazsınız!")
                return
            
            # Admin çıkar
            success = db_manager.remove_admin(admin_id)
            
            if success:
                message = f"✅ Admin başarıyla çıkarıldı! (ID: {admin_id})"
            else:
                message = f"❌ Admin bulunamadı! (ID: {admin_id})"
            
            # Kullanıcı durumunu temizle
            db_manager.clear_user_state(user_id)
            
            keyboard = [
                [InlineKeyboardButton("👥 Admin Yönetimi", callback_data="admin_management")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Admin çıkarma hatası: {e}")
            await update.message.reply_text(f"❌ Hata oluştu: {str(e)}")
    
    async def start_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Kanal ekleme sürecini başlatır"""
        user_id = str(update.effective_user.id)
        
        # Kullanıcı durumunu ayarla
        db_manager.set_user_state(user_id, "waiting_channel_link", {})
        
        message = """
➕ **Kanal Ekleme**

Lütfen kanal linkini giriniz:

**Örnek formatlar:**
• `https://t.me/kanal_adi` (Normal kanal)
• `https://t.me/+abc123def` (Gizli kanal)
• `@kanal_adi` (Username)
• `t.me/kanal_adi` (Kısa format)
• `+abc123def` (Sadece davet kodu)

⚠️ **Not:** Kanal linki geçerli olmalı ve erişilebilir olmalıdır.
        """
        
        # İptal butonu
        keyboard = [
            [InlineKeyboardButton("❌ İptal", callback_data="cancel_channel")]
        ]
        
        # Navigasyon butonlarını ekle
        nav_buttons = self.create_navigation_buttons("add_channel")
        keyboard.extend(nav_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, message, reply_markup)
    
    async def show_my_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Kullanıcının kanallarını gösterir"""
        user_id = str(update.effective_user.id)
        
        try:
            channels = db_manager.get_user_channels(user_id)
            
            if not channels:
                message = """
📺 **Kanallarım**

Henüz hiç kanal eklenmemiş.

Kanal eklemek için "➕ Kanal Ekle" butonunu kullanın.
                """
                keyboard = [
                    [InlineKeyboardButton("➕ Yeni Kanal Ekle", callback_data="add_channel")]
                ]
                
                # Navigasyon butonlarını ekle
                nav_buttons = self.create_navigation_buttons("my_channels")
                keyboard.extend(nav_buttons)
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await self.edit_or_send_message(update, context, message, reply_markup)
            else:
                # Temiz görünüm: doğrudan kanal kartlarını gönder
                for i, channel in enumerate(channels, 1):
                    await self.send_channel_message(update, context, channel, i)
                # En son bir ana menü butonu gönder
                await update.effective_message.reply_text(
                    "🏠 Ana Menü",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]])
                )
            
        except Exception as e:
            error_message = f"""
❌ **Hata Oluştu!**

Kanallar gösterilirken bir hata oluştu: `{str(e)}`

Lütfen tekrar deneyin veya Ana Menü'ye dönün.
            """
            
            keyboard = [
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, error_message, reply_markup)
            logger.error(f"Kanallar gösterilirken hata: {e}")
    
    async def send_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel: dict, channel_number: int) -> None:
        """Tek bir kanal için ayrı mesaj gönderir"""
        try:
            status_emoji = "🟢" if channel['status'] == 'active' else "🔴"
            status_text = "Aktif" if channel['status'] == 'active' else "Duraklatıldı"
            
            # İstek istatistiklerini al
            stats = db_manager.get_request_stats(channel['id'])
            
            message = f"""
📺 **Kanal #{channel_number}**

{status_emoji} **{channel['channel_link']}**

📊 **İstek:** {channel['total_requests']} | ⏱️ **Süre:** {channel['duration_minutes']} dk
📈 **Durum:** {stats['Gönderildi']} gönderildi, {stats['Bekliyor']} bekliyor, {stats['Atlandı']} atlandı
📅 **Tarih:** {channel['created_at'][:16]}
            """
            
            # Kanal yönetim butonları
            channel_id = channel['id']
            status = channel['status']
            
            if status == 'active':
                # Aktif kanal - Duraklat, Sil, Yenile, Planlanan İstekler
                keyboard = [
                    [
                        InlineKeyboardButton("⏸️ Duraklat", callback_data=f"channel_pause_{channel_id}"),
                        InlineKeyboardButton("🗑️ Sil", callback_data=f"channel_delete_{channel_id}")
                    ],
                    [
                        InlineKeyboardButton("🔄 Yenile", callback_data=f"channel_refresh_{channel_id}"),
                        InlineKeyboardButton("📋 Planlanan İstekler", callback_data=f"channel_planned_{channel_id}")
                    ],
                    [
                        InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")
                    ]
                ]
            else:
                # Duraklatılmış kanal - Başlat, Sil, Yenile, Planlanan İstekler
                keyboard = [
                    [
                        InlineKeyboardButton("▶️ Başlat", callback_data=f"channel_start_{channel_id}"),
                        InlineKeyboardButton("🗑️ Sil", callback_data=f"channel_delete_{channel_id}")
                    ],
                    [
                        InlineKeyboardButton("🔄 Yenile", callback_data=f"channel_refresh_{channel_id}"),
                        InlineKeyboardButton("📋 Planlanan İstekler", callback_data=f"channel_planned_{channel_id}")
                    ],
                    [
                        InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Yeni mesaj gönder (edit değil)
            await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Kanal mesajı gönderilirken hata: {e}")
            # Hata durumunda basit mesaj gönder
            error_msg = f"❌ Kanal #{channel_number} mesajı gönderilemedi: {str(e)}"
            await update.effective_message.reply_text(error_msg)
    
    async def cancel_channel_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Kanal ekleme işlemini iptal eder"""
        user_id = str(update.effective_user.id)
        
        # Kullanıcı durumunu temizle
        db_manager.clear_user_state(user_id)
        
        message = """
❌ **Kanal Ekleme İptal Edildi**

Ana menüye dönüyorsunuz.
        """
        
        # Ana menüye dön
        await self.show_main_menu(update, context)
    
    async def start_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """İstek gönderme işlemini başlatır (mesaj handler için)"""
        user_id = str(update.effective_user.id)
        
        try:
            # Kullanıcı durumunu al
            state, temp_data = db_manager.get_user_state(user_id)
            
            if state != "ready_to_start":
                await self.edit_or_send_message(update, context, "❌ Geçersiz işlem durumu!")
                return
            
            channel_id = temp_data.get('channel_id')
            if not channel_id:
                await self.edit_or_send_message(update, context, "❌ Kanal bilgisi bulunamadı!")
                return
            
            # Session dosyalarını al
            session_files = session_manager.get_session_files()
            if not session_files:
                await self.edit_or_send_message(update, context, "❌ Hiç session dosyası bulunamadı!")
                return
            
            # Proxy'leri yükle
            proxy_manager.reload_proxies()
            proxies = [proxy_manager.get_proxy_string(p) for p in proxy_manager.proxies]
            
            # İstek havuzunu oluştur
            success = db_manager.create_request_pool(channel_id, session_files, proxies)
            
            if success:
                # Kullanıcı durumunu temizle
                db_manager.clear_user_state(user_id)
                
                message = """
🚀 **İstek Gönderme Başlatıldı!**

✅ Kanal başarıyla eklendi
✅ İstek havuzu oluşturuldu
✅ Proxy'ler atandı

İstekler planlanan zamanlarda otomatik olarak gönderilecek.

📊 **Detaylar:**
• Session dosyaları: {} adet
• Proxy sayısı: {} adet
• Toplam istek: {} adet

Ana menüden "📺 Kanallarım" ile ilerlemeyi takip edebilirsiniz.
                """.format(
                    len(session_files),
                    len(proxies),
                    temp_data.get('total_requests', 0)
                )
                
                # Ana menü butonu
                keyboard = [
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.edit_or_send_message(update, context, message, reply_markup)
                
            else:
                await self.edit_or_send_message(update, context, "❌ İstek havuzu oluşturulamadı!")
                
        except Exception as e:
            error_message = f"❌ Hata oluştu: {str(e)}"
            await self.edit_or_send_message(update, context, error_message)
            logger.error(f"İstek başlatılırken hata: {e}")
    
    async def start_requests_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """İstek gönderme işlemini başlatır (callback handler için)"""
        user_id = str(update.effective_user.id)
        
        try:
            # Kullanıcı durumunu al
            state, temp_data = db_manager.get_user_state(user_id)
            
            # Eğer kullanıcı durumu yoksa, son eklenen kanalı bul
            if not state or state not in ["ready_to_start", "waiting_repeat_choice"]:
                # Son eklenen kanalı bul
                channels = db_manager.get_user_channels(user_id)
                if not channels:
                    await self.edit_or_send_message(update, context, "❌ Hiç kanal bulunamadı!")
                    return
                
                # En son eklenen kanalı al
                latest_channel = max(channels, key=lambda x: x['id'])
                channel_id = latest_channel['id']
            else:
                channel_id = temp_data.get('channel_id')
                if not channel_id:
                    await self.edit_or_send_message(update, context, "❌ Kanal bilgisi bulunamadı!")
                    return
            
            # Session dosyalarını al
            session_files = session_manager.get_session_files()
            if not session_files:
                await self.edit_or_send_message(update, context, "❌ Hiç session dosyası bulunamadı!")
                return
            
            # Proxy'leri yükle
            proxy_manager.reload_proxies()
            proxies = [proxy_manager.get_proxy_string(p) for p in proxy_manager.proxies]
            
            # İstek havuzunu oluştur
            success = db_manager.create_request_pool(channel_id, session_files, proxies)
            
            if success:
                # Kullanıcı durumunu temizle
                db_manager.clear_user_state(user_id)
                
                message = """
🚀 **İstek Gönderme Başlatıldı!**

✅ Kanal başarıyla eklendi
✅ İstek havuzu oluşturuldu
✅ Proxy'ler atandı

İstekler planlanan zamanlarda otomatik olarak gönderilecek.

📊 **Detaylar:**
• Session dosyaları: {} adet
• Proxy sayısı: {} adet

Ana menüden "📺 Kanallarım" ile ilerlemeyi takip edebilirsiniz.
                """.format(
                    len(session_files),
                    len(proxies)
                )
                
                # Ana menü butonu
                keyboard = [
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.edit_or_send_message(update, context, message, reply_markup)
                
            else:
                await self.edit_or_send_message(update, context, "❌ İstek havuzu oluşturulamadı!")
                
        except Exception as e:
            error_message = f"❌ Hata oluştu: {str(e)}"
            await self.edit_or_send_message(update, context, error_message)
            logger.error(f"İstek başlatılırken hata: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mesaj handler'ı - form doldurma süreci için"""
        user_id = str(update.effective_user.id)
        message_text = update.message.text.strip()
        
        try:
            # Kullanıcı durumunu al
            state, temp_data = db_manager.get_user_state(user_id)
            
            if not state:
                # Normal mesaj, işleme
                return
            
            if state == "waiting_channel_link":
                await self.handle_channel_link(update, context, message_text)
            elif state == "waiting_request_count":
                await self.handle_request_count(update, context, message_text)
            elif state == "waiting_duration":
                await self.handle_duration(update, context, message_text)
            elif state == "waiting_repeat_choice":
                await self.handle_repeat_choice(update, context, message_text)
            elif state == "waiting_admin_id":
                await self.handle_admin_id(update, context, message_text)
            elif state == "waiting_remove_admin_id":
                await self.handle_remove_admin_id(update, context, message_text)
            else:
                # Bilinmeyen durum, temizle
                db_manager.clear_user_state(user_id)
                
        except Exception as e:
            logger.error(f"Mesaj işlenirken hata: {e}")
            
            error_message = f"""
❌ **Hata Oluştu!**

Mesaj işlenirken bir hata oluştu: `{str(e)}`

Lütfen tekrar deneyin veya Ana Menü'ye dönün.
            """
            
            keyboard = [
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(error_message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def handle_channel_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link: str) -> None:
        """Kanal linki işler"""
        user_id = str(update.effective_user.id)
        
        # Link formatını kontrol et
        if not self.is_valid_channel_link(link):
            await update.message.reply_text(
                "❌ Geçersiz kanal linki formatı!\n\n"
                "Lütfen geçerli bir kanal linki girin:\n"
                "• `https://t.me/kanal_adi` (Normal kanal)\n"
                "• `https://t.me/+abc123def` (Gizli kanal)\n"
                "• `@kanal_adi` (Username)\n"
                "• `t.me/kanal_adi` (Kısa format)\n"
                "• `+abc123def` (Sadece davet kodu)"
            )
            return
        
        # Geçici veriyi güncelle
        temp_data = {'channel_link': link}
        db_manager.set_user_state(user_id, "waiting_request_count", temp_data)
        
        # Önceki mesajları sil
        try:
            await update.message.delete()
            # "➕ Kanal Ekleme" mesajını da sil
            if update.message.reply_to_message:
                await update.message.reply_to_message.delete()
        except Exception as e:
            logger.warning(f"Mesaj silinemedi: {e}")
        
        # Aktif session sayısını göster
        active_count = len(session_manager.get_session_files())
        message = """
📊 **İstek Sayısı**

Kanal: `{}`
🔹 Aktif hesap: `{}`

Kaç istek? (1-1000)
        """.format(link, active_count)
        
        # İptal ve Ana Menü butonları
        keyboard = [
            [InlineKeyboardButton("❌ İptal", callback_data="cancel_channel")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.edit_or_send_message(update, context, message, reply_markup, parse_mode='HTML')
    
    async def handle_request_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE, count_text: str) -> None:
        """İstek sayısı işler"""
        user_id = str(update.effective_user.id)
        
        try:
            count = int(count_text)
            if not (1 <= count <= 1000):
                await update.message.reply_text(
                    "❌ İstek sayısı 1-1000 arasında olmalıdır!\n\n"
                    "Lütfen geçerli bir sayı girin:"
                )
                return
            
            # Geçici veriyi güncelle
            state, temp_data = db_manager.get_user_state(user_id)
            temp_data['total_requests'] = count
            db_manager.set_user_state(user_id, "waiting_duration", temp_data)
            
            # Önceki mesajları sil
            try:
                await update.message.delete()
                # "📊 İstek Sayısı" mesajını da sil
                if update.message.reply_to_message:
                    await update.message.reply_to_message.delete()
            except Exception as e:
                logger.warning(f"Mesaj silinemedi: {e}")
            
            active_count = len(session_manager.get_session_files())
            message = """
⏱️ **Süre**

Aktif hesap: `{}`

Kaç dakika? (maksimum 1440)
            """.format(active_count)
            
            # İptal ve Ana Menü butonları
            keyboard = [
                [InlineKeyboardButton("❌ İptal", callback_data="cancel_channel")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup, parse_mode='HTML')
            
        except ValueError:
            await update.message.reply_text(
                "❌ Geçersiz sayı formatı!\n\n"
                "Lütfen sadece sayı girin (örn: 50):"
            )
    
    async def handle_duration(self, update: Update, context: ContextTypes.DEFAULT_TYPE, duration_text: str) -> None:
        """Süre işler"""
        user_id = str(update.effective_user.id)
        
        try:
            duration = int(duration_text)
            # 1 ile 1440 arası sınırı kaldır, sadece pozitif olsun, üst limit 1440 olarak uyarı amaçlı gösterildi
            if duration < 1:
                await update.message.reply_text(
                    "❌ Süre 1 veya daha büyük olmalıdır!\n\n"
                    "Lütfen geçerli bir süre girin:"
                )
                return
            
            # Geçici veriyi al ve 4. soruyu sor
            state, temp_data = db_manager.get_user_state(user_id)
            channel_link = temp_data.get('channel_link')
            total_requests = temp_data.get('total_requests')
            
            # 4. soru: Tekrar istek gönderme
            temp_data['duration'] = duration
            db_manager.set_user_state(user_id, "waiting_repeat_choice", temp_data)
            
            # Önceki mesajları sil
            try:
                await update.message.delete()
                # "⏱️ Süre Belirleme" mesajını da sil
                if update.message.reply_to_message:
                    await update.message.reply_to_message.delete()
            except Exception as e:
                logger.warning(f"Mesaj silinemedi: {e}")
            
            message = f"""
🔄 **Tekrar İstek Gönderme**

Süre alındı: `{duration}` dakika

Daha önce istek göndermiş hesaplar tekrar istek göndersin mi?

**Seçenekler:**
• **Evet** - Daha önce istek göndermiş hesaplar da tekrar istek gönderebilir
• **Hayır** - Sadece daha önce istek göndermemiş hesaplar istek gönderebilir
            """
            
            # Evet/Hayır butonları
            keyboard = [
                [InlineKeyboardButton("✅ Evet", callback_data="repeat_yes")],
                [InlineKeyboardButton("❌ Hayır", callback_data="repeat_no")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup, parse_mode='HTML')
            return
            
            if not channel_id:
                error_message = """
❌ **Kanal Eklenemedi!**

Kanal eklenirken bir hata oluştu. Lütfen tekrar deneyin.

Sorun devam ederse:
• Kanal linkinin doğru olduğundan emin olun
• Botu yeniden başlatın
• Destek ile iletişime geçin
                """
                
                keyboard = [
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(error_message, reply_markup=reply_markup, parse_mode='HTML')
                return
            
            # Geçici veriyi güncelle
            temp_data['channel_id'] = channel_id
            db_manager.set_user_state(user_id, "ready_to_start", temp_data)
            
            # Kanalın yeni mi yoksa güncellenmiş mi olduğunu kontrol et
            channel = db_manager.get_channel(channel_id)
            is_updated = channel and channel['created_at'] != channel['created_at']  # Bu kontrolü daha iyi yapalım
            
            # Basit kontrol: Eğer aynı link ile daha önce kanal varsa güncelleme
            existing_channels = db_manager.get_user_channels(user_id)
            is_update = any(ch['channel_link'] == channel_link for ch in existing_channels if ch['id'] != channel_id)
            
            if is_update:
                status_text = "✅ **Kanal Güncellendi!**"
                action_text = "Kanal bilgileri başarıyla güncellendi."
            else:
                status_text = "✅ **Kanal Bilgileri Tamamlandı!**"
                action_text = "Kanal başarıyla eklendi."
            
            message = f"""
{status_text}

{action_text}

📺 **Kanal:** `{channel_link}`
📊 **İstek Sayısı:** `{total_requests}`
⏱️ **Süre:** `{duration}` dakika

İstekler {duration} dakika içinde rastgele zamanlarda gönderilecek.

Başlatmak için aşağıdaki butona basın:
            """
            
            # Başlat ve Ana menü butonları
            keyboard = [
                [InlineKeyboardButton("🚀 Başlat", callback_data="start_requests")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
            
        except ValueError:
            await update.message.reply_text(
                "❌ Geçersiz süre formatı!\n\n"
                "Lütfen sadece sayı girin (örn: 60):"
            )
    
    def is_valid_channel_link(self, link: str) -> bool:
        """Kanal linkinin geçerli olup olmadığını kontrol eder"""
        import re
        
        # Telegram kanal linki pattern'leri
        patterns = [
            r'^https://t\.me/[a-zA-Z0-9_]+$',  # Normal kanal: https://t.me/kanal_adi
            r'^https://t\.me/\+[a-zA-Z0-9_-]+$',  # Gizli kanal: https://t.me/+abc123
            r'^@[a-zA-Z0-9_]+$',  # Username: @kanal_adi
            r'^t\.me/[a-zA-Z0-9_]+$',  # Kısa format: t.me/kanal_adi
            r'^t\.me/\+[a-zA-Z0-9_-]+$',  # Gizli kanal kısa: t.me/+abc123
            r'^\+[a-zA-Z0-9_-]+$'  # Sadece davet kodu: +abc123
        ]
        
        for pattern in patterns:
            if re.match(pattern, link):
                return True
        
        return False
    
    async def handle_channel_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
        """Kanal yönetim işlemlerini handle eder"""
        user_id = str(update.effective_user.id)
        
        try:
            # Action'ı parse et
            parts = action.split('_')
            if len(parts) < 3:
                await self.edit_or_send_message(update, context, "❌ Geçersiz işlem!")
                return
            
            # Action type'ı belirle
            if len(parts) == 3:
                # channel_start_1, channel_pause_1, channel_delete_1
                action_type = parts[1]  # start, pause, delete
                channel_id = int(parts[2])
            elif len(parts) == 4:
                # channel_confirm_delete_1
                action_type = f"{parts[1]}_{parts[2]}"  # confirm_delete
                channel_id = int(parts[3])
            else:
                await self.edit_or_send_message(update, context, f"❌ Geçersiz işlem formatı! Action: {action}")
                return
            
            # Kanalın kullanıcıya ait olup olmadığını kontrol et
            channel = db_manager.get_channel(channel_id)
            if not channel or channel['user_id'] != user_id:
                await self.edit_or_send_message(update, context, "❌ Bu kanalı yönetme yetkiniz yok!")
                return
            
            if action_type == "start":
                await self.start_channel(update, context, channel_id)
            elif action_type == "pause":
                await self.pause_channel(update, context, channel_id)
            elif action_type == "delete":
                await self.delete_channel(update, context, channel_id)
            elif action_type == "confirm_delete":
                await self.confirm_delete_channel(update, context, channel_id)
            elif action_type == "refresh":
                await self.refresh_channel(update, context, channel_id)
            elif action_type == "planned":
                await self.show_planned_requests(update, context, channel_id)
            else:
                await self.edit_or_send_message(update, context, f"❌ Geçersiz işlem! Action: {action}, Type: {action_type}")
                
        except Exception as e:
            logger.error(f"Kanal işlemi hatası: {e}, Action: {action}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def start_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int) -> None:
        """Kanalı başlatır"""
        try:
            # Kanal durumunu aktif yap
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE channels SET status = ? WHERE id = ?', ('active', channel_id))
                conn.commit()
            
            # Session dosyalarını al
            session_files = session_manager.get_session_files()
            if not session_files:
                await self.edit_or_send_message(update, context, "❌ Hiç session dosyası bulunamadı!")
                return
            
            # Proxy'leri yükle
            proxy_manager.reload_proxies()
            proxies = [proxy_manager.get_proxy_string(p) for p in proxy_manager.proxies]
            
            # İstek havuzunu oluştur
            success = db_manager.create_request_pool(channel_id, session_files, proxies)
            
            if success:
                message = f"""
✅ **Kanal Başlatıldı!**

Kanal başarıyla başlatıldı ve istekler gönderilmeye başlandı.

📊 **Detaylar:**
• Session dosyaları: {len(session_files)} adet
• Proxy sayısı: {len(proxies)} adet
• İstekler planlanıyor...

Kanallarım listesinden ilerlemeyi takip edebilirsiniz.
                """
            else:
                message = "❌ Kanal başlatılamadı! Lütfen tekrar deneyin."
            
            # Kanallarım listesine dön
            await self.show_my_channels(update, context)
            
        except Exception as e:
            logger.error(f"Kanal başlatma hatası: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def pause_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int) -> None:
        """Kanalı duraklatır"""
        try:
            # Kanal durumunu duraklatılmış yap
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE channels SET status = ? WHERE id = ?', ('paused', channel_id))
                
                # Bekleyen istekleri iptal et
                cursor.execute('''
                    UPDATE request_pool 
                    SET status = 'Atlandı' 
                    WHERE channel_id = ? AND status = 'Bekliyor'
                ''', (channel_id,))
                conn.commit()
            
            message = """
⏸️ **Kanal Duraklatıldı!**

Kanal başarıyla duraklatıldı.
Bekleyen istekler iptal edildi.

Kanalı tekrar başlatmak için "▶️ Başlat" butonunu kullanın.
            """
            
            # Kanallarım listesine dön
            await self.show_my_channels(update, context)
            
        except Exception as e:
            logger.error(f"Kanal duraklatma hatası: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def delete_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int) -> None:
        """Kanalı siler"""
        try:
            # Onay mesajı göster
            message = """
⚠️ **Kanal Silme Onayı**

Bu kanalı ve tüm isteklerini silmek istediğinizden emin misiniz?

Bu işlem geri alınamaz!
            """
            
            keyboard = [
                [InlineKeyboardButton("✅ Evet, Sil", callback_data=f"channel_confirm_delete_{channel_id}")],
                [InlineKeyboardButton("❌ İptal", callback_data="my_channels")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.edit_or_send_message(update, context, message, reply_markup)
            
        except Exception as e:
            logger.error(f"Kanal silme onayı hatası: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def confirm_delete_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int) -> None:
        """Kanal silme işlemini onaylar"""
        try:
            # Kanalı ve tüm isteklerini sil
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Önce kanalın var olup olmadığını kontrol et
                cursor.execute('SELECT id, channel_link FROM channels WHERE id = ?', (channel_id,))
                channel = cursor.fetchone()
                
                if not channel:
                    await self.edit_or_send_message(update, context, "❌ Kanal bulunamadı!")
                    return
                
                # İstek havuzundaki istekleri sil
                cursor.execute('DELETE FROM request_pool WHERE channel_id = ?', (channel_id,))
                deleted_requests = cursor.rowcount
                
                # Kanalı sil
                cursor.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
                deleted_channels = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Kanal silindi: ID={channel_id}, Link={channel[1]}, Silinen istekler={deleted_requests}")
            
            message = f"""
🗑️ **Kanal Başarıyla Silindi!**

✅ Kanal silindi: `{channel[1]}`
✅ Silinen istek sayısı: `{deleted_requests}`
✅ Toplam silinen kayıt: `{deleted_channels + deleted_requests}`

Kanal ve tüm istekleri veritabanından tamamen kaldırıldı.
            """
            
            # Kanallarım listesine dön
            await self.show_my_channels(update, context)
            
        except Exception as e:
            logger.error(f"Kanal silme hatası: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def refresh_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int) -> None:
        """Kanal verilerini yeniler"""
        try:
            # Kanallarım listesini yenile
            await self.show_my_channels(update, context)
            
        except Exception as e:
            logger.error(f"Kanal yenileme hatası: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def show_planned_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int) -> None:
        """Planlanan istekleri gösterir"""
        try:
            # Kanal bilgisini al
            channel = db_manager.get_channel(channel_id)
            if not channel:
                await self.edit_or_send_message(update, context, "❌ Kanal bulunamadı!")
                return
            
            # Planlanan istekleri al
            planned_requests = db_manager.get_planned_requests(channel_id, 10)
            
            if not planned_requests:
                message = f"""
📋 **Planlanan İstekler**

Kanal: `{channel['channel_link']}`

⚠️ Henüz planlanmış istek bulunmuyor.
                """
            else:
                message = f"""
📋 **Planlanan İstekler**

Kanal: `{channel['channel_link']}`
Toplam: {len(planned_requests)} istek

"""
                proxy_missing_count = 0
                for i, request in enumerate(planned_requests, 1):
                    scheduled_time = request['scheduled_time'][:19]
                    proxy_text = request.get('proxy_address') or '-'
                    if proxy_text == '-':
                        proxy_missing_count += 1
                        message += f"`{i}.` {scheduled_time} - {request['phone_number']} - ⚠️ PROXY YOK\n"
                    else:
                        message += f"`{i}.` {scheduled_time} - {request['phone_number']} - {proxy_text}\n"
                
                # Proxy uyarısı ekle
                if proxy_missing_count > 0:
                    message += f"\n⚠️ **Uyarı:** {proxy_missing_count} istek proxy olmadan çalışacak!\nProxy ayarlarından proxy yükleyin."
            
            # Yenile ve Geri dön butonları
            keyboard = [
                [InlineKeyboardButton("🔄 Yenile", callback_data=f"channel_planned_{channel_id}")],
                [InlineKeyboardButton("⬅️ Geri", callback_data="my_channels")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup)
            
        except Exception as e:
            logger.error(f"Planlanan istekler gösterilirken hata: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def show_global_pool(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Global havuzu gösterir"""
        try:
            # Global planlanan istekleri al
            global_requests = db_manager.get_global_planned_requests(30)
            
            if not global_requests:
                message = """
🌐 **Global Havuz**

⚠️ Henüz planlanmış istek bulunmuyor.

Tüm kanalların planlanan istekleri burada görüntülenir.
                """
            else:
                message = f"""
🌐 **Global Havuz**

Toplam: {len(global_requests)} planlanmış istek

"""
                proxy_missing_count = 0
                for i, request in enumerate(global_requests, 1):
                    scheduled_time = request['scheduled_time'][:19]
                    proxy_text = request.get('proxy_address') or '-'
                    if proxy_text == '-':
                        proxy_missing_count += 1
                        message += f"`{i}.` {scheduled_time} - {request['phone_number']} - {request['channel_link']} - ⚠️ PROXY YOK\n"
                    else:
                        message += f"`{i}.` {scheduled_time} - {request['phone_number']} - {request['channel_link']} - {proxy_text}\n"
                
                # Proxy uyarısı ekle
                if proxy_missing_count > 0:
                    message += f"\n⚠️ **Uyarı:** {proxy_missing_count} istek proxy olmadan çalışacak!\nProxy ayarlarından proxy yükleyin."
            
            # Ana menü butonu
            keyboard = [
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup)
            
        except Exception as e:
            logger.error(f"Global havuz gösterilirken hata: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def handle_repeat_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str) -> None:
        """Tekrar istek gönderme seçimini işler (mesaj handler için)"""
        user_id = str(update.effective_user.id)
        
        try:
            # Geçici veriyi al
            state, temp_data = db_manager.get_user_state(user_id)
            channel_link = temp_data.get('channel_link')
            total_requests = temp_data.get('total_requests')
            duration = temp_data.get('duration')
            
            # Kanalı veritabanına ekle
            channel_id = db_manager.add_channel(channel_link, total_requests, duration, user_id)
            
            if not channel_id:
                error_message = """
❌ **Kanal Eklenemedi!**

Kanal eklenirken bir hata oluştu. Lütfen tekrar deneyin.

Sorun devam ederse:
• Kanal linkinin doğru olduğundan emin olun
• Botu yeniden başlatın
• Destek ile iletişime geçin
                """
                
                keyboard = [
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.edit_or_send_message(update, context, error_message, reply_markup)
                return
            
            # Kullanıcı durumunu temizle
            db_manager.clear_user_state(user_id)
            
            # Başarı mesajı
            repeat_text = "Evet" if choice == "yes" else "Hayır"
            status_text = "✅ **Kanal Bilgileri Tamamlandı!**"
            action_text = "Kanal başarıyla eklendi."
            
            message = f"""
{status_text}

{action_text}

📺 **Kanal:** `{channel_link}`
📊 **İstek Sayısı:** `{total_requests}`
⏱️ **Süre:** `{duration}` dakika
🔄 **Tekrar İstek:** `{repeat_text}`

İstekler {duration} dakika içinde rastgele zamanlarda gönderilecek.

Başlatmak için aşağıdaki butona basın:
            """
            
            # Başlat ve Ana menü butonları
            keyboard = [
                [InlineKeyboardButton("🚀 Başlat", callback_data="start_requests")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup)
            
        except Exception as e:
            logger.error(f"Tekrar seçimi işlenirken hata: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    async def handle_repeat_choice_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str) -> None:
        """Tekrar istek gönderme seçimini işler (callback handler için)"""
        user_id = str(update.effective_user.id)
        
        try:
            # Geçici veriyi al
            state, temp_data = db_manager.get_user_state(user_id)
            channel_link = temp_data.get('channel_link')
            total_requests = temp_data.get('total_requests')
            duration = temp_data.get('duration')
            
            # Tekrar seçimini belirle
            allow_repeat = choice == "yes"
            
            # Kanalı veritabanına ekle
            channel_id = db_manager.add_channel(channel_link, total_requests, duration, user_id, allow_repeat)
            
            if not channel_id:
                error_message = """
❌ **Kanal Eklenemedi!**

Kanal eklenirken bir hata oluştu. Lütfen tekrar deneyin.

Sorun devam ederse:
• Kanal linkinin doğru olduğundan emin olun
• Botu yeniden başlatın
• Destek ile iletişime geçin
                """
                
                keyboard = [
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.edit_or_send_message(update, context, error_message, reply_markup)
                return
            
            # Kullanıcı durumunu temizle
            db_manager.clear_user_state(user_id)
            
            # Başarı mesajı
            repeat_text = "Evet" if choice == "yes" else "Hayır"
            status_text = "✅ **Kanal Bilgileri Tamamlandı!**"
            action_text = "Kanal başarıyla eklendi."
            
            message = f"""
{status_text}

{action_text}

📺 **Kanal:** `{channel_link}`
📊 **İstek Sayısı:** `{total_requests}`
⏱️ **Süre:** `{duration}` dakika
🔄 **Tekrar İstek:** `{repeat_text}`

İstekler {duration} dakika içinde rastgele zamanlarda gönderilecek.

Başlatmak için aşağıdaki butona basın:
            """
            
            # Başlat ve Ana menü butonları
            keyboard = [
                [InlineKeyboardButton("🚀 Başlat", callback_data="start_requests")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup)
            
        except Exception as e:
            logger.error(f"Tekrar seçimi işlenirken hata: {e}")
            await self.edit_or_send_message(update, context, f"❌ Hata oluştu: {str(e)}")
    
    def get_recent_logs(self, lines: int = 30) -> str:
        """Son N satır log'u döndürür"""
        try:
            import subprocess
            import os
            
            # Docker container'da mı çalışıyor kontrol et
            if os.path.exists('/.dockerenv'):
                # Docker container'da - log dosyası yok, konsol çıktısı kullan
                return "Docker container'da çalışıyor. Logları Coolify panelinden görüntüleyin.\n\nSon 30 log satırı için SSH ile VPS'e bağlanıp şu komutu çalıştırın:\n\ndocker logs --tail 30 $(docker ps --format '{{.Names}}' | grep python-app)"
            else:
                # Yerel - log dosyası varsa oku
                log_file = "bot.log"
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        all_lines = f.readlines()
                        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                        return ''.join(recent_lines)
                else:
                    return "Log dosyası bulunamadı."
                    
        except Exception as e:
            return f"Log okuma hatası: {e}"
    
    async def show_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Son logları gösterir"""
        try:
            logs = self.get_recent_logs(30)
            
            # Log çok uzunsa böl
            if len(logs) > 4000:
                logs = logs[-4000:] + "\n... (Son 30 satır)"
            
            message = f"📋 **Son 30 Log Satırı:**\n\n```\n{logs}\n```"
            
            # Geri butonu
            keyboard = [
                [InlineKeyboardButton("⬅️ Geri", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.edit_or_send_message(update, context, message, reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Log gösterimi hatası: {e}")
            await update.callback_query.answer("❌ Log gösterilemedi", show_alert=True)
    
    def run(self) -> None:
        """Botu çalıştırır"""
        logger.info("Bot başlatılıyor...")
        self.application.run_polling()

def main():
    """Ana fonksiyon"""
    try:
        # Bot'u oluştur ve çalıştır
        bot = TelegramBot()
        bot.run()
        
    except Exception as e:
        logger.error(f"Bot başlatılamadı: {e}")
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
