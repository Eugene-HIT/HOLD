import re

kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_code = f.read()

# 1. Add CMD_CHAR_UUID
if 'CMD_CHAR_UUID' not in kt_code:
    kt_code = kt_code.replace(
        'private val CAM_IMAGE_CHAR_UUID = UUID.fromString("19B10004-E8F2-537E-4F6C-D104768A1214")',
        'private val CAM_IMAGE_CHAR_UUID = UUID.fromString("19B10004-E8F2-537E-4F6C-D104768A1214")\n      private val CMD_CHAR_UUID = UUID.fromString("19B10005-E8F2-537E-4F6C-D104768A1214")'
    )

# 2. Add subscription logic
sub_old = '''                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)
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

sub_new = '''                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)
                      if (camChar != null) {
                          gatt.setCharacteristicNotification(camChar, true)     
                          val camDec = camChar.getDescriptor(CCCD_UUID)
                          if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                              gatt.writeDescriptor(camDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                          } else {
                              camDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                              gatt.writeDescriptor(camDec)
                          }
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
                          runOnUiThread { tvStatus.text = "All Subscribed" }
                      }'''

kt_code = kt_code.replace(sub_old, sub_new)

# 3. Add handler for CMD_CHAR_UUID + interrupt logic
cmd_handler = '''            } else if (uuid == CMD_CHAR_UUID) {
                  if (data.isNotEmpty() && data[0].toInt() == 0x02) {
                      android.util.Log.i("AI_DEBUG", "HARDWARE LONG PRESS INTERRUPT")
                      isInterrupted = true
                      isPlayingAudio = false
                      isAIThinking = false
                      try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
                      try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
                      writeSemaphore.release(100) // free TTS stream lock
                      
                      runOnUiThread { tvAiStatus.text = "🚫已打断AI，重新倾听中..." }
                      isRecordingLocal = true
                      audioBufferQueue.clear()
                  }
'''

if 'uuid == CMD_CHAR_UUID' not in kt_code:
    kt_code = kt_code.replace(
        '} else if (uuid == MIC_AUDIO_CHAR_UUID)',
        cmd_handler + '              } else if (uuid == MIC_AUDIO_CHAR_UUID)'
    )

# 4. ensure Volatile isInterrupted is there
if '@Volatile private var isInterrupted = false' not in kt_code:
    kt_code = kt_code.replace('private var isAIThinking = false', 'private var isAIThinking = false\n      @Volatile private var isInterrupted = false')

# 5. Add to streamPcmToEsp32 break
if 'if (isInterrupted) break' not in kt_code:
    kt_code = kt_code.replace('while (offset < audioBytes.size) {', 'while (offset < audioBytes.size) {\n                      if (isInterrupted) break')

# 6. Reset isInterrupted on stream start
if 'isInterrupted = false' not in kt_code.split('streamPcmToEsp32')[1][:200]:
    kt_code = kt_code.replace('writeSemaphore.release() // Allow the first chunk to proceed immediately', 'isInterrupted = false\n                  writeSemaphore.release() // Allow the first chunk to proceed immediately')

# 7. VAD Rewrite
start_str = "if (!isAIThinking) {"
end_str = "val now = System.currentTimeMillis()"

start_idx = kt_code.find(start_str)
end_idx = kt_code.find(end_str, start_idx)

new_block = '''if (!isAIThinking) {
                    var maxEnergy = 0
                    val shortBuffer = java.nio.ByteBuffer.wrap(data).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                    while (shortBuffer.hasRemaining()) {
                        val energy = Math.abs(shortBuffer.get().toInt())
                        if (energy > maxEnergy) maxEnergy = energy
                    }

                    if (isRecordingLocal) {
                        audioBufferQueue.add(data)
                        
                        if (maxEnergy > 800) {
                            silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                            silenceRunnable = Runnable {
                                if (isAIThinking) return@Runnable
                                android.util.Log.i("AI_DEBUG", "VAD trigger silence end")
                                isRecordingLocal = false
                                isAIThinking = true
                                playbackBuffer.reset()
                                try { audioTrack?.pause(); audioTrack?.flush(); if (isPlayingAudio) audioTrack?.play() } catch (e: Exception) {}
                                runOnUiThread { tvAiStatus.text = "打包上传音频推给 STT..." }
                                processAndUploadAudio()
                            }
                            silenceHandler.postDelayed(silenceRunnable!!, 2500)
                        }
                    }
                }

                  '''
kt_code = kt_code[:start_idx] + new_block + kt_code[end_idx:]

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_code)

print("All Android patches applied dynamically!")