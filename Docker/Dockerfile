# Python 3.11 slim image kullanıyoruz
FROM python:3.11-slim

# Çalışma dizinini ayarlıyoruz
WORKDIR /app

# Sistem paketlerini güncelliyoruz ve gerekli paketleri yüklüyoruz
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyalıyoruz
COPY requirements.txt .

# Python paketlerini yüklüyoruz
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyalıyoruz
COPY . .

# Port 8000'i expose ediyoruz
EXPOSE 8000

# Uygulamayı çalıştırıyoruz
CMD ["python", "main.py"]
