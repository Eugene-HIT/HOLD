/*
 * 创建时间: 2026-05-23
 * 文件主要职责: 实现 MAX30102 的基础寄存器配置、FIFO 轮询与原始 Red/IR 数据读取。
 * 核心函数输入输出:
 * - begin(TwoWire&): 识别 0x57 设备、校验 Part ID、完成基础配置。
 * - update(): 从 FIFO 读取最新样本并更新内部缓存。
 * - readFifoSample(...): 将 6 字节 FIFO 数据拼接为 18 位有效 Red/IR 原始值。
 * 最后更改时间: 2026-05-23
 * 累加式更改日志:
 * - 2026-05-23: 新建 MAX30102 原始读取实现，支持最小可运行的设备识别与串口数据验证。
 * 注意事项:
 * - 当前配置目标是“先稳定读到原始数据”，因此参数选择偏保守，不追求极限吞吐。
 * - FIFO 读取按 Red + IR 模式处理，每次样本总计 6 字节。
 */

#include "max30102_raw_reader.h"

#include "project_config.h"

namespace {

constexpr uint8_t kRegisterInterruptStatus1 = 0x00;
constexpr uint8_t kRegisterInterruptStatus2 = 0x01;
constexpr uint8_t kRegisterFifoWritePointer = 0x04;
constexpr uint8_t kRegisterOverflowCounter = 0x05;
constexpr uint8_t kRegisterFifoReadPointer = 0x06;
constexpr uint8_t kRegisterFifoData = 0x07;
constexpr uint8_t kRegisterFifoConfig = 0x08;
constexpr uint8_t kRegisterModeConfig = 0x09;
constexpr uint8_t kRegisterSpo2Config = 0x0A;
constexpr uint8_t kRegisterLed1PulseAmplitude = 0x0C;
constexpr uint8_t kRegisterLed2PulseAmplitude = 0x0D;
constexpr uint8_t kRegisterMultiLedConfig1 = 0x11;
constexpr uint8_t kRegisterMultiLedConfig2 = 0x12;
constexpr uint8_t kRegisterPartId = 0xFF;

constexpr uint8_t kModeReset = 0x40;
constexpr uint8_t kModeSpO2 = 0x03;
constexpr uint8_t kMask18Bit = 0x03;

}  // namespace

bool Max30102RawReader::begin(TwoWire& wire_bus) {
  wire_bus_ = &wire_bus;
  device_address_ = project_config::kMax30102Address;
  last_error_ = "beginning";
  is_initialized_ = false;
  has_sample_ = false;

  uint8_t part_id = 0;
  if (!readRegister(kRegisterPartId, part_id)) {
    last_error_ = "part-id-read-failed";
    return false;
  }

  part_id_ = part_id;
  if (part_id_ != project_config::kExpectedMax30102PartId) {
    last_error_ = "unexpected-part-id";
    return false;
  }

  if (!resetDevice()) {
    last_error_ = "reset-failed";
    return false;
  }

  if (!configureDevice()) {
    last_error_ = "config-failed";
    return false;
  }

  if (!clearFifo()) {
    last_error_ = "fifo-clear-failed";
    return false;
  }

  is_initialized_ = true;
  last_error_ = "ok";
  return true;
}

bool Max30102RawReader::update() {
  if (!is_initialized_) {
    return false;
  }

  uint8_t write_pointer = 0;
  uint8_t read_pointer = 0;
  if (!readRegister(kRegisterFifoWritePointer, write_pointer) ||
      !readRegister(kRegisterFifoReadPointer, read_pointer)) {
    ++fifo_pointer_read_fail_count_;
    last_error_ = "fifo-pointer-read-failed";
    return false;
  }

  last_fifo_write_pointer_ = write_pointer;
  last_fifo_read_pointer_ = read_pointer;

  const uint8_t available_samples = (write_pointer - read_pointer) & 0x1F;
  last_available_samples_ = available_samples;
  if (available_samples == 0) {
    return false;
  }

  Sample sample;
  bool read_any = false;
  for (uint8_t index = 0; index < available_samples; ++index) {
    if (!readFifoSample(sample)) {
      ++fifo_sample_read_fail_count_;
      last_error_ = "fifo-sample-read-failed";
      return false;
    }
    read_any = true;
  }

  if (read_any) {
    latest_sample_ = sample;
    has_sample_ = true;
    last_error_ = "ok";
  }

  return read_any;
}

bool Max30102RawReader::readLatestSample(Sample& sample) const {
  if (!has_sample_) {
    return false;
  }

  sample = latest_sample_;
  return true;
}

bool Max30102RawReader::isInitialized() const {
  return is_initialized_;
}

bool Max30102RawReader::hasSeenSample() const {
  return has_sample_;
}

uint8_t Max30102RawReader::deviceAddress() const {
  return device_address_;
}

uint8_t Max30102RawReader::partId() const {
  return part_id_;
}

const char* Max30102RawReader::lastError() const {
  return last_error_;
}

uint8_t Max30102RawReader::lastRegisterAddress() const {
  return last_register_address_;
}

uint8_t Max30102RawReader::lastWireTxStatus() const {
  return last_wire_tx_status_;
}

uint8_t Max30102RawReader::lastRequestedBytes() const {
  return last_requested_bytes_;
}

uint8_t Max30102RawReader::lastReceivedBytes() const {
  return last_received_bytes_;
}

uint8_t Max30102RawReader::lastFifoWritePointer() const {
  return last_fifo_write_pointer_;
}

uint8_t Max30102RawReader::lastFifoReadPointer() const {
  return last_fifo_read_pointer_;
}

uint8_t Max30102RawReader::lastAvailableSamples() const {
  return last_available_samples_;
}

uint32_t Max30102RawReader::registerReadFailCount() const {
  return register_read_fail_count_;
}

uint32_t Max30102RawReader::fifoPointerReadFailCount() const {
  return fifo_pointer_read_fail_count_;
}

uint32_t Max30102RawReader::fifoSampleReadFailCount() const {
  return fifo_sample_read_fail_count_;
}

bool Max30102RawReader::readDebugRegisters(DebugRegisters& debug_registers) {
  if (!is_initialized_) {
    return false;
  }

  return readRegister(kRegisterInterruptStatus1, debug_registers.interruptStatus1) &&
         readRegister(kRegisterInterruptStatus2, debug_registers.interruptStatus2) &&
         readRegister(kRegisterFifoConfig, debug_registers.fifoConfig) &&
         readRegister(kRegisterModeConfig, debug_registers.modeConfig) &&
         readRegister(kRegisterSpo2Config, debug_registers.spo2Config) &&
         readRegister(kRegisterLed1PulseAmplitude, debug_registers.led1PulseAmplitude) &&
         readRegister(kRegisterLed2PulseAmplitude, debug_registers.led2PulseAmplitude) &&
         readRegister(kRegisterMultiLedConfig1, debug_registers.multiLedConfig1) &&
         readRegister(kRegisterMultiLedConfig2, debug_registers.multiLedConfig2);
}

bool Max30102RawReader::resetDevice() {
  if (!writeRegister(kRegisterModeConfig, kModeReset)) {
    return false;
  }

  const unsigned long reset_start_ms = millis();
  uint8_t mode_config = 0;
  while ((millis() - reset_start_ms) < 100) {
    if (!readRegister(kRegisterModeConfig, mode_config)) {
      return false;
    }
    if ((mode_config & kModeReset) == 0) {
      return true;
    }
    delay(5);
  }

  return false;
}

bool Max30102RawReader::configureDevice() {
  if (!writeRegister(kRegisterFifoConfig, 0x5F)) {
    return false;
  }

  if (!writeRegister(kRegisterModeConfig, kModeSpO2)) {
    return false;
  }

  if (!writeRegister(kRegisterSpo2Config, 0x27)) {
    return false;
  }

  if (!writeRegister(
          kRegisterLed1PulseAmplitude,
          project_config::kMax30102LedRedPulseAmplitude)) {
    return false;
  }

  if (!writeRegister(
          kRegisterLed2PulseAmplitude,
          project_config::kMax30102LedIrPulseAmplitude)) {
    return false;
  }

  if (!writeRegister(kRegisterMultiLedConfig1, 0x21)) {
    return false;
  }

  if (!writeRegister(kRegisterMultiLedConfig2, 0x00)) {
    return false;
  }

  uint8_t ignored = 0;
  readRegister(kRegisterInterruptStatus1, ignored);
  readRegister(kRegisterInterruptStatus2, ignored);
  return true;
}

bool Max30102RawReader::clearFifo() {
  return writeRegister(kRegisterFifoWritePointer, 0x00) &&
         writeRegister(kRegisterOverflowCounter, 0x00) &&
         writeRegister(kRegisterFifoReadPointer, 0x00);
}

bool Max30102RawReader::readFifoSample(Sample& sample) {
  last_register_address_ = kRegisterFifoData;
  last_requested_bytes_ = 6;
  last_received_bytes_ = 0;
  wire_bus_->beginTransmission(device_address_);
  wire_bus_->write(kRegisterFifoData);
  last_wire_tx_status_ = wire_bus_->endTransmission(false);
  if (last_wire_tx_status_ != 0) {
    return false;
  }

  const uint8_t expected_bytes = 6;
  const uint8_t received_bytes = wire_bus_->requestFrom(device_address_, expected_bytes);
  last_received_bytes_ = received_bytes;
  if (received_bytes != expected_bytes) {
    return false;
  }

  uint8_t raw_bytes[expected_bytes];
  for (uint8_t index = 0; index < expected_bytes; ++index) {
    raw_bytes[index] = wire_bus_->read();
  }

  sample.red =
      ((static_cast<uint32_t>(raw_bytes[0] & kMask18Bit) << 16) |
       (static_cast<uint32_t>(raw_bytes[1]) << 8) |
       static_cast<uint32_t>(raw_bytes[2])) & 0x3FFFF;
  sample.ir =
      ((static_cast<uint32_t>(raw_bytes[3] & kMask18Bit) << 16) |
       (static_cast<uint32_t>(raw_bytes[4]) << 8) |
       static_cast<uint32_t>(raw_bytes[5])) & 0x3FFFF;
  sample.sequence = latest_sample_.sequence + 1;
  sample.capturedAtMs = millis();
  return true;
}

bool Max30102RawReader::readRegister(uint8_t reg, uint8_t& value) {
  last_register_address_ = reg;
  last_requested_bytes_ = 1;
  last_received_bytes_ = 0;
  wire_bus_->beginTransmission(device_address_);
  wire_bus_->write(reg);
  last_wire_tx_status_ = wire_bus_->endTransmission(false);
  if (last_wire_tx_status_ != 0) {
    ++register_read_fail_count_;
    return false;
  }

  last_received_bytes_ = wire_bus_->requestFrom(device_address_, static_cast<uint8_t>(1));
  if (last_received_bytes_ != 1) {
    ++register_read_fail_count_;
    return false;
  }

  value = wire_bus_->read();
  return true;
}

bool Max30102RawReader::writeRegister(uint8_t reg, uint8_t value) {
  last_register_address_ = reg;
  last_requested_bytes_ = 2;
  last_received_bytes_ = 0;
  wire_bus_->beginTransmission(device_address_);
  wire_bus_->write(reg);
  wire_bus_->write(value);
  last_wire_tx_status_ = wire_bus_->endTransmission();
  return last_wire_tx_status_ == 0;
}