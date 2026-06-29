/*
 * 创建时间: 2026-06-05
 * 文件主要职责: 使用 MR60BHA2 自带 XIAO ESP32C6 复现 Seeed 官方 Arduino 呼吸心跳读取教程。
 * 核心函数输入输出:
 * - setup(): 初始化 USB 调试串口与 MR60BHA2 雷达串口，输出实验说明。
 * - loop(): 周期性读取人体存在、呼吸频率、心率、距离与相位信息，并输出串口日志。
 * 最后更改时间: 2026-06-05
 * 累加式更改日志:
 * - 2026-06-05: 新建独立实验入口，先验证 MR60BHA2 官方库在 PlatformIO + Arduino 下的可用性。
 * 注意事项:
 * - 本文件只服务于 `mr60bha2_xiao_c6_demo` 环境，不参与 XIAO ESP32S3 主工程编译。
 * - MR60BHA2 呼吸/心跳检测建议在 1.5m 内、单人、静止或睡眠类场景下验证。
 * - 官方库默认通过 UART 与雷达模块通信，套件板载连线通常无需额外改接。
 */

#include <Arduino.h>
#include <HardwareSerial.h>

#include "Seeed_Arduino_mmWave.h"

namespace {

constexpr uint32_t kDebugBaudRate = 115200;
constexpr uint32_t kRadarBaudRate = 115200;
constexpr uint32_t kSensorUpdateTimeoutMs = 100;
constexpr uint32_t kStatusLogIntervalMs = 1000;

HardwareSerial mmWaveSerial(0);
SEEED_MR60BHA2 mmWave;

unsigned long lastStatusLogAtMs = 0;

void printOptionalFloat(const char* label, bool valid, float value) {
  Serial.print(label);
  Serial.print('=');
  if (valid) {
    Serial.print(value, 2);
  } else {
    Serial.print("nan");
  }
  Serial.print(' ');
}

void logMr60bha2Sample(unsigned long nowMs) {
  const bool humanDetected = mmWave.isHumanDetected();

  float breathRate = 0.0f;
  const bool hasBreathRate = mmWave.getBreathRate(breathRate);

  float heartRate = 0.0f;
  const bool hasHeartRate = mmWave.getHeartRate(heartRate);

  float distance = 0.0f;
  const bool hasDistance = mmWave.getDistance(distance);

  float totalPhase = 0.0f;
  float breathPhase = 0.0f;
  float heartPhase = 0.0f;
  const bool hasPhases =
      mmWave.getHeartBreathPhases(totalPhase, breathPhase, heartPhase);

  Serial.print("[mr60bha2] up_ms=");
  Serial.print(nowMs);
  Serial.print(" human=");
  Serial.print(humanDetected ? "YES" : "NO");
  Serial.print(' ');
  printOptionalFloat("breath_bpm", hasBreathRate, breathRate);
  printOptionalFloat("heart_bpm", hasHeartRate, heartRate);
  printOptionalFloat("distance_m", hasDistance, distance);

  if (hasPhases) {
    printOptionalFloat("total_phase", true, totalPhase);
    printOptionalFloat("breath_phase", true, breathPhase);
    printOptionalFloat("heart_phase", true, heartPhase);
  } else {
    printOptionalFloat("total_phase", false, 0.0f);
    printOptionalFloat("breath_phase", false, 0.0f);
    printOptionalFloat("heart_phase", false, 0.0f);
  }

  Serial.println();
}

}  // namespace

void setup() {
  Serial.begin(kDebugBaudRate);
  delay(1000);

  Serial.println();
  Serial.println("[system] MR60BHA2 XIAO ESP32C6 demo starting");
  Serial.println("[system] Hold still within 1.5m for breath/heart validation");

  mmWaveSerial.begin(kRadarBaudRate);
  mmWave.begin(&mmWaveSerial);

  Serial.println("[system] MR60BHA2 library initialized");
}

void loop() {
  const unsigned long nowMs = millis();
  const bool updated = mmWave.update(kSensorUpdateTimeoutMs);

  if (!updated) {
    return;
  }

  if (nowMs - lastStatusLogAtMs < kStatusLogIntervalMs) {
    return;
  }

  lastStatusLogAtMs = nowMs;
  logMr60bha2Sample(nowMs);
}