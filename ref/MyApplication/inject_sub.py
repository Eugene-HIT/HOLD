import codecs
p = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(p, 'r', encoding='utf-8') as f:
    text = f.read()

old_chain = '''                if (descriptor.characteristic.uuid == IMU_CHAR_UUID) {
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
                        runOnUiThread { tvStatus.text = "已成功订阅雷达与音频数据流！" }
                    }
                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {'''

new_chain = '''                if (descriptor.characteristic.uuid == IMU_CHAR_UUID) {
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
                        runOnUiThread { tvStatus.text = "已成功订阅雷达、指令与音频数据流！" }
                    }
                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {'''

if old_chain in text: 
    text = text.replace(old_chain, new_chain)
    with codecs.open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected CMD_CHAR_UUID subscription chain successfully!")
else:
    print("Couldn't find the target string. Maybe already injected or spacing is off.")
