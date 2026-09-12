@echo off
chcp 65001 > nul
title AutoTraffic & SEO CTR Master
echo ========================================================
echo       🚀 ĐANG KHỞI CHẠY AUTOTRAFFIC & SEO CTR MASTER
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Chưa cài đặt Python trên máy tính! Vui lòng cài Python 3.10+ và thử lại.
    pause
    exit /b
)

echo [1/2] Đang kiểm tra thư viện...
pip install -r requirements.txt --quiet

echo [2/2] Đang mở giao diện phần mềm...
python app.py

pause
