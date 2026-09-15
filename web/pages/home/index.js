const {
  SERVICE_UUID,
  EVENT_UUID,
  COMMAND_UUID,
  isTargetDevice,
  parsePacket,
  textToBuffer
} = require('../../utils/ble-protocol');

function readableBleError(error) {
  const message = `${error.errMsg || error.errCode || error}`;
  if (message.indexOf('Mac') !== -1 || message.indexOf('not support') !== -1 || message.indexOf('不支持') !== -1) {
    return {
      status: '模拟器不支持 BLE',
      hint: '请点开发者工具右上角“真机调试”或“预览”，在手机微信里连接 HOLD-INTEGRATED。'
    };
  }
  return {
    status: `蓝牙初始化失败 ${error.errCode || error.errMsg}`,
    hint: '请确认手机蓝牙、小程序蓝牙权限和定位权限已打开。'
  };
}

function writeCommand(options, onOk, onFail) {
  const firstWriteType = options.writeType || 'write';
  const secondWriteType = firstWriteType === 'writeNoResponse' ? 'write' : 'writeNoResponse';
  const firstPayload = {
    deviceId: options.deviceId,
    serviceId: options.serviceId,
    characteristicId: options.characteristicId,
    value: options.value
  };
  if (firstWriteType === 'writeNoResponse') {
    firstPayload.writeType = firstWriteType;
  }
  const secondPayload = {
    deviceId: options.deviceId,
    serviceId: options.serviceId,
    characteristicId: options.characteristicId,
    value: options.value,
    writeType: secondWriteType
  };
  wx.writeBLECharacteristicValue({
    deviceId: firstPayload.deviceId,
    serviceId: firstPayload.serviceId,
    characteristicId: firstPayload.characteristicId,
    value: firstPayload.value,
    writeType: firstPayload.writeType,
    success: onOk,
    fail: () => wx.writeBLECharacteristicValue({
      deviceId: secondPayload.deviceId,
      serviceId: secondPayload.serviceId,
      characteristicId: secondPayload.characteristicId,
      value: secondPayload.value,
      writeType: secondPayload.writeType,
      success: onOk,
      fail: onFail
    })
  });
}

Page({
  data: {
    adapterStatus: '未初始化',
    connectionStatus: '未连接',
    deviceName: '未发现',
    deviceId: '',
    serviceId: '',
    eventCharacteristicId: '',
    commandCharacteristicId: '',
    commandWriteType: 'write',
    scanning: false,
    connected: false,
    canSendCommand: false,
    packetType: 'none',
    packetSource: '',
    debugLogCount: 0,
    lastRaw: '等待设备上报',
    lastHex: '',
    respirationBpm: '',
    heartRateBpm: '',
    bodyTempC: '',
    beatCount: 0,
    pressureRaw: '',
    pressureLevel: '',
    pressureBaseline: '',
    pressureDelta: '',
    ppgIr: '',
    ppgRed: '',
    wearState: '等待佩戴',
    contactState: '等待 PPG 接触',
    dataState: '等待设备数据',
    signalQuality: '等待有效佩戴信号',
    cloudStatus: '等待提交',
    lastUpdateText: '暂无',
    lastCloudSubmitAt: 0,
    breathMode: 'timed',
    breathModeOptions: ['1 分钟引导', '心率平复后停止', '手动停止'],
    breathModeText: '1 分钟引导',
    breathRemainingText: '未开始',
    breathStartedAt: 0,
    breathHeartBaseline: 0,
    motion: '',
    phaseAxis: '',
    hapticReady: false,
    breathRunning: false,
    calibrationRunning: false,
    calibrationCompleted: false,
    guideTitle: '未收到设备状态',
    guideText: '连接设备后，这里会显示校准提示、呼吸阶段和硬件反馈状态。',
    primaryHint: '先连接 HOLD-INTEGRATED，再开始校准或呼吸引导。'
  },

  onLoad() {
    wx.onBLECharacteristicValueChange((result) => this.handleNotify(result));
    wx.onBluetoothDeviceFound((result) => this.handleDeviceFound(result));
    wx.onBLEConnectionStateChange((result) => {
      if (result.deviceId === this.data.deviceId && !result.connected) {
        this.setData({
          connected: false,
          canSendCommand: false,
          connectionStatus: '连接已断开',
          primaryHint: '蓝牙连接断开，请重新扫描连接。'
        });
      }
    });
  },

  onUnload() {
    this.clearBreathTimers();
    this.clearCalibrationTimer();
    this.disconnectDevice();
    wx.closeBluetoothAdapter({});
  },

  handleDeviceFound(result) {
    const target = (result.devices || []).find(isTargetDevice);
    if (!target) {
      return;
    }

    this.stopDiscovery();
    this.setData({
      deviceName: target.name || target.localName || 'HOLD-INTEGRATED',
      deviceId: target.deviceId,
      adapterStatus: '已发现设备',
      connectionStatus: '正在连接'
    });
    this.connectDevice(target.deviceId);
  },

  handleScanAndConnect() {
    this.setData({
      adapterStatus: '初始化蓝牙中',
      connectionStatus: '未连接',
      deviceId: '',
      serviceId: '',
      eventCharacteristicId: '',
      commandCharacteristicId: '',
      canSendCommand: false,
      connected: false,
      scanning: true,
      primaryHint: '正在寻找 HOLD-INTEGRATED...'
    });

    wx.stopBluetoothDevicesDiscovery({ complete: () => {} });
    this.openAdapterAndScan();
  },

  openAdapterAndScan() {
    wx.openBluetoothAdapter({
      success: () => {
        this.setData({ adapterStatus: '蓝牙已开启，开始扫描' });
        this.startDiscovery();
      },
      fail: (error) => {
        const readable = readableBleError(error);
        this.setData({
        adapterStatus: readable.status,
        scanning: false,
        primaryHint: readable.hint
      });
      }
    });
  },

  startDiscovery() {
    clearTimeout(this.discoveryTimer);
    this.discoveryTimer = setTimeout(() => {
      if (this.data.scanning && !this.data.deviceId) {
        this.setData({
          adapterStatus: '未发现设备，改用兼容扫描',
          primaryHint: '请确认 HOLD 已上电并靠近手机。'
        });
        this.startDiscoveryWithoutService();
      }
    }, 5000);
    wx.startBluetoothDevicesDiscovery({
      allowDuplicatesKey: false,
      success: () => this.setData({ adapterStatus: '扫描中', scanning: true }),
      fail: () => this.startDiscoveryWithoutService()
    });
    setTimeout(() => this.pickKnownDevice(), 800);
  },

  startDiscoveryWithoutService() {
    wx.startBluetoothDevicesDiscovery({
      allowDuplicatesKey: false,
      success: () => this.setData({ adapterStatus: '兼容扫描中', scanning: true }),
      fail: (error) => this.setData({
        adapterStatus: `扫描失败 ${error.errCode || error.errMsg}`,
        scanning: false
      })
    });
    setTimeout(() => this.pickKnownDevice(), 800);
  },

  pickKnownDevice() {
    if (!this.data.scanning) {
      return;
    }
    wx.getBluetoothDevices({
      success: (result) => this.handleDeviceFound({ devices: result.devices || [] })
    });
  },

  stopDiscovery() {
    wx.stopBluetoothDevicesDiscovery({
      complete: () => {
        clearTimeout(this.discoveryTimer);
        if (this.data.scanning) {
          this.setData({ scanning: false });
        }
      }
    });
  },

  connectDevice(deviceId) {
    wx.createBLEConnection({
      deviceId,
      timeout: 10000,
      success: () => {
        this.setData({ connected: true, connectionStatus: '已连接，获取服务中' });
        this.requestBleMtu(deviceId, () => setTimeout(() => this.fetchServices(deviceId), 500));
      },
      fail: (error) => this.setData({
        connected: false,
        connectionStatus: `连接失败 ${error.errCode || error.errMsg}`
      })
    });
  },

  requestBleMtu(deviceId, next) {
    if (!wx.setBLEMTU) {
      next();
      return;
    }
    wx.setBLEMTU({
      deviceId,
      mtu: 247,
      complete: next
    });
  },

  fetchServices(deviceId) {
    wx.getBLEDeviceServices({
      deviceId,
      success: (result) => {
        const service = (result.services || []).find((item) => item.uuid.toLowerCase() === SERVICE_UUID);
        if (!service) {
          this.setData({ connectionStatus: '未找到 HOLD 主服务' });
          return;
        }

        this.setData({ serviceId: service.uuid, connectionStatus: '服务已找到，获取特征中' });
        this.fetchCharacteristics(deviceId, service.uuid);
      },
      fail: (error) => this.setData({ connectionStatus: `获取服务失败 ${error.errCode || error.errMsg}` })
    });
  },

  fetchCharacteristics(deviceId, serviceId) {
    wx.getBLEDeviceCharacteristics({
      deviceId,
      serviceId,
      success: (result) => {
        const characteristics = result.characteristics || [];
        const eventCharacteristic = characteristics.find((item) => item.uuid.toLowerCase() === EVENT_UUID);
        const commandCharacteristic = characteristics.find((item) => item.uuid.toLowerCase() === COMMAND_UUID);
        if (!eventCharacteristic) {
          this.setData({ connectionStatus: '缺少上报特征，请烧录 integrated BLE 固件' });
          return;
        }

        this.setData({
          eventCharacteristicId: eventCharacteristic.uuid,
          commandCharacteristicId: commandCharacteristic ? commandCharacteristic.uuid : '',
          commandWriteType: commandCharacteristic && commandCharacteristic.properties && commandCharacteristic.properties.writeNoResponse ? 'writeNoResponse' : 'write',
          canSendCommand: Boolean(commandCharacteristic)
        });
        this.enableNotify(deviceId, serviceId, eventCharacteristic.uuid);
      },
      fail: (error) => this.setData({ connectionStatus: `获取特征失败 ${error.errCode || error.errMsg}` })
    });
  },

  enableNotify(deviceId, serviceId, characteristicId) {
    wx.notifyBLECharacteristicValueChange({
      deviceId,
      serviceId,
      characteristicId,
      state: true,
      success: () => this.setData({
        adapterStatus: '蓝牙链路已打通，等待状态与波形数据',
        connectionStatus: '已订阅设备上报',
        primaryHint: '设备连接成功。可先做基础校准，再开启呼吸引导。'
      }),
      fail: (error) => this.setData({ connectionStatus: `订阅失败 ${error.errCode || error.errMsg}` })
    });
  },

  sendCommand(command) {
    if (!this.data.canSendCommand) {
      this.setData({ primaryHint: '当前固件没有命令写入特征，请烧录 integrated BLE 固件。' });
      return;
    }

    this.writeCommandOnce(command, () => this.setData({ primaryHint: `已发送 ${command}` }), () => {
      this.setData({ primaryHint: '连接状态已刷新，正在重发命令...' });
      this.reconnectThenSend(command);
    });
  },

  writeCommandOnce(command, onOk, onFail) {
    const payload = {
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      characteristicId: this.data.commandCharacteristicId,
      value: textToBuffer(command)
    };
    if (this.data.commandWriteType === 'writeNoResponse') {
      payload.writeType = 'writeNoResponse';
    }
    writeCommand(payload, onOk, onFail);
  },

  reconnectThenSend(command) {
    if (!this.data.deviceId) {
      this.setData({ primaryHint: '设备已断开，请重新扫描连接。' });
      return;
    }
    wx.createBLEConnection({
      deviceId: this.data.deviceId,
      timeout: 8000,
      success: () => this.refreshCommandPath(command),
      fail: () => this.setData({ primaryHint: '重连失败，请重新扫描连接。' })
    });
  },

  refreshCommandPath(command) {
    wx.getBLEDeviceServices({
      deviceId: this.data.deviceId,
      success: (serviceResult) => {
        const service = (serviceResult.services || []).find((item) => item.uuid.toLowerCase() === SERVICE_UUID);
        if (!service) {
          this.setData({ primaryHint: '重连后未找到 HOLD 服务，请重新扫描。' });
          return;
        }
        wx.getBLEDeviceCharacteristics({
          deviceId: this.data.deviceId,
          serviceId: service.uuid,
          success: (charResult) => {
            const commandCharacteristic = (charResult.characteristics || []).find((item) => item.uuid.toLowerCase() === COMMAND_UUID);
            if (!commandCharacteristic) {
              this.setData({ primaryHint: '重连后未找到命令特征。' });
              return;
            }
            this.setData({
              serviceId: service.uuid,
              commandCharacteristicId: commandCharacteristic.uuid,
              commandWriteType: commandCharacteristic.properties && commandCharacteristic.properties.writeNoResponse ? 'writeNoResponse' : 'write',
              canSendCommand: true
            });
            setTimeout(() => this.writeCommandOnce(
              command,
              () => this.setData({ primaryHint: `已重发 ${command}` }),
              (error) => this.setData({ primaryHint: `发送失败 ${error.errCode || ''}，请重新扫描` })
            ), 300);
          },
          fail: () => this.setData({ primaryHint: '重连后获取特征失败。' })
        });
      },
      fail: () => this.setData({ primaryHint: '重连后获取服务失败。' })
    });
  },

  onBreathModeChange(event) {
    const index = Number(event.detail.value || 0);
    const modes = ['timed', 'calm', 'manual'];
    this.setData({
      breathMode: modes[index] || 'timed',
      breathModeText: this.data.breathModeOptions[index] || this.data.breathModeOptions[0]
    });
  },

  toggleBreathGuide() {
    if (this.data.breathRunning) {
      this.stopBreathGuide('用户已停止引导');
      return;
    }
    this.startBreathGuide();
  },

  startBreathGuide() {
    this.clearBreathTimers();
    const now = Date.now();
    const heartRate = Number(this.data.heartRateBpm || 0);
    let breathMode = this.data.breathMode;
    let breathModeText = this.data.breathModeText;
    let primaryHint = this.data.primaryHint;
    if (breathMode === 'calm' && heartRate <= 0) {
      breathMode = 'timed';
      breathModeText = '1 分钟引导';
      primaryHint = '心率数据不足，已切换为 1 分钟引导。';
    }
    this.setData({
      breathMode,
      breathModeText,
      breathStartedAt: now,
      breathHeartBaseline: heartRate > 0 ? heartRate : 0,
      breathRemainingText: breathMode === 'manual' ? '手动停止' : '准备开始',
      primaryHint
    });
    this.sendCommand('breath_start');
    this.startBreathCountdown(breathMode);
  },

  stopBreathGuide(reason) {
    const elapsedSeconds = this.data.breathStartedAt
      ? Math.max(0, Math.floor((Date.now() - this.data.breathStartedAt) / 1000))
      : 0;
    this.clearBreathTimers();
    this.setData({
      breathRemainingText: reason || '已停止',
      guideTitle: reason && reason.indexOf('完成') !== -1 ? '本次引导完成' : this.data.guideTitle,
      primaryHint: elapsedSeconds > 0 ? `本次引导 ${elapsedSeconds} 秒，数据仍会继续上报。` : this.data.primaryHint
    });
    this.sendCommand('breath_stop');
  },

  startBreathCountdown(mode) {
    if (mode === 'timed') {
      this.breathStopTimer = setTimeout(() => this.stopBreathGuide('1 分钟完成'), 60000);
    }
    this.breathTickTimer = setInterval(() => {
      const elapsedSeconds = Math.max(0, Math.floor((Date.now() - this.data.breathStartedAt) / 1000));
      if (mode === 'timed') {
        this.setData({ breathRemainingText: `剩余 ${Math.max(0, 60 - elapsedSeconds)} 秒` });
      } else if (mode === 'calm') {
        this.setData({ breathRemainingText: '心率平复后自动停止' });
      }
    }, 1000);
  },

  clearBreathTimers() {
    if (this.breathStopTimer) {
      clearTimeout(this.breathStopTimer);
      this.breathStopTimer = null;
    }
    if (this.breathTickTimer) {
      clearInterval(this.breathTickTimer);
      this.breathTickTimer = null;
    }
  },

  startCalibration() {
    this.clearCalibrationTimer();
    this.setData({
      calibrationRunning: true,
      calibrationCompleted: false,
      guideTitle: '基础校准进行中',
      guideText: '请保持佩戴稳定，校准约 12 秒完成。',
      primaryHint: '校准中会有震动反馈，结束后这里会显示完成状态。'
    });
    this.sendCommand('calibrate_start');
    this.calibrationDoneTimer = setTimeout(() => {
      if (this.data.calibrationRunning) {
        this.setData({
          guideTitle: '校准计时结束',
          guideText: '震动校准流程已结束，正在等待设备确认。原始数据会继续显示。',
          primaryHint: '如果设备未返回完成包，可继续看实时数据或重新校准。'
        });
      }
    }, 13000);
  },

  clearCalibrationTimer() {
    if (this.calibrationDoneTimer) {
      clearTimeout(this.calibrationDoneTimer);
      this.calibrationDoneTimer = null;
    }
  },

  clearDebugCache() {
    this.setData({
      packetType: 'none',
      packetSource: '',
      debugLogCount: 0,
      lastRaw: '已清空调试窗口',
      lastHex: '',
      respirationBpm: '',
      heartRateBpm: '',
      bodyTempC: '',
      beatCount: 0,
      pressureRaw: '',
      pressureLevel: '',
      pressureBaseline: '',
      pressureDelta: '',
      ppgIr: '',
      ppgRed: '',
      wearState: '等待佩戴',
      contactState: '等待 PPG 接触',
      dataState: '等待设备数据',
      signalQuality: '等待有效佩戴信号',
      cloudStatus: '等待提交',
      lastUpdateText: '暂无',
      calibrationCompleted: false,
      motion: '',
      phaseAxis: '',
      guideTitle: '调试窗口已清空',
      guideText: '等待下一条设备状态。'
    });
  },

  handleNotify(result) {
    const packet = parsePacket(result.value);
    const hasRespiration = Number.isFinite(packet.respirationBpm);
    const hasHeartRate = Number.isFinite(packet.heartRateBpm);
    const hasPressure = Number.isFinite(packet.pressureRaw) && packet.pressureRaw > 0;
    const hasPpg = Number.isFinite(packet.ppgIr) && packet.ppgIr > 0;
    const hasRawPacket = packet.source === 'json' && (
      Number.isFinite(packet.pressureRaw) ||
      Number.isFinite(packet.ppgIr) ||
      Number.isFinite(packet.bodyTempC) ||
      Number.isFinite(packet.beatCount)
    );
    const hasAnySensor = packet.source === 'json' && (hasPressure || hasPpg || packet.wearing || packet.contactPresent);
    const dataState = packet.source === 'binary'
      ? '收到未解析数据'
      : packet.source === 'json'
        ? (hasRawPacket ? '数据链路已打通' : '已收到状态包')
        : '等待设备数据';
    const signalQuality = hasAnySensor ? '传感器数据已到达' : '等待有效佩戴信号';
    const calibrationEnded = this.data.calibrationRunning && packet.calibrationRunning === false;
    const calibrationDone = packet.type === 'cal_done' || packet.type === 'calibration_done' || packet.calibrationCompleted || calibrationEnded;
    const guideTitle = calibrationDone || this.data.calibrationCompleted
      ? '基础校准完成'
      : packet.calibrationRunning
      ? '基础校准进行中'
      : packet.breathRunning
        ? '呼吸引导启动中'
        : '设备状态已同步';
    const guideText = packet.calibrationPrompt || packet.guideText || (
      calibrationDone
        ? '校准已完成。现在可以进入呼吸引导；即使佩戴信号不足，也会继续显示原始数据。'
        : packet.phaseLabel
          ? `跟随硬件反馈：${packet.phaseLabel}`
          : '保持佩戴稳定，等待更多有效数据。'
    );

    const update = {
      packetType: packet.type,
      packetSource: packet.source,
      debugLogCount: this.data.debugLogCount + 1,
      deviceName: packet.deviceId || this.data.deviceName,
      lastRaw: packet.rawText || '(二进制包)',
      lastHex: packet.rawHex,
      respirationBpm: hasRespiration ? packet.respirationBpm : this.data.respirationBpm,
      heartRateBpm: hasHeartRate ? packet.heartRateBpm : this.data.heartRateBpm,
      bodyTempC: Number.isFinite(packet.bodyTempC) ? packet.bodyTempC : this.data.bodyTempC,
      beatCount: Number.isFinite(packet.beatCount) ? packet.beatCount : this.data.beatCount,
      pressureRaw: Number.isFinite(packet.pressureRaw) ? packet.pressureRaw : this.data.pressureRaw,
      pressureLevel: Number.isFinite(packet.pressureLevel) ? packet.pressureLevel : this.data.pressureLevel,
      pressureBaseline: Number.isFinite(packet.pressureBaseline) ? packet.pressureBaseline : this.data.pressureBaseline,
      pressureDelta: Number.isFinite(packet.pressureDelta) ? packet.pressureDelta : this.data.pressureDelta,
      ppgIr: Number.isFinite(packet.ppgIr) ? packet.ppgIr : this.data.ppgIr,
      ppgRed: Number.isFinite(packet.ppgRed) ? packet.ppgRed : this.data.ppgRed,
      dataState,
      signalQuality,
      lastUpdateText: new Date().toLocaleTimeString(),
      motion: packet.motionLabel || packet.motion || this.data.motion,
      phaseAxis: [packet.phaseLabel || packet.phase, packet.axis].filter(Boolean).join(' / ') || this.data.phaseAxis,
      guideTitle,
      guideText,
      primaryHint: packet.source === 'binary'
        ? '收到二进制包：请对照调试页 hex 判断固件协议版本。'
        : dataState
    };
    if (packet.hapticReady !== undefined) {
      update.hapticReady = packet.hapticReady;
    }
    if (packet.breathRunning !== undefined) {
      update.breathRunning = packet.breathRunning;
    }
    if (packet.calibrationRunning !== undefined) {
      update.calibrationRunning = packet.calibrationRunning;
    }
    if (packet.wearing !== undefined) {
      update.wearState = packet.wearing ? '佩戴中' : '等待佩戴';
    }
    if (packet.contactPresent !== undefined) {
      update.contactState = packet.contactPresent ? 'PPG 接触有效' : '等待 PPG 接触';
    }
    if (calibrationDone) {
      update.calibrationRunning = false;
      update.calibrationCompleted = true;
      update.guideTitle = '基础校准完成';
      update.guideText = '校准已完成。现在可以开始呼吸引导；原始数据会持续显示。';
      update.primaryHint = '校准完成，数据链路已继续上报。';
      this.clearCalibrationTimer();
    }

    this.setData(update);
    this.maybeAutoStopBreath(packet);
    if (packet.source === 'json') {
      this.submitTelemetryToCloud(packet);
    }
  },

  maybeAutoStopBreath(packet) {
    if (!this.data.breathRunning || this.data.breathMode !== 'calm' || !this.data.breathHeartBaseline) {
      return;
    }
    const elapsedMs = Date.now() - this.data.breathStartedAt;
    const heartRate = Number(packet.heartRateBpm || 0);
    if (elapsedMs > 30000 && heartRate > 0 && heartRate <= this.data.breathHeartBaseline - 3) {
      this.stopBreathGuide('心率已平复');
    }
  },

  submitTelemetryToCloud(packet) {
    if (!wx.cloud || !wx.cloud.callFunction) {
      return;
    }
    const now = Date.now();
    if ((packet.type === 'telemetry' || packet.type === 'tel') && now - this.data.lastCloudSubmitAt < 3000) {
      return;
    }
    this.setData({ lastCloudSubmitAt: now });
    wx.cloud.callFunction({
      name: 'link_test_ingest',
      data: {
        device_id: packet.deviceId || this.data.deviceName,
        event_type: packet.type,
        respiration_bpm: packet.respirationBpm,
        heart_rate_bpm: packet.heartRateBpm,
        body_temp_c: packet.bodyTempC,
        beat_count: packet.beatCount,
        pressure_raw: packet.pressureRaw,
        pressure_level: packet.pressureLevel,
        ppg_ir: packet.ppgIr,
        ppg_red: packet.ppgRed,
        wearing: packet.wearing,
        contact_present: packet.contactPresent,
        device_timestamp: packet.deviceAgeMs || Date.now(),
        miniapp_timestamp: now
      },
      success: () => this.setData({ cloudStatus: '云端已提交' }),
      fail: (error) => this.setData({ cloudStatus: `云端提交失败 ${error.errMsg || ''}` })
    });
  },

  disconnectDevice() {
    this.clearBreathTimers();
    this.clearCalibrationTimer();
    this.stopDiscovery();
    if (!this.data.deviceId) {
      return;
    }

    wx.closeBLEConnection({
      deviceId: this.data.deviceId,
      complete: () => this.setData({
        connected: false,
        canSendCommand: false,
        connectionStatus: '已断开',
        deviceId: '',
        serviceId: '',
        eventCharacteristicId: '',
      commandCharacteristicId: '',
        commandWriteType: 'write',
        primaryHint: '连接已断开，可重新扫描。'
      })
    });
  },

  openDebugPage() {
    wx.navigateTo({ url: '/pages/index/index' });
  }
});
