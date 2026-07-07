/*
 * 创建时间: 2026-07-05
 * 文件主要职责: 提供一个与主工程解耦的 XIAO ESP32S3 恢复探针固件，用于确认板卡基础启动、USB CDC 串口与板载用户灯是否正常。
 * 核心函数输入输出:
 * - setup(): 初始化串口与板载用户灯，输出恢复探针启动标识。
 * - loop(): 周期性翻转板载用户灯，并输出当前运行计数，便于确认固件正在持续运行。
 * 最后更改时间: 2026-07-05
 * 累加式更改日志:
 * - 2026-07-05: 新增独立恢复探针环境，避免主工程依赖与外设状态干扰板卡恢复判断。
 * 注意事项:
 * - XIAO ESP32S3 板载用户灯为低电平点亮，因此 HIGH/LOW 与视觉亮灭相反。
 * - 本文件只用于恢复与基础连通性验证，不承载业务逻辑。
 */

#include <Arduino.h>

namespace {

constexpr uint8_t kUserLedPin = 21;
constexpr unsigned long kBlinkIntervalMs = 500;

bool ledOn = false;
unsigned long lastToggleAtMs = 0;
unsigned long bootCounter = 0;

void applyLedState(bool on) {
  digitalWrite(kUserLedPin, on ? LOW : HIGH);
}

}  // namespace

void setup() {
  pinMode(kUserLedPin, OUTPUT);
  applyLedState(false);

  Serial.begin(115200);
  delay(1200);
  Serial.println("[recovery] xiao_esp32s3_recovery_probe booted");
  Serial.println("[recovery] LED will toggle every 500ms");
}

void loop() {
  const unsigned long nowMs = millis();
  if (nowMs - lastToggleAtMs < kBlinkIntervalMs) {
    return;
  }

  lastToggleAtMs = nowMs;
  ledOn = !ledOn;
  applyLedState(ledOn);
  ++bootCounter;

  Serial.print("[recovery] tick=");
  Serial.print(bootCounter);
  Serial.print(" led=");
  Serial.println(ledOn ? "ON" : "OFF");
}