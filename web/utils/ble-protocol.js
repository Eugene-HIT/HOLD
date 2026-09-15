const SERVICE_UUID = '19b10010-e8f2-537e-4f6c-d104768a1214';
const EVENT_UUID = '19b10011-e8f2-537e-4f6c-d104768a1214';
const COMMAND_UUID = '19b10013-e8f2-537e-4f6c-d104768a1214';
const DEVICE_PREFIXES = ['HOLD-INTEGRATED', 'HOLD-LINK-TEST'];
const PHASE_LABELS = {
  n: '待机',
  i: '吸气：震动渐强',
  e: '呼气：震动渐弱',
  c: '基础校准中',
  idle: '待机',
  inhale: '吸气：震动渐强',
  exhale: '呼气：震动渐弱',
  calibrating: '基础校准中'
};
const MOTION_LABELS = {
  still: '稳定佩戴',
  moving: '轻微移动',
  active: '动作较大',
  'imu-miss': 'IMU 未在线'
};

function bytesToText(bytes) {
  let text = '';
  for (let index = 0; index < bytes.length; index += 1) {
    text += String.fromCharCode(bytes[index]);
  }
  return text;
}

function textToBuffer(text) {
  const buffer = new ArrayBuffer(text.length);
  const bytes = new Uint8Array(buffer);
  for (let index = 0; index < text.length; index += 1) {
    bytes[index] = text.charCodeAt(index) & 0xff;
  }
  return buffer;
}

function bytesToHex(bytes) {
  return Array.prototype.map.call(bytes, (byte) => byte.toString(16).padStart(2, '0')).join(' ');
}

function isTargetDevice(device) {
  const name = device.name || device.localName || '';
  return DEVICE_PREFIXES.some((prefix) => name.indexOf(prefix) !== -1);
}

function firstDefined(values, fallback) {
  for (let index = 0; index < values.length; index += 1) {
    if (values[index] !== undefined && values[index] !== null && values[index] !== '') {
      return values[index];
    }
  }
  return fallback;
}

function toBoolean(value) {
  return value === true || value === 1 || value === '1' || value === 'true' || value === 'Y' || value === 'y';
}

function optionalNumber(values) {
  const value = firstDefined(values, undefined);
  return value === undefined ? undefined : Number(value);
}

function optionalBoolean(values) {
  const value = firstDefined(values, undefined);
  return value === undefined ? undefined : toBoolean(value);
}

function labelOf(labels, value) {
  return labels[value] || value || '';
}

function normalizePacket(payload, rawText, bytes) {
  const type = payload.t || payload.type || payload.event_type || 'telemetry';
  const motion = payload.mo || payload.motion || payload.motion_level || '';
  const phase = payload.ph || payload.phase || payload.guide_phase || '';
  return {
    ok: true,
    type,
    rawText,
    rawHex: bytesToHex(bytes),
    deviceId: payload.id || payload.device_id || payload.deviceId || '',
    respirationBpm: optionalNumber([payload.br, payload.respiration_bpm, payload.breath_rate_bpm]),
    heartRateBpm: optionalNumber([payload.hr, payload.heart_rate_bpm, payload.bpm]),
    bodyTempC: optionalNumber([payload.bt, payload.body_temp_c, payload.temperature_c, payload.temp]),
    beatDetected: optionalBoolean([payload.beat, payload.beat_detected]),
    beatCount: optionalNumber([payload.bc, payload.beat_count, payload.press_count]),
    pressureRaw: optionalNumber([payload.pr, payload.pressure_raw]),
    pressureLevel: optionalNumber([payload.pl, payload.pressure_level]),
    pressureBaseline: optionalNumber([payload.pb, payload.pressure_baseline]),
    pressureDelta: optionalNumber([payload.pd, payload.pressure_delta]),
    ppgIr: optionalNumber([payload.ir, payload.ppg_ir]),
    ppgRed: optionalNumber([payload.red, payload.ppg_red]),
    contactPresent: optionalBoolean([payload.ct, payload.contact, payload.contact_present]),
    wearing: optionalBoolean([payload.wear, payload.wearing]),
    calibrationCompleted: optionalBoolean([payload.cc, payload.calibration_completed]),
    deviceAgeMs: Number(firstDefined([payload.age, payload.device_age_ms], 0)),
    motion,
    motionLabel: labelOf(MOTION_LABELS, motion),
    phase,
    phaseLabel: labelOf(PHASE_LABELS, phase),
    axis: payload.axs || payload.axis || payload.locked_axis || '',
    hapticReady: optionalBoolean([payload.hp, payload.haptic_ready]),
    breathRunning: optionalBoolean([payload.bg, payload.breath_enabled, payload.breath_running]),
    calibrationRunning: optionalBoolean([payload.cg, payload.calibration_running]),
    calibrationPrompt: payload.cp || payload.calibration_prompt || '',
    guideText: payload.guide || payload.status_text || '',
    battery: payload.battery || '',
    source: 'json'
  };
}

function parsePacket(buffer) {
  const bytes = new Uint8Array(buffer);
  const rawText = bytesToText(bytes).replace(/\0+$/g, '').trim();

  if (rawText) {
    try {
      return normalizePacket(JSON.parse(rawText), rawText, bytes);
    } catch (error) {
      const pairs = {};
      rawText.split(/[,\n|;]/).forEach((part) => {
        const pieces = part.split(/[:=]/);
        if (pieces.length >= 2) {
          pairs[pieces[0].trim()] = pieces.slice(1).join('=').trim();
        }
      });
      if (Object.keys(pairs).length > 0) {
        return normalizePacket(pairs, rawText, bytes);
      }
    }
  }

  return {
    ok: true,
    type: 'binary',
    rawText,
    rawHex: bytesToHex(bytes),
    deviceId: '',
    motion: '',
    motionLabel: '',
    phase: '',
    phaseLabel: '',
    axis: '',
    hapticReady: false,
    breathRunning: false,
    calibrationRunning: false,
    calibrationPrompt: '',
    guideText: `收到 ${bytes.length} 字节二进制包`,
    battery: '',
    source: 'binary'
  };
}

module.exports = {
  SERVICE_UUID,
  EVENT_UUID,
  COMMAND_UUID,
  DEVICE_PREFIXES,
  isTargetDevice,
  parsePacket,
  textToBuffer
};
