# Python Docker Uygulaması

Bu proje, Python uygulamanızı Docker ile containerize etmek için hazırlanmıştır. Hem yerel bilgisayarınızda hem de VPS'te çalıştırabilirsiniz.

## 📁 Proje Yapısı

```
TGDocker/
├── Docker/                 # Docker dosyaları
│   ├── Dockerfile         # Docker image tanımı
│   ├── docker-compose.yml # Docker Compose konfigürasyonu
│   └── .dockerignore      # Docker ignore dosyası
├── main.py                # Ana Python uygulaması
├── requirements.txt       # Python bağımlılıkları
├── run.bat               # Windows çalıştırma scripti
├── run.sh                # Linux/Mac çalıştırma scripti
├── stop.bat              # Windows durdurma scripti
├── stop.sh               # Linux/Mac durdurma scripti
└── README.md             # Bu dosya
```

## 🚀 Kullanım

### Yerel Bilgisayarda Çalıştırma

**Windows:**
```bash
# Uygulamayı çalıştır
run.bat

# Uygulamayı durdur
stop.bat
```

**Linux/Mac:**
```bash
# Scriptlere çalıştırma izni ver
chmod +x run.sh stop.sh

# Uygulamayı çalıştır
./run.sh

# Uygulamayı durdur
./stop.sh
```

### Manuel Docker Komutları

```bash
# Docker Compose ile çalıştır
docker-compose -f Docker/docker-compose.yml up --build

# Arka planda çalıştır
docker-compose -f Docker/docker-compose.yml up -d --build

# Durdur
docker-compose -f Docker/docker-compose.yml down
```

## 🌐 Erişim

Uygulama çalıştıktan sonra:
- **Web arayüzü:** http://localhost:8000
- **Port:** 8000

## 📦 VPS'e Deploy

1. Projeyi VPS'e yükleyin:
```bash
git clone <your-repo-url>
cd TGDocker
```

2. Docker ve Docker Compose'u VPS'e yükleyin

3. Uygulamayı çalıştırın:
```bash
# Linux/Mac
./run.sh

# veya manuel
docker-compose -f Docker/docker-compose.yml up -d --build
```

## 🔧 Özelleştirme

### Python Bağımlılıkları
`requirements.txt` dosyasına ihtiyacınız olan paketleri ekleyin:
```txt
flask==2.3.3
requests==2.31.0
```

### Port Değiştirme
`Docker/docker-compose.yml` dosyasında port numarasını değiştirin:
```yaml
ports:
  - "8080:8000"  # 8080 portunu kullan
```

### Environment Variables
`Docker/docker-compose.yml` dosyasına environment variables ekleyin:
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - MY_VAR=my_value
```

## 🐛 Sorun Giderme

### Container çalışmıyor
```bash
# Logları kontrol et
docker-compose -f Docker/docker-compose.yml logs

# Container'ı yeniden oluştur
docker-compose -f Docker/docker-compose.yml up --build --force-recreate
```

### Port zaten kullanımda
```bash
# Kullanılan portları kontrol et
netstat -tulpn | grep :8000

# Farklı port kullan
docker-compose -f Docker/docker-compose.yml up -p 8080:8000
```

## 📝 Notlar

- Docker dosyaları `Docker/` klasöründe tutulmuştur
- Ana dizinde çalıştırma scriptleri bulunmaktadır
- Uygulama hem yerel hem VPS'te aynı şekilde çalışır
- Volume mount ile kod değişiklikleri anında yansır
