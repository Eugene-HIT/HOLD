# HOLD 工程仓库

## 项目简介
本仓库用于承载 HOLD 智能挂坠的 PCB 硬件工程、嵌入式固件、整机联调、小程序与阶段性开发记录。

## PCB 工程已上传
HOLD 主板的嘉立创 EDA 专业版工程已归档到 [hardware/pcb/easyeda/Hold.eprj2](hardware/pcb/easyeda/Hold.eprj2)，可直接用于继续维护原理图和 PCB。

配套硬件资料位于 [hardware/pcb/](hardware/pcb/)：

- `easyeda/`：可编辑的嘉立创 EDA 专业版工程。
- `gerber/current/`：当前 Gerber 生产文件，下单前仍需完成 DRC、Gerber 预览和网络复核。
- `gerber/archive/`：历史下单文件，仅用于问题追溯，其中带 `DO_NOT_FABRICATE` 的文件禁止再次生产。
- `netlist/`：阶段性原理图网表。

本次归档重点补齐了 HOLD PCB 的可编辑源工程，后续硬件修改应以源工程为入口重新导出生产文件，不要直接修改或复用历史 Gerber。

当前重点包括：
- HOLD 主板与 PPG 子板的原理图、PCB 和生产资料维护
- XIAO ESP32S3 多传感器固件验证
- MAX30102、MPU6050/MPU6500、压力模块、DRV2605L 的独立探针与整机冒烟测试
- 呼吸/心率相关原始数据采集与日志导出
- 微信小程序调试页与用户页壳子
- 接线文档、开发日志和阶段性方案沉淀

## 当前工程结构
- 固件主工程：PlatformIO + Arduino，板卡以 `seeed_xiao_esp32s3` 为主
- 传感器与算法公共头文件：`include/`
- 各独立实验入口与整机测试入口：`src/`
- 接线文档与方案说明：`docs/`
- 开发日志与阶段记录：`log/`
- 小程序与云函数：`web/`
- 串口采集与辅助脚本：`tools/`
- PCB 源工程与生产资料：`hardware/pcb/`

## 当前实现范围
- 独立环境：MPU6050/MPU6500 探针、单 IMU 呼吸实验、MAX30102 指尖/胸口环境、DRV2605L LRA 环境、BLE 按键链路环境
- 整机环境：IMU + PPG + 压力 + DRV2605L + 热反馈 PWM + RGB 流水灯的统一冒烟测试
- 诊断能力：I2C 地址可见性、启动阶段日志、RGB 单色自检、兼容 `MPU6500/MPU9250` 系列 IMU 识别

## MR60BHA2 当前建议
- XIAO ESP32C6 + MR60BHA2 的首轮验证暂时改走 Arduino IDE 独立草图路径，避免继续受 PlatformIO 的 ESP32-C6 Arduino 环境问题阻塞。
- 可直接使用 [arduino/README.md](arduino/README.md) 中的验证步骤与草图。

## 推荐使用方式
1. 在 HOLD 根目录执行 `pio run` 进行编译。
2. 连接开发板后执行 `pio run -t upload` 进行烧录。
3. 执行 `pio device monitor -b 115200` 查看串口日志。

## 串口日志预期
- 上电或复位后会先输出一组启动信息。
- 随后每次 LED 翻转都会输出一行日志，包含运行毫秒数和当前 LED 状态。
- 如果打开监视器时没有看到启动日志，按一下开发板 Reset 键即可重新看到完整启动过程。

## 烧录异常排查
- 如果串口口号未出现，先更换数据线并重新插拔开发板。
- 如果上传失败，可按住 BOOT 键接入 USB 进入 BootLoader 模式后重新烧录。
- 如果点灯逻辑与观察结果相反，优先检查是否误用了外接 LED，而不是板载用户灯。

## 待确认项
- 当前仓库开发指南提到 Plus 版本，但本工程先按通用 XIAO ESP32S3 板卡配置建立。
- 若你的实际硬件为 XIAO ESP32S3 Plus，后续建议补充 Flash 容量与分区配置验证。
