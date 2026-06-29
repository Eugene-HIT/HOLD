import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

new_func = r'''    private fun streamPcmToEsp32(audioBytes: ByteArray) {
        Thread {
            val gatt = bluetoothGatt
            val service = gatt?.getService(SERVICE_UUID)
            val spkChar = service?.getCharacteristic(SPK_AUDIO_CHAR_UUID)

            if (gatt != null && spkChar != null && audioBytes.isNotEmpty()) {
                val chunkSize = 240 // 恢复单包发送，绝不连发
                var offset = 0
                val startTimeMs = System.currentTimeMillis()
                var bytesSent = 0

                isInterrupted = false
                while (offset < audioBytes.size) {
                    if (isInterrupted) {
                        break
                    }
                    var length = Math.min(chunkSize, audioBytes.size - offset)
                    if (length % 2 != 0) length -= 1
                    if (length <= 0) break

                    val chunk = ByteArray(length)
                    System.arraycopy(audioBytes, offset, chunk, 0, length)

                    // 硬件音量调整逻辑保持不变
                    if (hardwareVolumeMultiplier != 1.0f) {
                        try {
                            val shortBuffer = java.nio.ByteBuffer.wrap(chunk).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                            val shortArray = ShortArray(shortBuffer.capacity())
                            shortBuffer.get(shortArray)
                            for (i in shortArray.indices) {
                                var v = (shortArray[i] * hardwareVolumeMultiplier).toInt()
                                if (v > 32767) v = 32767
                                if (v < -32768) v = -32768
                                shortArray[i] = v.toShort()
                            }
                            java.nio.ByteBuffer.wrap(chunk).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(shortArray)
                            val modifiedBytes = ByteArray(shortArray.size * 2)
                            java.nio.ByteBuffer.wrap(modifiedBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(shortArray)
                            System.arraycopy(modifiedBytes, 0, chunk, 0, length)
                        } catch(e: Exception) {}
                    }

                    spkChar.value = chunk
                    spkChar.writeType = android.bluetooth.BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                    try {
                        @Suppress("MISSING_PERMISSION")
                        gatt.writeCharacteristic(spkChar)
                    } catch (e: Exception) {
                    }
                    
                    offset += length
                    bytesSent += length

                    // 🚀 核心降速区：绝对匀速的“滴流控制”
                    val expectedElapsedMs = (bytesSent * 1000L) / 32000L // 16kHz 16bit 每秒32000字节
                    val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                    val leadTimeMs = 40L // 只允许底层有 40ms（大约 1200 字节）的轻微超前量
                    
                    val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs                        
                    
                    if (sleepTime > 0) {
                        // 如果发得太快，严格等待
                        try { Thread.sleep(sleepTime) } catch(e: Exception) {}
                    } else {
                        // 🌟 最关键的防抖：哪怕发落后了，也【强制】休息 4 毫秒！
                        // 绝不允许 while 循环因为追赶时间而发生连续狂发，彻底杜绝瞬间拥堵
                        try { Thread.sleep(4) } catch(e: Exception) {}
                    }
                }
            }
        }.start()
    }'''

pattern = r'    private fun streamPcmToEsp32\(audioBytes: ByteArray\) \{.*?(?=    @SuppressLint\(\"MissingPermission\"\)\r?\n\r?\n    private fun startPttRecording\(\))'
match = re.search(pattern, text, re.DOTALL)
if match:
    text = text[:match.start()] + new_func + '\n\n' + text[match.end():]
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text)
    print('PATCH APPLIED!')
else:
    print('COULD NOT MATCH FUNCTION!')

