# HOLD 小程序 ↔ 硬件 BLE 接口文档

> 本文档基于小程序端代码（`utils/ble-debug-protocol.js`、`utils/hold-ble-runtime.js`）逆向整理，描述微信小程序与 HOLD-INTEGRATED 设备之间的 BLE 通信协议。
> 整理日期：2026-09-06 ｜ 协议版本：runtime state v2

---

## 1. 概览

| 项 | 说明 |
|---|---|
| 传输方式 | BLE GATT，单服务双特征（Notify + Write） |
| 数据编码 | **JSON 文本**，逐字节 ASCII/UTF-8 解码，单条通知即一个完整 JSON 对象 |
| 下行（设备 → 小程序） | Notify 特征推送，共 8 类报文 + 2 类日志报文 |
| 上行（小程序 → 设备） | Write 特征写入 JSON 命令，目前 2 条 |
| 设备识别 | 广播名包含关键字 `HOLD-INTEGRATED`（大小写不敏感） |
| 连接超时 | 10 秒 |
| 重连策略 | 意外断开后 1.2 秒触发重扫重连，最多 3 次；手动断开不触发 |

---

## 2. GATT 结构

| 角色 | UUID | 属性 |
|---|---|---|
| Service | `19b10010-e8f2-537e-4f6c-d104768a1214` | — |
| Notify Characteristic | `19b10011-e8f2-537e-4f6c-d104768a1214` | Notify |
| Write Characteristic | `19b10012-e8f2-537e-4f6c-d104768a1214` | Write / WriteNoResponse |

**特征兜底匹配规则**：若精确 UUID 未匹配到，小程序会退化为按属性查找——Notify 特征取第一个 `properties.notify` 为真的特征，Write 特征取第一个 `properties.write || properties.writeNoResponse` 为真的特征。

**连接流程**：扫描（名称匹配）→ `createBLEConnection` → `getBLEDeviceServices`（匹配 Service UUID）→ `getBLEDeviceCharacteristics` → `notifyBLECharacteristicValueChange(true)` 订阅 → 链路就绪。未调用 `setBLEMTU`，使用默认 MTU。

---

## 3. 上行命令（小程序 → 设备）

写入 Write 特征，内容为 JSON 文本。

### 3.1 开始呼吸引导 `start_breath_guide`

```json
{
  "cmd": "start_breath_guide",
  "cycles": 6,
  "inhale_ms": 4000,
  "exhale_ms": 5000,
  "duration_ms": 54000
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `cmd` | string | 固定 `start_breath_guide` |
| `cycles` | number | 引导循环次数，当前固定 6 |
| `inhale_ms` | number | 单次吸气时长，固定 4000 |
| `exhale_ms` | number | 单次呼气时长，固定 5000 |
| `duration_ms` | number | 总时长，固定 54000 |

下发后设备进入 `BREATH_GUIDE_SESSION` 状态，通过 `device_state` / `resp_debug` 报文持续下发 `guide_text`、`phase_type`、`phase_remaining_ms`。

### 3.2 开始主动检测 `start_active_test`

```json
{
  "cmd": "start_active_test",
  "duration_ms": 60000
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `cmd` | string | 固定 `start_active_test` |
| `duration_ms` | number | 检测时长，默认 60000 |

> ⚠️ **待真机验证**：该命令名为小程序侧按 `start_breath_guide` 对称推断，固件是否识别需实测；若不识别需按固件实际命令名调整（仅改 `hold-ble-runtime.js` 一处）。设备也可自行进入 `FINGER_PPG_ACTIVE_TEST` 状态，此时小程序仅作为接收方，全流程不受影响。

---

## 4. 下行报文（设备 → 小程序）

### 4.1 报文类型识别规则

小程序按以下优先级判定报文类型（`detectPacketKind`）：

1. **`msg_type` 字段存在 → 直接作为报文类型**（推荐，固件应显式携带）
2. 同时含 `device_state` + `ble_state` → `device_state`
3. 含 `resp_signal_value` → `resp_debug`
4. 同时含 `i6` + `i7` + `sample_count` + `bpm` → `passive_ppg_batch`
5. 均不匹配 → `unknown`（仅记录调试日志）

非 JSON 文本 → `invalid`（记录原文，不处理）。

### 4.2 `device_state` — 设备状态

| 字段 | 类型 | 说明 |
|---|---|---|
| `device_state` | string | 设备状态机值，见第 5 节 |
| `ble_state` | string | 设备侧 BLE 链路状态描述 |
| `guide_text` | string | 引导/提示文案（`status_text` 为等价别名） |
| `phase_type` | string | 引导阶段类型，仅 `BREATH_GUIDE_SESSION` 下有效 |
| `phase_remaining_ms` | number | 当前阶段剩余毫秒 |

### 4.3 `resp_debug` / `calibration_status` — 呼吸实时流

| 字段 | 类型 | 说明 |
|---|---|---|
| `resp_signal_value` | number | 呼吸波形采样点（追加到呼吸波形序列） |
| `resp_beat_marker_value` | number | 呼吸跳点标记值 |
| `resp_rate_bpm` | number | 当前呼吸率（次/分） |
| `resp_amplitude` | number | 呼吸幅度（调试用） |
| `motion_level` | number | 体动水平（0–1 浮点） |
| `axis_name` | string | 校准轴名，仅 `RESP_CALIBRATING` 下使用 |
| `calibration_step` | number | 校准步骤序号 |
| `guide_text` | string | 引导文案（可选，覆盖前值） |
| `phase_type` | string | 阶段类型（校准时复用） |
| `phase_remaining_ms` | number | 阶段剩余毫秒 |

### 4.4 `active_realtime` — 指部 PPG 实时单点

| 字段 | 类型 | 说明 |
|---|---|---|
| `i6_filtered_point` | number | I6 滤波后 PPG 单点 |
| `i7_beat_marker` | number | I7 beat 标记单点 |
| `heart_rate_bpm` | number | 实时心率 |
| `quality_score` | number | 信号质量分（0–100） |
| `beat_count` | number | 累计检出 beat 数 |
| `contact_present` | bool | 手指接触状态 |
| `measurement_id` | number | 所属测量 ID |

### 4.5 `active_realtime_batch` — 指部 PPG 实时批量

| 字段 | 类型 | 说明 |
|---|---|---|
| `i6` | number[] | I6 滤波波形批量点 |
| `i7` | number[] | I7 beat 标记批量点 |
| `measurement_id` | number | 测量 ID |
| `sample_count` | number | 本批点数 |
| `dt_ms` | number | 采样间隔（毫秒） |
| `ts_ms_end` | number | 本批末点设备时间戳 |
| `bpm` | number | 实时心率 |
| `bc` | number | 累计 beat 数 |
| `i12` | number | 最近一次 beat 间期（毫秒） |
| `qs` | number | 信号质量分 |
| `cp` | number/bool | 接触状态（非 0 即贴合） |

小程序按 `measurement_id` 累积完整实时波形（上限 6000 点 ≈ 60s × 100Hz），用于在窗口元数据到达前先完成归档。

### 4.6 `passive_resp_window` — 被动呼吸窗口

设备周期性完成一个被动监测窗口后上报，触发日级聚合。

| 字段 | 类型 | 说明 |
|---|---|---|
| `window_id` | number | 窗口 ID |
| `window_end_ts_ms` | number | 窗口结束时间戳（用于按天归档） |
| `resp_rate_bpm` | number | 窗口平均呼吸率 |
| `quality_score` | number | 窗口质量分 |
| `motion_level` | number | 窗口体动水平 |
| `point_count` | number | 窗口点数 |

### 4.7 `passive_ppg_batch` — 胸口 PPG 批量

| 字段 | 类型 | 说明 |
|---|---|---|
| `i6` | number[] | 胸口 PPG 波形批量点 |
| `i7` | number[] | 胸口 PPG beat 标记批量点 |
| `sample_count` | number | 本批点数 |
| `bpm` | number | 当前心率 |
| `qs` | number | 信号质量分 |

识别依赖第 4.1 节的字段启发式（`i6+i7+sample_count+bpm`），**建议固件显式携带 `msg_type`**。

### 4.8 `active_window` — 主动检测窗口（分片协议）

检测完成后设备分片下发窗口元数据，按 `measurement_id` 重组。

**元数据字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `measurement_id` | number | 测量 ID（与实时批量关联） |
| `session_id` | number | 会话 ID（可选） |
| `fragment_index` | number | 当前分片序号 |
| `fragment_total` | number | 分片总数 |
| `sample_start_ts_ms` / `sample_end_ts_ms` | number | 采样起止时间戳 |
| `heart_rate_bpm` | number | 窗口平均心率 |
| `quality_score` | number | 窗口质量分 |
| `processed_point_count` | number | 处理后总点数 |
| `beat_count` | number | beat 总数 |
| `rr_interval_count` | number | RR 间期总数 |

**分片数据字段**（按 offset 写入对应数组）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `processed_point_offset` | number | 波形分片起始下标 |
| `processed_points_fragment` | number[] | 处理后波形分片 |
| `beat_offset` | number | beat 时间戳分片起始下标 |
| `beat_ts_ms_fragment` | number[] | beat 时间戳分片 |
| `rr_intervals_ms_fragment` | number[] | RR 间期分片（从头填充，无 offset） |

**完成判定**：已收分片数 = `fragment_total` 且 `processedPoints`、`rrIntervalsMs` 无空洞。

**实时兜底**：若分片未到齐但实时累积波形已达预期点数 90%（或 ≥ 1200 点、或时长 ≥ 55 秒），小程序以实时累计结果先行归档，分片到齐后二次覆盖归档（同 id upsert）。

### 4.9 `debug_log` / `error_status` — 日志报文

| 报文 | 字段 | 说明 |
|---|---|---|
| `debug_log` | `message` | 设备调试文本，直接进调试日志 |
| `error_status` | `error_code`、`error_message` | 设备错误上报 |

---

## 5. 设备状态机（`device_state` 已知取值）

| 状态值 | 含义 | 小程序行为 |
|---|---|---|
| `RESP_CALIBRATING` | 呼吸校准中 | 显示轴名、校准步骤、引导文案 |
| `BREATH_GUIDE_SESSION` | 呼吸引导进行中 | 显示阶段类型与剩余时间，主按钮变为"引导进行中" |
| `FINGER_PPG_ACTIVE_TEST` | 指部 PPG 主动检测中 | 首页显示 60 秒进度、实时心率与 beat 数 |
| 其他值 | 常规监测 | 仅更新状态文案与调试日志 |

---

## 6. 主动检测完整时序

```
小程序                     设备
  |---- start_active_test --->|  （可选，设备也可自行开始）
  |                           |  进入 FINGER_PPG_ACTIVE_TEST
  |<-- active_realtime_batch--|  实时 I6/I7 波形 + 心率/beat（持续 60s）
  |<-- active_realtime_batch--|  ...
  |<-- active_window (1/N) ---|  窗口元数据分片
  |<-- active_window (N/N) ---|  分片到齐 → 完整归档
  |                           |  离开 FINGER_PPG_ACTIVE_TEST
```

- 实时流与窗口元数据**可能乱序**：小程序用 `pendingActiveRealtimeMeasurements` 与 `pendingActiveWindows` 两个暂存表按 `measurement_id` 关联
- 归档以**实时累计波形为准**（完整 60 秒），分片数据用于补充处理后波形与 RR 间期
- 归档完成后自动触发一次云端整体分析刷新

---

## 7. 待确认事项

| 项 | 状态 |
|---|---|
| `start_active_test` 命令名 | ⚠️ 小程序侧推断，需固件确认 |
| `device_state` 完整取值集合 | 代码仅消费上述 3 个值，其余按未知状态处理 |
| `passive_ppg_batch` 无 `msg_type` 时依赖字段启发式 | 建议固件显式携带 `msg_type` |
| MTU / 长 JSON 分包 | 小程序未协商 MTU；若单条 JSON 超过默认 MTU，需固件侧分包或双方协商 |
| `calibration_status` 与 `resp_debug` 字段差异 | 小程序同函数处理，字段全集以固件为准 |
