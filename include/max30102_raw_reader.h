/*
 * 创建时间: 2026-05-23
 * 文件主要职责: 声明 MAX30102 原始 Red/IR 数据读取模块的对外接口。
 * 核心函数输入输出:
 * - begin(TwoWire&): 初始化 I2C 与 MAX30102，返回是否成功识别并配置设备。
 * - update(): 轮询 FIFO 并刷新最近一次样本状态。
 * - readLatestSample(...): 读取最近一次成功采集的样本。
 * 最后更改时间: 2026-05-23
 * 累加式更改日志:
 * - 2026-05-23: 新建 MAX30102 原始数据读取模块接口，服务于首轮原始数据验证。
 * 注意事项:
 * - 本模块当前只负责设备识别、基础配置和 Red/IR 原始数据读取，不负责心率或血氧计算。
 */

#pragma once

#include <Arduino.h>
#include <Wire.h>

class Max30102RawReader {
 public:
  struct DebugRegisters {
    uint8_t interruptStatus1 = 0;
    uint8_t interruptStatus2 = 0;
    uint8_t fifoConfig = 0;
    uint8_t modeConfig = 0;
    uint8_t spo2Config = 0;
    uint8_t led1PulseAmplitude = 0;
    uint8_t led2PulseAmplitude = 0;
    uint8_t multiLedConfig1 = 0;
    uint8_t multiLedConfig2 = 0;
  };

  struct Sample {
    uint32_t red = 0;
    uint32_t ir = 0;
    uint32_t sequence = 0;
    unsigned long capturedAtMs = 0;
  };

  bool begin(TwoWire& wire_bus);
  bool update();
  bool readLatestSample(Sample& sample) const;

  bool isInitialized() const;
  bool hasSeenSample() const;
  uint8_t deviceAddress() const;
  uint8_t partId() const;
  const char* lastError() const;
  uint8_t lastRegisterAddress() const;
  uint8_t lastWireTxStatus() const;
  uint8_t lastRequestedBytes() const;
  uint8_t lastReceivedBytes() const;
  uint8_t lastFifoWritePointer() const;
  uint8_t lastFifoReadPointer() const;
  uint8_t lastAvailableSamples() const;
  uint32_t registerReadFailCount() const;
  uint32_t fifoPointerReadFailCount() const;
  uint32_t fifoSampleReadFailCount() const;
  bool readDebugRegisters(DebugRegisters& debug_registers);

 private:
  bool resetDevice();
  bool configureDevice();
  bool clearFifo();
  bool readFifoSample(Sample& sample);
  bool readRegister(uint8_t reg, uint8_t& value);
  bool writeRegister(uint8_t reg, uint8_t value);

  TwoWire* wire_bus_ = nullptr;
  bool is_initialized_ = false;
  bool has_sample_ = false;
  uint8_t device_address_ = 0;
  uint8_t part_id_ = 0;
  const char* last_error_ = "not-started";
  uint8_t last_register_address_ = 0;
  uint8_t last_wire_tx_status_ = 0;
  uint8_t last_requested_bytes_ = 0;
  uint8_t last_received_bytes_ = 0;
  uint8_t last_fifo_write_pointer_ = 0;
  uint8_t last_fifo_read_pointer_ = 0;
  uint8_t last_available_samples_ = 0;
  uint32_t register_read_fail_count_ = 0;
  uint32_t fifo_pointer_read_fail_count_ = 0;
  uint32_t fifo_sample_read_fail_count_ = 0;
  Sample latest_sample_{};
};