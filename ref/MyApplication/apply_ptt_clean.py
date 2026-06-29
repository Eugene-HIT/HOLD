import sys
import codecs

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add CMD_CHAR_UUID and InterruptAgent
if 'private val CMD_CHAR_UUID' not in text:
    text = text.replace(
        'private val CAM_IMAGE_CHAR_UUID = UUID.fromString("19B10004-E8F2-537E-4F6C-D104768A1214")',
        'private val CAM_IMAGE_CHAR_UUID = UUID.fromString("19B10004-E8F2-537E-4F6C-D104768A1214")\n    private val CMD_CHAR_UUID = UUID.fromString("19B10005-E8F2-537E-4F6C-D104768A1214")'
    )

if 'private fun InterruptAgent()' not in text:
    text = text.replace(
        'class MainActivity : AppCompatActivity() {',
        '''class MainActivity : AppCompatActivity() {
    private fun InterruptAgent() {
        runOnUiThread {
            tvStatus.text = "检测到硬件中断 (0x02)"
            tvAiStatus.text = "硬件触发，正在录音中..."
            try {
                audioTrack?.pause()
                audioTrack?.flush()
            } catch(e: Exception){}
        }
        isAIThinking = false
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
    }'''
    )

# 2. Add CMD_CHAR_UUID descriptor
old_cmd_desc = '''                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {
                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)'''
new_cmd_desc = '''                } else if (descriptor.characteristic.uuid == CMD_CHAR_UUID) {
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
                    }
                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {
                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)'''
if 'characteristic.uuid == CMD_CHAR_UUID' not in text:
    text = text.replace(old_cmd_desc, new_cmd_desc)

# 3. Remove 1500 timeout and replace with CMD_CHAR_UUID logic
idx_start = text.find('// 2. 16-bit VAD AI Logic')
if idx_start != -1:
    idx_end = text.find('val now = System.currentTimeMillis()', idx_start)
    if idx_end != -1:
        pure_mic_logic = '''// 2. Hardware PTT Support logic
                if (isRecordingLocal) {
                    audioBufferQueue.add(data)
                }

                '''
        text = text[:idx_start] + pure_mic_logic + text[idx_end:]

# 4. Insert CMD_CHAR_UUID parse block before MIC_AUDIO_CHAR_UUID parse
cmd_parse_block = '''              } else if (uuid == CMD_CHAR_UUID) {
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
if 'uuid == CMD_CHAR_UUID' not in text:
    text = text.replace('              } else if (uuid == MIC_AUDIO_CHAR_UUID) {', cmd_parse_block)

# Remove the resetAI(1500) usages
text = text.replace('resetAI(1500)', 'resetAI(1500) // Changed by PTT patch but kept for backwards compatibility if needed anywhere else, though VAD is gone')

with codecs.open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Restored PTT interrupt logic inside original user-requested UI!")
