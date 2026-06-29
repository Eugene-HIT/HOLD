import sys

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add CMD_CHAR_UUID and InterruptAgent if missing
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
            try {
                audioTrack?.pause()
                audioTrack?.flush()
            } catch(e: Exception){}
        }
        isAIThinking = false
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
    }'''
    )

# 2. Replace the VAD 1.5s logic inside onDescriptorWrite (MIC)
old_vad = '''                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {
                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)'''
new_vad = '''                } else if (descriptor.characteristic.uuid == CMD_CHAR_UUID) {
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
if 'descriptor.characteristic.uuid == CMD_CHAR_UUID' not in text:
    text = text.replace(old_vad, new_vad)

# 3. Change UUID parsing in handleCharacteristicChange to handle CMD_CHAR_UUID, remove 1500 timeout from MIC
# Find the exact MIC block
old_mic_handler = '''            } else if (uuid == MIC_AUDIO_CHAR_UUID) {
                if (data.contentEquals(lastAudioData)) {
                    return
                }
                lastAudioData = data.clone()

                totalAudioBytes += data.size

                // 2. Hardware PTT Support logic
                if (isRecordingLocal) {
                    audioBufferQueue.add(data)
                } else {
                    if (data.size >= 5) {
                        var rms = 0.0
                        for (i in 0 until data.size step 2) {
                            if (i + 1 < data.size) {
                                val s = (data[i + 1].toInt() shl 8) or (data[i].toInt() and 0xFF)
                                rms += s * s
                            }
                        }
                        rms = Math.sqrt(rms / (data.size / 2))
                        val isTalking = rms > 1500.0

                        if (isTalking && !isAIThinking) {
                            silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                            if (!isRecordingLocal) {
                                isRecordingLocal = true
                                audioBufferQueue.clear()
                                runOnUiThread { tvAiStatus.text = "🎤 您正在讲话..." }
                            }
                            audioBufferQueue.add(data)
                        } else if (isRecordingLocal && !isTalking) {
                            audioBufferQueue.add(data)
                            silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                            silenceRunnable = Runnable {
                                isRecordingLocal = false
                                isAIThinking = true
                                runOnUiThread { tvAiStatus.text = "⏳ 打包上传 STT ..." }
                                processAndUploadAudio()
                            }
                            silenceHandler.postDelayed(silenceRunnable!!, 1500)
                        }
                    }
                }

                val now = System.currentTimeMillis()'''


# Wait, wait, actually let's see what is inside MainActivity_bot_mess.kt exactly around MIC_AUDIO_CHAR_UUID to make sure we replace perfectly!
