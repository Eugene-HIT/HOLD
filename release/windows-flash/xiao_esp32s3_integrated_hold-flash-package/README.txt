HOLD XIAO ESP32S3 集成固件一键刷机包

版本说明:
- 已同步到 2026-07-05 当前本机实板验证可启动版本
- 当前版本包含启动阶段诊断日志，便于后续定位启动问题

目标环境:
- xiao_esp32s3_integrated_hold

包内文件说明:
- flash_firmware.bat: 双击执行的一键刷机脚本
- esptool.exe: 串口刷写工具
- bootloader.bin: 启动引导镜像
- partitions.bin: 分区表镜像
- boot_app0.bin: ESP32 启动辅助镜像
- firmware.bin: 主应用固件

推荐刷写步骤:
1. 用 USB 连接 XIAO ESP32S3
2. 双击 flash_firmware.bat
3. 若失败，按住 BOOT 再插 USB，或按住 BOOT 后点按 RESET，再重新双击脚本

刷写成功后的验证方式:
1. 打开串口监视器，115200 波特率
2. 观察是否打印:
   [boot] xiao_esp32s3_integrated_hold hardware-first starting
3. 如需进一步确认启动流程，可继续观察:
   [boot-stage] setup-complete

注意事项:
- 刷机时不要打开其他串口工具
- 若远端用户没有 PlatformIO，本包即可直接使用
- 本包用于串口刷写，不依赖 UF2 拖拽模式