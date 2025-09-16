@echo off
echo ================================================
echo 🐳 Python Uygulaması Docker ile Çalıştırılıyor
echo ================================================
echo.

echo 📦 Docker image oluşturuluyor ve çalıştırılıyor...
docker-compose -f Docker/docker-compose.yml up --build

echo.
echo ✅ İşlem tamamlandı!
pause
