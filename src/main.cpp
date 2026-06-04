/*
 * 创建时间: 2026-05-22
 * 文件主要职责: 驱动 XIAO ESP32S3 接入 MAX30102 与 ICS43434，并输出原始数据与最小状态日志。
 * 核心函数输入输出:
 * - setup(): 初始化串口、板载 LED、I2C、MAX30102 与 ICS43434，输出启动和识别日志。
 * - loop(): 并行轮询 MAX30102 与 ICS43434，并按约 2Hz 输出麦克风状态与可选心率状态。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-22: 新建最小点灯测试程序，使用非阻塞节拍控制板载 LED 闪烁。
 * - 2026-05-22: 随 PlatformIO 工程一起移动到 HOLD 根目录。
 * - 2026-05-22: 增强串口日志可见性，补充启动等待和时间戳输出。
 * - 2026-05-23: 切换为 MAX30102 原始数据读取验证程序，增加 I2C 初始化、设备识别与 FIFO 原始数据打印。
 * - 2026-05-23: 增加最小心率估计模块，基于 IR 去直流、轻度平滑与节拍间隔计算 BPM。
 * - 2026-05-25: 新增 ICS43434 麦克风原始读取模块，并按与心率状态一致的节拍输出串口统计行。
 * - 2026-05-25: 暂时关闭心率状态行输出，优先降低串口噪声并观察麦克风状态。
 * 注意事项:
 * - 板载用户灯为低电平点亮，因此输出电平与视觉状态相反。
 * - 当前 BPM 仅用于静止场景下的工程验证，不作为医学级结果。
 * - 当前麦克风状态行只用于确认 I2S 采样链路是否已跑通，不作为音频算法结论。
 */

#include <Arduino.h>
#include <Wire.h>

#include "ad8232_raw_reader.h"
#include "heart_rate_estimator.h"
#include "ics43434_raw_reader.h"
#include "max30102_raw_reader.h"
#include "pressure_film_raw_reader.h"
#include "project_config.h"

namespace {

bool ledIsOn = false;
bool sensorReady = false;
bool microphoneReady = false;
unsigned long lastToggleAtMs = 0;
unsigned long lastSensorPollAtMs = 0;
unsigned long lastHeartRateLogAtMs = 0;
unsigned long lastSensorStatusLogAtMs = 0;
unsigned long lastI2cRescanAtMs = 0;
unsigned long lastMicrophonePollAtMs = 0;
unsigned long lastMicrophoneLogAtMs = 0;
unsigned long lastMicrophoneStatusLogAtMs = 0;
unsigned long lastMicrophoneRetryAtMs = 0;
unsigned long lastPressurePollAtMs = 0;
unsigned long lastPressureLogAtMs = 0;
unsigned long lastAd8232PollAtMs = 0;
unsigned long lastAd8232LogAtMs = 0;
uint32_t lastProcessedSequence = 0;

Max30102RawReader max30102;
HeartRateEstimator heartRateEstimator;
Ics43434RawReader microphone;
PressureFilmRawReader pressureSensor;
Ad8232RawReader ad8232;

bool isAnyVofaStreamEnabled() {
  return project_config::kEnableAd8232VofaStream ||
         project_config::kEnableMax30102VofaStream;
}

void logLedState(const char* reason) {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Serial.print("[system] ");
  Serial.print(reason);
  Serial.print(" | uptime=");
  Serial.print(millis());
  Serial.print("ms | led=");
  Serial.println(ledIsOn ? "ON" : "OFF");
}

void logMax30102WiringGuide() {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Serial.println("[wiring] XIAO 3V3 -> MAX30102 VIN");
  Serial.println("[wiring] XIAO GND -> MAX30102 GND");
  Serial.println("[wiring] XIAO D4(GPIO5/SDA) -> MAX30102 SDA");
  Serial.println("[wiring] XIAO D5(GPIO6/SCL) -> MAX30102 SCL");
}

void logMicrophoneWiringGuide() {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Serial.println("[wiring] XIAO 3V3 -> ICS43434 3V/VIN");
  Serial.println("[wiring] XIAO GND -> ICS43434 GND");
  Serial.println("[wiring] XIAO D8(GPIO7) -> ICS43434 BCLK/SCK");
  Serial.println("[wiring] XIAO D9(GPIO8) -> ICS43434 WS/LRCL");
  Serial.println("[wiring] XIAO D10(GPIO9) -> ICS43434 DOUT/SD");
  Serial.println("[wiring] XIAO GND -> ICS43434 SEL/LR");
}

void logPressureWiringGuide() {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Serial.println("[wiring] XIAO 3V3 -> 薄膜压力模块 VCC");
  Serial.println("[wiring] XIAO GND -> 薄膜压力模块 GND");
  Serial.println("[wiring] XIAO D0/A0(GPIO1) -> 薄膜压力模块 AO");
  Serial.println("[wiring] 薄膜压力模块 DO 本阶段先不接");
}

void logAd8232WiringGuide() {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Serial.println("[wiring] XIAO 3V3 -> AD8232 3.3v");
  Serial.println("[wiring] XIAO GND -> AD8232 GND");
  Serial.println("[wiring] XIAO D1/A1(GPIO2) -> AD8232 OUTPUT");
  Serial.println("[wiring] XIAO 3V3 -> AD8232 SDN");
  Serial.println("[wiring] AD8232 LO+/LO- 本阶段可先不接");
}

bool scanI2cBus() {
  bool foundAny = false;
  for (uint8_t address = 1; address < 0x7F; ++address) {
    Wire.beginTransmission(address);
    const uint8_t result = Wire.endTransmission();
    if (result != 0) {
      continue;
    }

    foundAny = true;
    Serial.print("[i2c-scan] found device at 0x");
    if (address < 0x10) {
      Serial.print('0');
    }
    Serial.println(address, HEX);
  }

  if (!foundAny) {
    Serial.println("[i2c-scan] no i2c device found on current SDA/SCL pins");
  }

  return foundAny;
}

void logHeartRateStatus(const Max30102RawReader::Sample& sample) {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  char bpmText[16];
  if (heartRateEstimator.hasValidBpm()) {
    snprintf(bpmText, sizeof(bpmText), "%6.1f", heartRateEstimator.bpm());
  } else {
    snprintf(bpmText, sizeof(bpmText), "%6s", "calc");
  }

  Serial.printf(
      "[hr] seq=%-5lu | up=%-6lums | finger=%-3s | bpm=%6s | int=%-4lums | amp=%8.1f | red=%-6lu | ir=%-6lu | avg_r=%-6lu | avg_i=%-6lu | filt=%9.1f | beats=%-4lu\n",
      static_cast<unsigned long>(sample.sequence),
      sample.capturedAtMs,
      heartRateEstimator.fingerPresent() ? "YES" : "NO",
      bpmText,
      heartRateEstimator.lastBeatIntervalMs(),
      heartRateEstimator.signalAmplitude(),
      static_cast<unsigned long>(sample.red),
      static_cast<unsigned long>(sample.ir),
      static_cast<unsigned long>(heartRateEstimator.averageRed()),
      static_cast<unsigned long>(heartRateEstimator.averageIr()),
      heartRateEstimator.filteredIr(),
      static_cast<unsigned long>(heartRateEstimator.beatCount()));
}

void logMicrophoneStatus(unsigned long nowMs) {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Ics43434RawReader::WindowSummary summary;
  if (!microphone.readWindowSummary(summary)) {
    Serial.printf(
        "[mic] up=%-6lums | state=%-9s | err=%-12s | total=%-7llu | empty=%-4lu | bytes=%-4u\n",
        nowMs,
        microphoneReady ? "idle" : "init-fail",
        microphone.lastError(),
        microphone.totalSamplesRead(),
        static_cast<unsigned long>(microphone.emptyReadCount()),
        static_cast<unsigned>(microphone.lastBytesRead()));
    return;
  }

  Serial.printf(
      "[mic] seq=%-5lu | up=%-6lums | batches=%-3u | samples=%-5u | min=%-8ld | max=%-8ld | p2p=%-8lu | mean=%-7lu\n",
      static_cast<unsigned long>(summary.lastSequence),
      summary.lastUpdatedAtMs,
      static_cast<unsigned>(summary.batchCount),
      static_cast<unsigned>(summary.sampleCount),
      static_cast<long>(summary.minSample),
      static_cast<long>(summary.maxSample),
      static_cast<unsigned long>(summary.peakToPeak),
      static_cast<unsigned long>(summary.meanAbs));
}

void logReaderDebug(const char* reason) {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Serial.print("[sensor-debug] reason=");
  Serial.print(reason);
  Serial.print(" | last_error=");
  Serial.print(max30102.lastError());
  Serial.print(" | reg=0x");
  if (max30102.lastRegisterAddress() < 0x10) {
    Serial.print('0');
  }
  Serial.print(max30102.lastRegisterAddress(), HEX);
  Serial.print(" | tx_status=");
  Serial.print(max30102.lastWireTxStatus());
  Serial.print(" | req=");
  Serial.print(max30102.lastRequestedBytes());
  Serial.print(" | got=");
  Serial.print(max30102.lastReceivedBytes());
  Serial.print(" | wr_ptr=");
  Serial.print(max30102.lastFifoWritePointer());
  Serial.print(" | rd_ptr=");
  Serial.print(max30102.lastFifoReadPointer());
  Serial.print(" | avail=");
  Serial.print(max30102.lastAvailableSamples());
  Serial.print(" | reg_fail=");
  Serial.print(max30102.registerReadFailCount());
  Serial.print(" | ptr_fail=");
  Serial.print(max30102.fifoPointerReadFailCount());
  Serial.print(" | sample_fail=");
  Serial.println(max30102.fifoSampleReadFailCount());
}

void logRuntimeI2cProbe() {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Wire.beginTransmission(project_config::kMax30102Address);
  const uint8_t probeStatus = Wire.endTransmission();
  Serial.print("[i2c-probe] addr=0x");
  Serial.print(project_config::kMax30102Address, HEX);
  Serial.print(" | end_tx_status=");
  Serial.println(probeStatus);
}

void logRegisterReadback() {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Max30102RawReader::DebugRegisters registers;
  if (!max30102.readDebugRegisters(registers)) {
    Serial.println("[sensor-reg] readback-failed");
    return;
  }

  Serial.print("[sensor-reg] int1=0x");
  Serial.print(registers.interruptStatus1, HEX);
  Serial.print(" | int2=0x");
  Serial.print(registers.interruptStatus2, HEX);
  Serial.print(" | fifo=0x");
  Serial.print(registers.fifoConfig, HEX);
  Serial.print(" | mode=0x");
  Serial.print(registers.modeConfig, HEX);
  Serial.print(" | spo2=0x");
  Serial.print(registers.spo2Config, HEX);
  Serial.print(" | led1=0x");
  Serial.print(registers.led1PulseAmplitude, HEX);
  Serial.print(" | led2=0x");
  Serial.print(registers.led2PulseAmplitude, HEX);
  Serial.print(" | slot1_2=0x");
  Serial.print(registers.multiLedConfig1, HEX);
  Serial.print(" | slot3_4=0x");
  Serial.println(registers.multiLedConfig2, HEX);
}

void writeUserLed(bool turnOn) {
  digitalWrite(
      project_config::kUserLedPin,
      turnOn ? project_config::kLedOnLevel : project_config::kLedOffLevel);
  ledIsOn = turnOn;
}

void waitForSerialIfNeeded() {
  const unsigned long waitStartMs = millis();
  while (!Serial && (millis() - waitStartMs) < project_config::kSerialReadyTimeoutMs) {
    delay(10);
  }
}

void setupMax30102() {
  if (project_config::kEnableAd8232VofaStream) {
    sensorReady = false;
    return;
  }

  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);

  if (!project_config::kEnableMax30102VofaStream) {
    Serial.print("[i2c] SDA=GPIO");
    Serial.print(project_config::kI2cSdaPin);
    Serial.print(" | SCL=GPIO");
    Serial.print(project_config::kI2cSclPin);
    Serial.print(" | clock=");
    Serial.print(project_config::kI2cClockHz);
    Serial.print("Hz | addr=0x");
    Serial.println(project_config::kMax30102Address, HEX);
    scanI2cBus();
  }

  sensorReady = max30102.begin(Wire);
  if (!sensorReady) {
    if (!project_config::kEnableMax30102VofaStream) {
      Serial.print("[sensor] MAX30102 init failed | reason=");
      Serial.print(max30102.lastError());
      Serial.print(" | part_id=0x");
      Serial.println(max30102.partId(), HEX);
    }
    return;
  }

  if (!project_config::kEnableMax30102VofaStream) {
    Serial.print("[sensor] MAX30102 ready | addr=0x");
    Serial.print(max30102.deviceAddress(), HEX);
    Serial.print(" | part_id=0x");
    Serial.println(max30102.partId(), HEX);
    Serial.println("[sensor] waiting for FIFO samples, use a steady fingertip cover for first validation");
  }
}

void setupMicrophone() {
  if (isAnyVofaStreamEnabled()) {
    microphoneReady = false;
    return;
  }

  Serial.print("[mic] BCLK=GPIO");
  Serial.print(project_config::kMicrophoneBclkPin);
  Serial.print(" | WS=GPIO");
  Serial.print(project_config::kMicrophoneWsPin);
  Serial.print(" | DIN=GPIO");
  Serial.print(project_config::kMicrophoneDataPin);
  Serial.print(" | sample_rate=");
  Serial.print(project_config::kMicrophoneSampleRateHz);
  Serial.print("Hz | batch=");
  Serial.print(project_config::kMicrophoneBatchSampleCount);
  Serial.println(" samples");

  microphoneReady = microphone.begin();
  if (!microphoneReady) {
    Serial.print("[mic] ICS43434 init failed | reason=");
    Serial.println(microphone.lastError());
    return;
  }

  Serial.println("[mic] ICS43434 ready | waiting for environment sound changes");
}

void setupPressureSensor() {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  Serial.print("[pressure] ADC=GPIO");
  Serial.print(project_config::kPressureAdcPin);
  Serial.print(" | baseline_samples=");
  Serial.print(project_config::kPressureBaselineSampleCount);
  Serial.print(" | average_samples=");
  Serial.println(project_config::kPressureAverageSampleCount);

  if (!pressureSensor.begin()) {
    Serial.print("[pressure] init failed | reason=");
    Serial.println(pressureSensor.lastError());
    return;
  }

  Serial.print("[pressure] ready | baseline=");
  Serial.print(pressureSensor.baselineRaw());
  Serial.print(" | min_range=");
  Serial.println(project_config::kPressureMinimumRangeRaw);
}

void setupAd8232() {
  if (project_config::kEnableMax30102VofaStream) {
    return;
  }

  if (!project_config::kEnableAd8232VofaStream) {
    Serial.print("[ecg] ADC=GPIO");
    Serial.print(project_config::kAd8232AdcPin);
    Serial.print(" | sample_interval=");
    Serial.print(project_config::kAd8232PollIntervalMs);
    Serial.print("ms | log_interval=");
    Serial.print(project_config::kAd8232LogIntervalMs);
    Serial.println("ms");
  }

  if (!ad8232.begin()) {
    if (!project_config::kEnableAd8232VofaStream) {
      Serial.print("[ecg] init failed | reason=");
      Serial.println(ad8232.lastError());
    }
    return;
  }

  if (!project_config::kEnableAd8232VofaStream) {
    Serial.println("[ecg] AD8232 ready | waiting for electrode contact and waveform changes");
  }
}

void handleMax30102(unsigned long nowMs) {
  if (project_config::kEnableAd8232VofaStream) {
    return;
  }

  if (!sensorReady) {
    if (nowMs - lastI2cRescanAtMs >= 4000) {
      lastI2cRescanAtMs = nowMs;
      Serial.print("[i2c-scan] rescan triggered | uptime=");
      Serial.print(nowMs);
      Serial.println("ms");
      scanI2cBus();
      sensorReady = max30102.begin(Wire);
      if (sensorReady) {
        Serial.print("[sensor] MAX30102 recovered | addr=0x");
        Serial.print(max30102.deviceAddress(), HEX);
        Serial.print(" | part_id=0x");
        Serial.println(max30102.partId(), HEX);
      }
    }

    if (nowMs - lastSensorStatusLogAtMs >= 2000) {
      lastSensorStatusLogAtMs = nowMs;
      Serial.print("[sensor] init-not-ready | uptime=");
      Serial.print(nowMs);
      Serial.print("ms | reason=");
      Serial.print(max30102.lastError());
      Serial.print(" | part_id=0x");
      Serial.println(max30102.partId(), HEX);
    }
    return;
  }

  if (nowMs - lastSensorPollAtMs >= project_config::kSensorPollIntervalMs) {
    lastSensorPollAtMs = nowMs;
    max30102.update();
  }

  Max30102RawReader::Sample sample;
  if (max30102.readLatestSample(sample)) {
    if (sample.sequence != lastProcessedSequence) {
      lastProcessedSequence = sample.sequence;
      heartRateEstimator.addSample(sample);
    }

    if (project_config::kEnableMax30102VofaStream) {
      if (nowMs - lastHeartRateLogAtMs < project_config::kMax30102VofaStreamIntervalMs) {
        return;
      }

      lastHeartRateLogAtMs = nowMs;
      const float bpm_value = heartRateEstimator.hasValidBpm() ? heartRateEstimator.bpm() : 0.0f;
        const float filtered_display_value =
          heartRateEstimator.filteredIr() * project_config::kMax30102VofaFilteredDisplayGain;
      Serial.printf(
          "%lu,%lu,%.1f,%.1f\n",
          static_cast<unsigned long>(sample.ir),
          static_cast<unsigned long>(sample.red),
          filtered_display_value,
          bpm_value);
      return;
    }

    if (project_config::kEnableHeartRateStatusLog &&
        nowMs - lastHeartRateLogAtMs >= project_config::kHeartRateLogIntervalMs) {
      lastHeartRateLogAtMs = nowMs;
      logHeartRateStatus(sample);
    }
    return;
  }

  logReaderDebug("sample-missing");
  if (max30102.lastAvailableSamples() == 0) {
    logRegisterReadback();
    logRuntimeI2cProbe();
  }

  Serial.print("[raw] no-sample-yet | uptime=");
  Serial.print(nowMs);
  Serial.print("ms | reason=");
  Serial.println(max30102.lastError());
}

void handleMicrophone(unsigned long nowMs) {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  if (!microphoneReady) {
    if (nowMs - lastMicrophoneRetryAtMs >= 4000) {
      lastMicrophoneRetryAtMs = nowMs;
      microphoneReady = microphone.begin();
      if (microphoneReady) {
        Serial.println("[mic] ICS43434 recovered | I2S input active");
      }
    }

    if (nowMs - lastMicrophoneStatusLogAtMs >= 2000) {
      lastMicrophoneStatusLogAtMs = nowMs;
      Serial.print("[mic] init-not-ready | uptime=");
      Serial.print(nowMs);
      Serial.print("ms | reason=");
      Serial.println(microphone.lastError());
    }
    return;
  }

  if (nowMs - lastMicrophonePollAtMs >= project_config::kMicrophonePollIntervalMs) {
    lastMicrophonePollAtMs = nowMs;
    microphone.update();
  }

  if (nowMs - lastMicrophoneLogAtMs >= project_config::kMicrophoneLogIntervalMs) {
    lastMicrophoneLogAtMs = nowMs;
    logMicrophoneStatus(nowMs);
    microphone.resetWindowSummary();
  }
}

void handlePressureSensor(unsigned long nowMs) {
  if (isAnyVofaStreamEnabled()) {
    return;
  }

  if (!pressureSensor.isInitialized()) {
    Serial.print("[pressure] init-not-ready | reason=");
    Serial.println(pressureSensor.lastError());
    return;
  }

  if (nowMs - lastPressurePollAtMs >= project_config::kPressurePollIntervalMs) {
    lastPressurePollAtMs = nowMs;
    pressureSensor.update();
  }

  if (nowMs - lastPressureLogAtMs < project_config::kPressureLogIntervalMs) {
    return;
  }

  lastPressureLogAtMs = nowMs;
  PressureFilmRawReader::Sample sample;
  if (!pressureSensor.readLatestSample(sample)) {
    Serial.println("[pressure] no-sample-yet");
    return;
  }

  Serial.print("[pressure] ");
  Serial.println(sample.level);
}

void handleAd8232(unsigned long nowMs) {
  if (project_config::kEnableMax30102VofaStream) {
    return;
  }

  if (!ad8232.isInitialized()) {
    if (!project_config::kEnableAd8232VofaStream) {
      Serial.print("[ecg] init-not-ready | reason=");
      Serial.println(ad8232.lastError());
    }
    return;
  }

  if (nowMs - lastAd8232PollAtMs >= project_config::kAd8232PollIntervalMs) {
    lastAd8232PollAtMs = nowMs;
    ad8232.update();
  }

  if (project_config::kEnableAd8232VofaStream) {
    if (nowMs - lastAd8232LogAtMs < project_config::kAd8232VofaStreamIntervalMs) {
      return;
    }

    lastAd8232LogAtMs = nowMs;
    Ad8232RawReader::Sample sample;
    if (!ad8232.readLatestSample(sample)) {
      return;
    }

    Serial.printf("%u\n", static_cast<unsigned>(sample.rawValue));
    return;
  }

  if (nowMs - lastAd8232LogAtMs < project_config::kAd8232LogIntervalMs) {
    return;
  }

  lastAd8232LogAtMs = nowMs;
  Ad8232RawReader::WindowSummary summary;
  if (!ad8232.readWindowSummary(summary)) {
    Serial.printf(
        "[ecg] up=%-6lums | state=%-9s | err=%-12s | total=%-7llu\n",
        nowMs,
        "idle",
        ad8232.lastError(),
        ad8232.totalSamplesRead());
    return;
  }

  Serial.printf(
      "[ecg] seq=%-5lu | up=%-6lums | samples=%-3u | raw=%-4u | mean=%-4u | min=%-4u | max=%-4u | p2p=%-4u\n",
      static_cast<unsigned long>(summary.lastSequence),
      summary.lastUpdatedAtMs,
      static_cast<unsigned>(summary.sampleCount),
      static_cast<unsigned>(summary.lastRaw),
      static_cast<unsigned>(summary.meanRaw),
      static_cast<unsigned>(summary.minRaw),
      static_cast<unsigned>(summary.maxRaw),
      static_cast<unsigned>(summary.peakToPeak));
  ad8232.resetWindowSummary();
}

}  // namespace

void setup() {
  Serial.begin(115200);
  waitForSerialIfNeeded();
  delay(project_config::kStartupDelayMs);

  pinMode(project_config::kUserLedPin, OUTPUT);
  writeUserLed(false);

  if (!isAnyVofaStreamEnabled()) {
    Serial.println();
    Serial.println("[system] XIAO ESP32S3 多模块原始读取测试启动");
    Serial.println("[system] 板载用户灯引脚: GPIO21, 低电平点亮");
    Serial.print("[system] ADC 采样率配置: ");
    Serial.print(project_config::kSensorAdcSampleRateHz);
    Serial.println("Hz");
    Serial.print("[system] FIFO 平均点数: ");
    Serial.println(project_config::kFifoSampleAverage);
    Serial.print("[system] 有效输出采样率约: ");
    Serial.print(project_config::kSensorEffectiveSampleRateHz);
    Serial.println("Hz");
    Serial.print("[system] 统一内部轮询节拍: ");
    Serial.print(project_config::kSensorPollIntervalMs);
    Serial.println("ms");
    if (project_config::kEnableHeartRateStatusLog) {
      Serial.println("[system] 串口输出目标: 约 2Hz 输出心率状态行，并输出麦克风、压力和 ECG 状态");
    } else {
      Serial.println("[system] 串口输出目标: 暂时关闭心率状态行，保留麦克风、压力和 ECG 状态");
    }
  }

  logMax30102WiringGuide();
  logMicrophoneWiringGuide();
  logPressureWiringGuide();
  logAd8232WiringGuide();
  setupMax30102();
  setupMicrophone();
  setupPressureSensor();
  setupAd8232();
  logLedState("startup");
}

void loop() {
  const unsigned long nowMs = millis();

  if (nowMs - lastToggleAtMs >= project_config::kBlinkIntervalMs) {
    lastToggleAtMs = nowMs;
    writeUserLed(!ledIsOn);
    logLedState("heartbeat");
  }

  handleMax30102(nowMs);
  handleMicrophone(nowMs);
  handlePressureSensor(nowMs);
  handleAd8232(nowMs);
}
