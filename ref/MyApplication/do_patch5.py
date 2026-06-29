import sys
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add CMD_CHAR_UUID
code = code.replace(
    'private val CAM_IMAGE_CHAR_UUID = UUID.fromString("19B10004-E8F2-537E-4F6C-D104768A1214")',
    'private val CAM_IMAGE_CHAR_UUID = UUID.fromString("19B10004-E8F2-537E-4F6C-D104768A1214")\n    private val CMD_CHAR_UUID = UUID.fromString("19B10005-E8F2-537E-4F6C-D104768A1214")'
)

# 2. Subscribe to CMD_CHAR_UUID
cam_sub_old = '''                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {
                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)
                    if (camChar != null) {
                        gatt.setCharacteristicNotification(camChar, true)       
                        val camDec = camChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(camDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            camDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(camDec)
                        }
                        runOnUiThread { tvStatus.text = "Camera Data" }
                    }'''
cam_sub_new = '''                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {
                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)
                    if (camChar != null) {
                        gatt.setCharacteristicNotification(camChar, true)       
                        val camDec = camChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(camDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            camDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(camDec)
                        }
                        runOnUiThread { tvStatus.text = "Camera Data" }
                    }
                } else if (descriptor.characteristic.uuid == CAM_IMAGE_CHAR_UUID) {
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
                    }'''
code = code.replace(cam_sub_old, cam_sub_new)

vad_old = re.compile(r'//\s*2\.\s*16-bit\s*VAD\s*AI\s*Logic.*?(?=val now = System\.currentTimeMillis\(\))', re.DOTALL)
vad_new = '''// 2. Hardware PTT Support logic
                if (isRecordingLocal) {
                    audioBufferQueue.add(data)
                }

                '''
code = vad_old.sub(vad_new, code)

mic_handler_old = '''              } else if (uuid == MIC_AUDIO_CHAR_UUID) {'''
cmd_handler_new = '''              } else if (uuid == CMD_CHAR_UUID) {
                  if (data.isNotEmpty() && data[0] == 0x02.toByte()) {
                      InterruptAgent()
                      isRecordingLocal = true
                      audioBufferQueue.clear()
                      runOnUiThread { tvAiStatus.text = "🎤 硬件端正在讲话..." }
                  } else if (data.isNotEmpty() && data[0] == 0x03.toByte()) {
                      if (isRecordingLocal) {
                          isRecordingLocal = false
                          isAIThinking = true
                          runOnUiThread { tvAiStatus.text = "⏳ 打包上传音频推给 STT ..." }
                          processAndUploadAudio()
                      }
                  }
              } else if (uuid == MIC_AUDIO_CHAR_UUID) {'''
code = code.replace(mic_handler_old, cmd_handler_new)

interrupt_agent = '''
    private fun InterruptAgent() {
        runOnUiThread {
            tvStatus.text = "检测到硬件中断 (0x02)"
            tvAiStatus.text = "用户语音输入触发中..."
            audioTrack?.pause()
            audioTrack?.flush()
        }
        isAIThinking = false
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
    }'''
if 'InterruptAgent' not in code:
    code = code.replace('class MainActivity : AppCompatActivity() {', 'class MainActivity : AppCompatActivity() {' + interrupt_agent)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch generated.")
