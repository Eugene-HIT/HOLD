/*
 * 创建时间：2026-07-02
 * 文件职责：统一管理小程序调试页使用的 BLE 协议常量与通知解析。
 * 输入：BLE characteristic ArrayBuffer。
 * 输出：标准化后的调试消息对象，供页面直接更新状态、波形和日志窗口。
 * 最后修改时间：2026-07-02
 * 变更记录：
 * - 2026-07-02：新增 BLE 调试协议工具，覆盖状态、呼吸、心率等整机联调消息解析。
 */

const SERVICE_UUID = '19b10010-e8f2-537e-4f6c-d104768a1214';
const NOTIFY_CHARACTERISTIC_UUID = '19b10011-e8f2-537e-4f6c-d104768a1214';
const WRITE_CHARACTERISTIC_UUID = '19b10012-e8f2-537e-4f6c-d104768a1214';
const TARGET_NAME_KEYWORDS = ['HOLD-INTEGRATED'];

function arrayBufferToString(buffer) {
  const byteArray = new Uint8Array(buffer);
  let result = '';

  for (let index = 0; index < byteArray.length; index += 1) {
    result += String.fromCharCode(byteArray[index]);
  }

  return result;
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (error) {
    return null;
  }
}

function detectPacketKind(payload) {
  if (!payload || typeof payload !== 'object') {
    return 'invalid';
  }

  if (payload.msg_type) {
    return payload.msg_type;
  }

  if (payload.device_state && payload.ble_state) {
    return 'device_state';
  }

  if (payload.resp_signal_value !== undefined) {
    return 'resp_debug';
  }

  if (payload.i6 && payload.i7 && payload.sample_count && payload.bpm !== undefined) {
    return 'passive_ppg_batch';
  }

  return 'unknown';
}

function normalizePacket(payload, rawText) {
  const kind = detectPacketKind(payload);
  return {
    kind,
    payload: payload || {},
    rawText: rawText || '',
    receivedAtLabel: new Date().toLocaleTimeString()
  };
}

function parseBleNotifyBuffer(buffer) {
  const rawText = arrayBufferToString(buffer);
  const payload = safeJsonParse(rawText);

  if (!payload) {
    return {
      kind: 'invalid',
      payload: {},
      rawText,
      receivedAtLabel: new Date().toLocaleTimeString()
    };
  }

  return normalizePacket(payload, rawText);
}

function findTargetDevice(devices) {
  return (devices || []).find((item) => {
    const name = (item.name || item.localName || '').toUpperCase();
    return TARGET_NAME_KEYWORDS.some((keyword) => name.indexOf(keyword) !== -1);
  });
}

function findNotifyCharacteristic(characteristics) {
  const exact = (characteristics || []).find((item) =>
    (item.uuid || '').toLowerCase() === NOTIFY_CHARACTERISTIC_UUID
  );

  if (exact) {
    return exact;
  }

  return (characteristics || []).find((item) => item.properties && item.properties.notify);
}

function findWriteCharacteristic(characteristics) {
  const exact = (characteristics || []).find((item) =>
    (item.uuid || '').toLowerCase() === WRITE_CHARACTERISTIC_UUID
  );

  if (exact) {
    return exact;
  }

  return (characteristics || []).find((item) => item.properties && (item.properties.write || item.properties.writeNoResponse));
}

module.exports = {
  SERVICE_UUID,
  NOTIFY_CHARACTERISTIC_UUID,
  WRITE_CHARACTERISTIC_UUID,
  TARGET_NAME_KEYWORDS,
  arrayBufferToString,
  parseBleNotifyBuffer,
  normalizePacket,
  findTargetDevice,
  findNotifyCharacteristic,
  findWriteCharacteristic
};