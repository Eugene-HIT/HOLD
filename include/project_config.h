/*
 * 创建时间: 2026-05-22
 * 文件主要职责: 集中管理 XIAO ESP32S3 当前工程的板级参数、MAX30102 验证参数与 ICS43434 麦克风参数。
 * 核心函数输入输出: 本文件仅提供常量定义，供主程序和传感器模块读取引脚、节拍、地址与采样配置。
 * 最后更改时间: 2026-06-09
 * 累加式更改日志:
 * - 2026-05-22: 新建板级配置头文件，定义板载用户灯引脚和闪烁周期。
 * - 2026-05-22: 随 PlatformIO 工程一起移动到 HOLD 根目录。
 * - 2026-05-23: 补充 MAX30102 原始数据读取所需的 I2C 引脚、地址与日志节拍配置。
 * - 2026-05-25: 补充 ICS43434 麦克风 I2S 引脚、采样率、批处理与日志节拍配置。
 * - 2026-06-09: 补充单 IMU 呼吸实验的 VOFA 调试开关与输出节拍配置。
 * 注意事项:
 * - XIAO ESP32S3 系列板载用户灯为低电平点亮。
 * - 当前 I2C 引脚按 Seeed 官方 XIAO ESP32S3 默认功能使用 D4(GPIO5)/D5(GPIO6)。
 */

#pragma once

#include <Arduino.h>

namespace project_config {

constexpr uint8_t kUserLedPin = 21;
constexpr uint8_t kLedOnLevel = LOW;
constexpr uint8_t kLedOffLevel = HIGH;
constexpr unsigned long kBlinkIntervalMs = 250;
constexpr unsigned long kSerialReadyTimeoutMs = 2000;

constexpr uint8_t kI2cSdaPin = 5;
constexpr uint8_t kI2cSclPin = 6;
constexpr uint32_t kI2cClockHz = 100000;
constexpr uint8_t kMax30102Address = 0x57;
constexpr uint8_t kExpectedMax30102PartId = 0x15;

constexpr uint16_t kSensorAdcSampleRateHz = 100;
constexpr uint8_t kFifoSampleAverage = 4;
constexpr uint16_t kSensorEffectiveSampleRateHz =
	kSensorAdcSampleRateHz / kFifoSampleAverage;
constexpr unsigned long kSensorPollIntervalMs = 10;
constexpr unsigned long kHeartRateLogIntervalMs = 500;
constexpr bool kEnableHeartRateStatusLog = false;
constexpr bool kEnableMax30102VofaStream = true;
constexpr unsigned long kMax30102VofaStreamIntervalMs = kSensorPollIntervalMs;
constexpr float kMax30102VofaFilteredDisplayGain = 4.0f;
constexpr unsigned long kStartupDelayMs = 300;

constexpr int8_t kMicrophoneBclkPin = 7;
constexpr int8_t kMicrophoneWsPin = 8;
constexpr int8_t kMicrophoneDataPin = 9;
constexpr uint32_t kMicrophoneSampleRateHz = 16000;
constexpr size_t kMicrophoneBatchSampleCount = 160;
constexpr size_t kMicrophoneDmaBufferCount = 4;
constexpr size_t kMicrophoneDmaBufferLength = 256;
constexpr unsigned long kMicrophonePollIntervalMs = kSensorPollIntervalMs;
constexpr unsigned long kMicrophoneLogIntervalMs = kHeartRateLogIntervalMs;

constexpr uint8_t kPressureAdcPin = 1;
constexpr uint8_t kPressureAdcResolutionBits = 12;
constexpr size_t kPressureBaselineSampleCount = 32;
constexpr size_t kPressureAverageSampleCount = 8;
constexpr uint16_t kPressureMinimumRangeRaw = 300;
constexpr unsigned long kPressurePollIntervalMs = kSensorPollIntervalMs;
constexpr unsigned long kPressureLogIntervalMs = kHeartRateLogIntervalMs;

constexpr uint8_t kAd8232AdcPin = 2;
constexpr uint8_t kAd8232AdcResolutionBits = 12;
constexpr unsigned long kAd8232PollIntervalMs = 4;
constexpr unsigned long kAd8232LogIntervalMs = 100;
constexpr bool kEnableAd8232VofaStream = false;
constexpr unsigned long kAd8232VofaStreamIntervalMs = kAd8232PollIntervalMs;

constexpr bool kEnableMpu6050RespirationVofaStream = true;
constexpr unsigned long kMpu6050RespirationVofaStreamIntervalMs = 20;

constexpr uint32_t kFingerPresentIrMeanThreshold = 8000;
constexpr uint32_t kFingerPresentRedMeanThreshold = 2000;
constexpr uint8_t kMax30102LedRedPulseAmplitude = 0x3C;
constexpr uint8_t kMax30102LedIrPulseAmplitude = 0x3C;
constexpr float kHeartRateDcAlpha = 0.05f;
constexpr float kHeartRateSignalAlpha = 0.20f;
constexpr float kHeartRateAmplitudeMin = 120.0f;
constexpr unsigned long kHeartRateBeatIntervalMinMs = 300;
constexpr unsigned long kHeartRateBeatIntervalMaxMs = 2000;
constexpr unsigned long kHeartRateBeatStaleTimeoutMs = 2500;
constexpr unsigned long kHeartRateFingerLossResetMs = 1500;

}  // namespace project_config
