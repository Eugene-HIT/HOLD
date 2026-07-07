/*
 * 创建时间：2026-07-02
 * 文件职责：验证 XIAO ESP32S3 在整机联动方案下对 1 分钟业务窗口缓存的 RAM 承载能力。
 * 核心输入输出：输入为预设的缓冲场景参数；输出为各场景分配结果、堆剩余量与建议的分片策略。
 * 最后更改时间：2026-07-02
 * 更改日志：
 * - 2026-07-02：新增最小 RAM 探针环境，用于验证被动/主动窗口缓存的可行性。
 * 注意事项：
 * - 本环境不接任何外设，只验证代表性数据结构的内存占用。
 * - 若后续真实字段数量变化，需要同步调整本文件的场景参数。
 */

#include <Arduino.h>
#include <esp_heap_caps.h>

namespace {

struct ProbeScenario {
  const char *name;
  size_t passiveRespPoints;
  size_t passivePpgPoints;
  size_t activeProcessedPoints;
  size_t activeBeatCount;
  size_t activeRawPoints;
  size_t passiveWindowCount;
  bool includeRawChannels;
};

struct AllocationBlock {
  const char *label;
  size_t bytes;
  uint8_t *data;
};

constexpr uint32_t kProbeRepeatIntervalMs = 8000;

const ProbeScenario kScenarios[] = {
    {
        "minute-lite",
        300,
        300,
        1500,
        120,
        0,
        1,
        false,
    },
    {
        "minute-with-raw",
        300,
        300,
        1500,
        120,
        1500,
        1,
        true,
    },
    {
        "multi-window-fragment-cache",
        600,
        600,
        1500,
        160,
        1500,
        3,
        true,
    },
};

uint32_t lastProbeAtMs = 0;

size_t bytesForU16(size_t count) { return count * sizeof(uint16_t); }

size_t bytesForU32(size_t count) { return count * sizeof(uint32_t); }

void logHeap(const char *stageLabel) {
  Serial.printf(
      "[heap] stage=%s free=%u min=%u largest=%u psram=%s\n",
      stageLabel,
      static_cast<unsigned>(ESP.getFreeHeap()),
      static_cast<unsigned>(ESP.getMinFreeHeap()),
      static_cast<unsigned>(heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)),
      psramFound() ? "YES" : "NO");
}

bool allocateBlock(AllocationBlock &block) {
  block.data = static_cast<uint8_t *>(heap_caps_malloc(block.bytes, MALLOC_CAP_8BIT));
  if (block.data == nullptr) {
    Serial.printf("[alloc] label=%s bytes=%u result=FAIL\n",
                  block.label,
                  static_cast<unsigned>(block.bytes));
    return false;
  }

  const size_t touchBytes = block.bytes < 64 ? block.bytes : 64;
  for (size_t index = 0; index < touchBytes; ++index) {
    block.data[index] = static_cast<uint8_t>(index & 0xFF);
  }

  Serial.printf("[alloc] label=%s bytes=%u result=OK\n",
                block.label,
                static_cast<unsigned>(block.bytes));
  return true;
}

void freeBlocks(AllocationBlock *blocks, size_t blockCount) {
  for (size_t index = 0; index < blockCount; ++index) {
    if (blocks[index].data != nullptr) {
      free(blocks[index].data);
      blocks[index].data = nullptr;
    }
  }
}

void printScenarioSummary(const ProbeScenario &scenario) {
  const size_t passiveRespBytes = bytesForU16(scenario.passiveRespPoints * scenario.passiveWindowCount);
  const size_t passivePpgBytes = bytesForU16(scenario.passivePpgPoints * scenario.passiveWindowCount);
  const size_t activeProcessedBytes = bytesForU16(scenario.activeProcessedPoints);
  const size_t activeBeatBytes = bytesForU32(scenario.activeBeatCount);
  const size_t activeRawIrBytes = scenario.includeRawChannels ? bytesForU32(scenario.activeRawPoints) : 0;
  const size_t activeRawRedBytes = scenario.includeRawChannels ? bytesForU32(scenario.activeRawPoints) : 0;
  const size_t metadataBytes = 1024;
  const size_t totalBytes = passiveRespBytes + passivePpgBytes + activeProcessedBytes +
                            activeBeatBytes + activeRawIrBytes + activeRawRedBytes + metadataBytes;

  Serial.printf(
      "[scenario] name=%s passive_windows=%u resp_points=%u ppg_points=%u active_processed=%u beats=%u raw_points=%u total_bytes=%u\n",
      scenario.name,
      static_cast<unsigned>(scenario.passiveWindowCount),
      static_cast<unsigned>(scenario.passiveRespPoints),
      static_cast<unsigned>(scenario.passivePpgPoints),
      static_cast<unsigned>(scenario.activeProcessedPoints),
      static_cast<unsigned>(scenario.activeBeatCount),
      static_cast<unsigned>(scenario.activeRawPoints),
      static_cast<unsigned>(totalBytes));

  if (scenario.passiveWindowCount > 1) {
    Serial.println("[recommend] 建议优先按 10s 到 20s 分片发送，再在云端聚合为 1 分钟窗口");
  } else if (scenario.includeRawChannels) {
    Serial.println("[recommend] 建议主动检测优先发送处理后波形和 beat，再视链路余量附带 raw ir/red");
  } else {
    Serial.println("[recommend] 当前场景适合作为分钟级摘要缓存基线");
  }
}

void runScenario(const ProbeScenario &scenario) {
  AllocationBlock blocks[] = {
      {"passive_resp_wave", bytesForU16(scenario.passiveRespPoints * scenario.passiveWindowCount), nullptr},
      {"passive_ppg_wave", bytesForU16(scenario.passivePpgPoints * scenario.passiveWindowCount), nullptr},
      {"active_processed_wave", bytesForU16(scenario.activeProcessedPoints), nullptr},
      {"active_beat_ts", bytesForU32(scenario.activeBeatCount), nullptr},
      {"active_raw_ir", scenario.includeRawChannels ? bytesForU32(scenario.activeRawPoints) : 0, nullptr},
      {"active_raw_red", scenario.includeRawChannels ? bytesForU32(scenario.activeRawPoints) : 0, nullptr},
      {"packet_metadata", 1024, nullptr},
  };

  printScenarioSummary(scenario);
  logHeap("before");

  bool allAllocated = true;
  for (size_t index = 0; index < (sizeof(blocks) / sizeof(blocks[0])); ++index) {
    if (blocks[index].bytes == 0) {
      continue;
    }

    if (!allocateBlock(blocks[index])) {
      allAllocated = false;
      break;
    }
  }

  logHeap(allAllocated ? "after_alloc_ok" : "after_alloc_fail");
  freeBlocks(blocks, sizeof(blocks) / sizeof(blocks[0]));
  logHeap("after_free");
  Serial.println("[scenario] done");
}

void runProbe() {
  Serial.println();
  Serial.println("[probe] ===== RAM window probe start =====");
  for (size_t index = 0; index < (sizeof(kScenarios) / sizeof(kScenarios[0])); ++index) {
    runScenario(kScenarios[index]);
  }
  Serial.println("[probe] ===== RAM window probe end =====");
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(1200);
  Serial.println("[boot] xiao_esp32s3_ram_window_probe starting");
  logHeap("boot");
  runProbe();
  lastProbeAtMs = millis();
}

void loop() {
  const uint32_t nowMs = millis();
  if (nowMs - lastProbeAtMs >= kProbeRepeatIntervalMs) {
    lastProbeAtMs = nowMs;
    runProbe();
  }

  delay(50);
}