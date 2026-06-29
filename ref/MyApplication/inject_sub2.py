import codecs
p = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(p, 'r', encoding='utf-8') as f:
    text = f.read()

idx_imu = text.find('if (descriptor.characteristic.uuid == IMU_CHAR_UUID) {')
idx_cam = text.find('val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)')

if idx_imu != -1 and idx_cam != -1:
    new_chain = '''if (descriptor.characteristic.uuid == IMU_CHAR_UUID) {
                    val cmdChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CMD_CHAR_UUID)
                    if (cmdChar != null) {
                        gatt.setCharacteristicNotification(cmdChar, true)
                        val cmdDec = cmdChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(cmdDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            cmdDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(cmdDec)
                        }
                    }
                } else if (descriptor.characteristic.uuid == CMD_CHAR_UUID) {
                    val audioChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(MIC_AUDIO_CHAR_UUID)
                    if (audioChar != null) {
                        gatt.setCharacteristicNotification(audioChar, true)
                        val audioDec = audioChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(audioDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            audioDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(audioDec)
                        }
                        runOnUiThread { tvStatus.text = "已成功订阅全部数据流！" }
                    }
                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {
                    '''
    text = text[:idx_imu] + new_chain + text[idx_cam:]
    with codecs.open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected perfectly.")
