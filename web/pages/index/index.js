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
    return '模拟器不支持 BLE，请用真机调试或预览到手机';
  }
  return `蓝牙初始化失败: ${error.errCode || error.errMsg}`;
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
    canSendCommand: false,
    breathRunning: false,
    calibrationRunning: false,
    hapticReady: false,
    packetType: 'none',
    packetSource: '',
    respirationBpm: '',
    heartRateBpm: '',
    bodyTempC: '',
    beatCount: 0,
    pressureRaw: '',
    pressureLevel: '',
    ppgIr: '',
    ppgRed: '',
    dataState: '等待设备数据',
    motion: '',
    phaseAxis: '',
    lastEventTime: '暂无',
    lastEventRaw: '等待设备通知...',
    lastEventHex: '',
    cloudStatus: '未提交',
    storagePath: '暂无',
    llmReply: '暂无'
  },

  onLoad() {
    wx.onBLECharacteristicValueChange((result) => this.handleNotifyMessage(result));
    wx.onBluetoothDeviceFound((result) => this.handleDeviceFound(result));
  },

  onUnload() {
    this.stopDiscovery();
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
      adapterStatus: '已发现目标设备',
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
      scanning: true
    });

    wx.stopBluetoothDevicesDiscovery({ complete: () => {} });
    wx.openBluetoothAdapter({
      success: () => {
        this.setData({ adapterStatus: '蓝牙已开启，开始扫描' });
        this.startDiscovery();
      },
      fail: (error) => this.setData({
        adapterStatus: readableBleError(error),
        scanning: false
      })
    });
  },

  startDiscovery() {
    wx.startBluetoothDevicesDiscovery({
      allowDuplicatesKey: false,
      success: () => this.setData({ adapterStatus: '扫描中，等待 HOLD-INTEGRATED...', scanning: true }),
      fail: () => wx.startBluetoothDevicesDiscovery({
        allowDuplicatesKey: false,
        success: () => this.setData({ adapterStatus: '扫描中，等待 HOLD-INTEGRATED...', scanning: true }),
        fail: (error) => this.setData({
          adapterStatus: `扫描失败: ${error.errCode || error.errMsg}`,
          scanning: false
        })
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
        this.setData({ connectionStatus: '已连接，获取服务中' });
        this.requestBleMtu(deviceId, () => this.fetchServices(deviceId));
      },
      fail: (error) => this.setData({ connectionStatus: `连接失败: ${error.errCode || error.errMsg}` })
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
      fail: (error) => this.setData({ connectionStatus: `获取服务失败: ${error.errCode || error.errMsg}` })
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
          this.setData({ connectionStatus: '缺少通知特征，请烧录 integrated BLE 固件' });
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
      fail: (error) => this.setData({ connectionStatus: `获取特征失败: ${error.errCode || error.errMsg}` })
    });
  },

  enableNotify(deviceId, serviceId, characteristicId) {
    wx.notifyBLECharacteristicValueChange({
      deviceId,
      serviceId,
      characteristicId,
      state: true,
      success: () => this.setData({
        connectionStatus: '已订阅硬件通知',
        adapterStatus: '蓝牙链路已打通，等待状态与波形数据'
      }),
      fail: (error) => this.setData({ connectionStatus: `订阅失败: ${error.errCode || error.errMsg}` })
    });
  },

  sendCommand(command) {
    if (!this.data.canSendCommand) {
      this.setData({ connectionStatus: '未发现命令特征，不能发送' });
      return;
    }

    const payload = {
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      characteristicId: this.data.commandCharacteristicId,
      value: textToBuffer(command),
      writeType: this.data.commandWriteType
    };
    writeCommand(payload, () => this.setData({ connectionStatus: `已发送: ${command}` }),
    (error) => this.setData({ connectionStatus: `发送失败 ${error.errCode || ''}，请重新连接` }));
  },

  toggleBreath() {
    this.sendCommand(this.data.breathRunning ? 'breath_stop' : 'breath_start');
  },

  startCalibration() {
    this.sendCommand('calibrate_start');
  },

  clearDebugWindow() {
    this.setData({
      packetType: 'none',
      packetSource: '',
      respirationBpm: '',
      heartRateBpm: '',
      bodyTempC: '',
      beatCount: 0,
      pressureRaw: '',
      pressureLevel: '',
      ppgIr: '',
      ppgRed: '',
      dataState: '等待设备数据',
      motion: '',
      phaseAxis: '',
      lastEventTime: '暂无',
      lastEventRaw: '已清空调试窗口',
      lastEventHex: ''
    });
  },

  handleNotifyMessage(result) {
    const packet = parsePacket(result.value);
    const hasSensor = packet.source === 'json' && (
      packet.wearing || packet.contactPresent || packet.pressureRaw > 0 || packet.ppgIr > 0
    );
    this.setData({
      packetType: packet.type,
      packetSource: packet.source,
      deviceName: packet.deviceId || this.data.deviceName,
      respirationBpm: Number.isFinite(packet.respirationBpm) ? packet.respirationBpm : this.data.respirationBpm,
      heartRateBpm: Number.isFinite(packet.heartRateBpm) ? packet.heartRateBpm : this.data.heartRateBpm,
      bodyTempC: Number.isFinite(packet.bodyTempC) ? packet.bodyTempC : this.data.bodyTempC,
      beatCount: Number.isFinite(packet.beatCount) ? packet.beatCount : this.data.beatCount,
      pressureRaw: Number.isFinite(packet.pressureRaw) ? packet.pressureRaw : this.data.pressureRaw,
      pressureLevel: Number.isFinite(packet.pressureLevel) ? packet.pressureLevel : this.data.pressureLevel,
      ppgIr: Number.isFinite(packet.ppgIr) ? packet.ppgIr : this.data.ppgIr,
      ppgRed: Number.isFinite(packet.ppgRed) ? packet.ppgRed : this.data.ppgRed,
      dataState: packet.source === 'binary'
        ? '收到未解析数据'
        : packet.source === 'json'
          ? (hasSensor ? '数据链路已打通 / 传感器有效' : '数据链路已打通 / 佩戴信号弱')
          : '等待设备数据',
      motion: packet.motionLabel || packet.motion || this.data.motion,
      phaseAxis: [packet.phaseLabel || packet.phase, packet.axis].filter(Boolean).join(' / ') || this.data.phaseAxis,
      lastEventTime: new Date().toLocaleString(),
      lastEventRaw: packet.rawText || packet.guideText || '(二进制包)',
      lastEventHex: packet.rawHex
    });

    if (packet.hapticReady !== undefined) {
      this.setData({ hapticReady: packet.hapticReady });
    }
    if (packet.breathRunning !== undefined) {
      this.setData({ breathRunning: packet.breathRunning });
    }
    if (packet.calibrationRunning !== undefined) {
      this.setData({ calibrationRunning: packet.calibrationRunning });
    }

    if (packet.source === 'json') {
      this.submitEventToCloud(packet);
    }
  },

  submitEventToCloud(eventPayload) {
    this.setData({ cloudStatus: '提交云函数中...' });
    wx.cloud.callFunction({
      name: 'link_test_ingest',
      data: {
        device_id: eventPayload.deviceId || this.data.deviceName,
        event_type: eventPayload.type,
        press_count: eventPayload.beatCount,
        respiration_bpm: eventPayload.respirationBpm,
        heart_rate_bpm: eventPayload.heartRateBpm,
        body_temp_c: eventPayload.bodyTempC,
        pressure_raw: eventPayload.pressureRaw,
        pressure_level: eventPayload.pressureLevel,
        ppg_ir: eventPayload.ppgIr,
        ppg_red: eventPayload.ppgRed,
        wearing: eventPayload.wearing,
        contact_present: eventPayload.contactPresent,
        device_timestamp: Date.now(),
        miniapp_timestamp: Date.now()
      },
      success: (result) => {
        const payload = result.result || {};
        this.setData({
          cloudStatus: payload.code === 200 ? '成功' : `失败: ${payload.msg || 'unknown'}`,
          storagePath: payload.storage_cloud_path || payload.storage_file_id || '未写入',
          llmReply: payload.llm_reply || '未返回文本'
        });
      },
      fail: (error) => this.setData({
        cloudStatus: `调用失败: ${error.errMsg}`,
        llmReply: '云函数调用失败'
      })
    });
  },

  disconnectDevice() {
    this.stopDiscovery();
    if (!this.data.deviceId) {
      return;
    }

    wx.closeBLEConnection({
      deviceId: this.data.deviceId,
      complete: () => this.setData({
        connectionStatus: '已断开',
        deviceId: '',
        serviceId: '',
        eventCharacteristicId: '',
        commandCharacteristicId: '',
        commandWriteType: 'write',
        canSendCommand: false,
        breathRunning: false,
        calibrationRunning: false
      })
    });
  }
});
