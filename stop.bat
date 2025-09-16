@echo off
echo ================================================
echo 🛑 Docker Container Durduruluyor
echo ================================================
echo.

echo 🛑 Container durduruluyor...
docker-compose -f Docker/docker-compose.yml down

echo.
echo ✅ Container durduruldu!
pause
