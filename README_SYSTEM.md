# 🤖 Telegram Bot Sistemi

Bu sistem, Telegram hesapları ile kanallara otomatik katılım istekleri gönderen gelişmiş bir bot uygulamasıdır.

## 🏗️ Sistem Mimarisi

### 📁 Dosya Yapısı
```
TGDocker/
├── Docker/                 # Docker dosyaları
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── Sessions/               # Telegram session dosyaları
├── main.py                # Ana uygulama
├── telegram_bot.py        # Telegram bot sınıfı
├── database.py            # Veritabanı yönetimi
├── proxy_manager.py       # Proxy yönetimi
├── telethon_client.py     # Telethon client yönetimi
├── request_processor.py   # İstek işleme sistemi
├── config.py              # Bot konfigürasyonu
├── bot_config.json        # Bot ayarları
├── proxies.txt            # Proxy listesi
└── test_system.py         # Sistem test dosyası
```

## 🚀 Özellikler

### 🤖 Telegram Bot
- **Kanal Ekleme**: Kullanıcı dostu form sistemi
- **Session Yönetimi**: Otomatik session dosyası sayma
- **Admin Paneli**: Gelişmiş yönetim özellikleri
- **Navigasyon**: Ana Menü ve Geri butonları

### 🗄️ Veritabanı Sistemi
- **SQLite**: Hafif ve hızlı veritabanı
- **Kanal Yönetimi**: Kanal bilgileri ve ayarları
- **İstek Havuzu**: Planlanan isteklerin yönetimi
- **Hesap-Proxy İlişkisi**: Proxy atamaları

### 🌐 Proxy Yönetimi
- **Çoklu Proxy**: Birden fazla proxy desteği
- **Otomatik Dağıtım**: Hesaplara eşit dağıtım
- **Proxy Testi**: Bağlantı testleri
- **Yedek Proxy**: Başarısız proxy'ler için alternatif

### 📱 Telethon Entegrasyonu
- **Session Yönetimi**: Otomatik session açma/kapama
- **Proxy Desteği**: Her hesap için özel proxy
- **Hata Yönetimi**: Rate limit ve bağlantı hataları
- **Otomatik Temizlik**: Kullanılmayan client'ları temizleme

### ⚙️ İstek İşleme
- **Zamanlanmış İstekler**: Rastgele zaman dağılımı
- **Paralel İşleme**: Aynı anda birden fazla istek
- **Durum Takibi**: Bekliyor/Gönderildi/Atlandı
- **Otomatik İşleme**: Arka planda sürekli çalışma

## 📋 Kullanım

### 1. Kurulum
```bash
# Gereksinimleri yükle
pip install -r requirements.txt

# Test et
python test_system.py
```

### 2. Konfigürasyon
```bash
# Bot ayarlarını düzenle
python config_manager.py

# Proxy listesini düzenle
nano proxies.txt
```

### 3. Çalıştırma
```bash
# Yerel olarak
python main.py

# Docker ile
run.bat  # Windows
./run.sh # Linux/Mac
```

## 🔧 Konfigürasyon

### Bot Ayarları (`bot_config.json`)
```json
{
    "bot_api": "YOUR_BOT_TOKEN",
    "admin_ids": ["USER_ID_1", "USER_ID_2"],
    "webhook_url": "",
    "webhook_port": 8443,
    "debug_mode": true,
    "max_file_size": 20,
    "allowed_file_types": ["jpg", "jpeg", "png", "gif", "mp4", "mp3", "pdf", "txt", "doc", "docx"]
}
```

### Proxy Listesi (`proxies.txt`)
```
# Format: ip:port:username:password
192.168.1.100:8080
192.168.1.101:8080:user1:pass1
192.168.1.102:3128:user2:pass2
```

## 📊 Veritabanı Tabloları

### `channels` - Kanal Bilgileri
- `id`: Benzersiz ID
- `channel_link`: Kanal linki
- `total_requests`: Toplam istek sayısı
- `duration_minutes`: Süre (dakika)
- `user_id`: Kullanıcı ID
- `status`: Durum (active/inactive)

### `request_pool` - İstek Havuzu
- `id`: Benzersiz ID
- `channel_id`: Kanal ID
- `account_name`: Hesap adı (session dosyası)
- `scheduled_time`: Planlanan zaman
- `status`: Durum (Bekliyor/Gönderildi/Atlandı)
- `proxy_address`: Proxy adresi

### `accounts` - Hesap-Proxy İlişkisi
- `id`: Benzersiz ID
- `session_file`: Session dosyası adı
- `proxy_address`: Atanan proxy
- `proxy_type`: Proxy tipi (http/socks5)
- `is_active`: Aktif durumu

### `user_states` - Kullanıcı Durumları
- `user_id`: Kullanıcı ID
- `current_state`: Mevcut durum
- `temp_data`: Geçici veri (JSON)

## 🔄 İş Akışı

### 1. Kanal Ekleme
1. Kullanıcı "➕ Kanal Ekle" butonuna basar
2. Kanal linkini girer
3. İstek sayısını belirtir (1-1000)
4. Süreyi belirtir (1-1440 dakika)
5. "🚀 Başlat" butonuna basar

### 2. İstek Havuzu Oluşturma
1. Session dosyaları taranır
2. Proxy'ler yüklenir ve dağıtılır
3. İstekler rastgele zamanlara dağıtılır
4. Veritabanına kaydedilir

### 3. İstek İşleme
1. İstek işleyici sürekli çalışır
2. Bekleyen istekleri kontrol eder
3. Telethon client'ları oluşturur
4. Kanallara katılım istekleri gönderir
5. Sonuçları veritabanına kaydeder

## 🛠️ Geliştirme

### Test Etme
```bash
# Tüm sistemi test et
python test_system.py

# Sadece veritabanını test et
python database.py

# Sadece proxy'leri test et
python proxy_manager.py
```

### Log Takibi
```bash
# Detaylı loglar için
export LOG_LEVEL=DEBUG
python main.py
```

### Docker ile Geliştirme
```bash
# Container'ı oluştur ve çalıştır
docker-compose -f Docker/docker-compose.yml up --build

# Logları takip et
docker-compose -f Docker/docker-compose.yml logs -f
```

## 🔒 Güvenlik

### Session Dosyaları
- Session dosyaları `Sessions/` klasöründe saklanır
- Her dosya bir Telegram hesabını temsil eder
- Proxy ile güvenli bağlantı sağlanır

### Proxy Kullanımı
- Her hesap için özel proxy atanır
- Başarısız proxy'ler otomatik değiştirilir
- Proxy testleri düzenli olarak yapılır

### Rate Limiting
- Telegram API limitlerine uygun çalışır
- FloodWait hatalarını otomatik işler
- İstekler arasında güvenli aralıklar

## 📈 Performans

### Optimizasyonlar
- Paralel istek işleme
- Otomatik client temizliği
- Veritabanı indeksleri
- Proxy havuzu yönetimi

### Ölçeklenebilirlik
- Çoklu session desteği
- Sınırsız kanal ekleme
- Esnek proxy dağıtımı
- Modüler mimari

## 🐛 Sorun Giderme

### Yaygın Sorunlar

#### Session Dosyaları Bulunamıyor
```bash
# Sessions klasörünü kontrol et
ls -la Sessions/

# Test session oluştur
python test_sessions.py
```

#### Proxy Bağlantı Hatası
```bash
# Proxy dosyasını kontrol et
cat proxies.txt

# Proxy testi yap
python proxy_manager.py
```

#### Veritabanı Hatası
```bash
# Veritabanını sıfırla
rm telegram_bot.db
python database.py
```

### Log Analizi
```bash
# Hata loglarını filtrele
grep "ERROR" logs/bot.log

# İstek loglarını takip et
grep "İstek" logs/bot.log
```

## 📞 Destek

### Gereksinimler
- Python 3.11+
- SQLite3
- Telegram Bot Token
- Proxy listesi (opsiyonel)

### Bağımlılıklar
- python-telegram-bot
- telethon
- sqlalchemy
- aiohttp
- loguru

### Sistem Gereksinimleri
- RAM: 512MB minimum
- Disk: 100MB
- Ağ: Stabil internet bağlantısı
- OS: Windows/Linux/macOS

---

**Not**: Bu sistem eğitim amaçlıdır. Kullanımından doğacak sorumluluk kullanıcıya aittir.
