# Arduino IDE 独立验证路径

## 目的
本目录用于绕开当前 PlatformIO + ESP32-C6 Arduino 环境阻塞，直接使用 Arduino IDE 验证 MR60BHA2 套件是否能稳定输出呼吸、心率、距离和人体存在信息。

## 目录说明
- `mr60bha2_xiao_c6_validation/`：主验证草图，读取呼吸频率、心率、距离和相位信息。
- `mr60bha2_passthrough/`：串口透传草图，用于查看原始输出或配合官方升级工具做模块排查。

## 官方依据
- Seeed 官方 MR60BHA2 XIAO 套件文档给出了 Arduino IDE 安装步骤和 Breath Module 示例，核心调用为 `mmWave.begin(&mmWaveSerial)`、`mmWave.update(100)`、`getBreathRate()`、`getHeartRate()`、`getDistance()`、`isHumanDetected()`。
- `Seeed Arduino mmWave` 库的 `library.properties` 明确这是 Arduino 库，依赖 `Adafruit NeoPixel` 和 `hp_BH1750`。

## 建议安装步骤
1. 在 Arduino IDE 中安装开发板包 `esp32`，并选择 `Seeed XIAO ESP32C6`。
2. 安装库 `Seeed Arduino mmWave`。
3. 补装依赖库 `Adafruit NeoPixel` 和 `hp_BH1750`。
4. 打开 `mr60bha2_xiao_c6_validation/mr60bha2_xiao_c6_validation.ino`。
5. 选择正确端口，直接上传。
6. 以 `115200` 打开串口监视器。

## 预期结果
- 串口启动后会打印初始化日志。
- 在 1.5m 内单人静止场景下，应周期性看到 `breath_bpm`、`heart_bpm`、`distance_m` 等字段更新。
- 如果只有 `human=YES` 但呼吸/心率长期没有有效值，优先怀疑场景不符合官方建议，或模块固件版本较旧。

## 推荐验证顺序
1. 先跑主验证草图，确认是否有生命体征输出。
2. 若没有稳定输出，再跑透传草图，确认雷达 UART 是否有原始数据。
3. 若透传有数据但高层 API 无结果，再考虑按照 Seeed 官方文档升级模块固件。

## 风险与边界
- Seeed 官方明确提示，呼吸/心跳检测更适合睡眠或静止场景，不建议用桌前坐姿或运动状态评估精度。
- 官方同时说明算法和固件并不开源；更深层的检测参数与算法调整不适合在当前阶段自研替换。
- 该路径的目标是“先验证模块是否可用”，不是把毫米波立即并入现有 S3 主工程。