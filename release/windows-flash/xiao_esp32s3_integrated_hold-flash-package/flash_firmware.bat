@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo HOLD XIAO ESP32S3 一键刷机包
echo 目标固件: xiao_esp32s3_integrated_hold
echo ========================================
echo.
echo 请先确认:
echo 1. 板子已通过 USB 连接电脑
echo 2. 当前没有其他串口工具占用设备
echo.
echo 如首次刷写失败，请按以下方式重试:
echo - 按住 BOOT 再插 USB
echo - 或按住 BOOT 后点按一次 RESET
echo.

esptool.exe --chip esp32s3 --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 80m --flash_size 8MB 0x0 bootloader.bin 0x8000 partitions.bin 0xe000 boot_app0.bin 0x10000 firmware.bin

if errorlevel 1 (
    echo.
    echo [FAIL] 刷写失败。
    echo 建议检查:
    echo - USB 线是否支持数据传输
    echo - 是否有串口监视器占用端口
    echo - 是否已进入 BOOT 模式
    pause
    exit /b 1
)

echo.
echo [OK] 刷写完成。
echo 启动后可用串口查看启动标识:
echo [boot] xiao_esp32s3_integrated_hold hardware-first starting
pause
exit /b 0