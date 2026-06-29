import codecs

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

start_str = '    private fun streamPcmToEsp32(audioBytes: ByteArray) {'
start_idx = text.find(start_str)

end_str = '.start()\n\n    }'
end_idx = text.find(end_str, start_idx) + len(end_str)

# Double check context
print(text[start_idx:start_idx+100])
print('---')
print(text[end_idx-100:end_idx+20])

new_func = '''    private fun streamPcmToEsp32(audioBytes: ByteArray) {
        Thread {
            val gatt = bluetoothGatt
            val service = gatt?.getService(SERVICE_UUID)
            val spkChar = service?.getCharacteristic(SPK_AUDIO_CHAR_UUID)

            if (gatt != null && spkChar != null && audioBytes.isNotEmpty()) {
                val chunkSize = 240 
                var offset = 0
                var bytesSent = 0
                val startTimeMs = System.currentTimeMillis()
                
                // 🚀 新增：批处理引擎变量
                val batchSize = 4 // 每次连发 4 个包再休息，减少线程睡眠的碎片化
                var chunksSentInBatch = 0

                isInterrupted = false
                while (offset < audioBytes.size) {
                    if (isInterrupted) {
                        android.util.Log.i("AI_DEBUG", "BLE Streaming Interrupted!")
                        break
                    }
                    var length = Math.min(chunkSize, audioBytes.size - offset)
                    if (length % 2 != 0) length -= 1
                    if (length <= 0) break

                    val chunk = ByteArray(length)
                    System.arraycopy(audioBytes, offset, chunk, 0, length)

                    // 音量缩放逻辑保持不变
                    if (hardwareVolumeMultiplier != 1.0f) {
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
                    }

                    spkChar.value = chunk
                    spkChar.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                    try {
                        @SuppressLint("MissingPermission")
                        val result = gatt.writeCharacteristic(spkChar)
                    } catch (e: Exception) {
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                    }

                    offset += length
                    bytesSent += length
                    chunksSentInBatch++

                    // 🚀 核心优化：凑够一批包，才进行一次时间效验和睡眠
                    if (chunksSentInBatch >= batchSize) {
                        val expectedElapsedMs = (bytesSent / 32.0).toLong() // 16000Hz 16bit = 32KB/s
                        val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                        val leadTimeMs = 100L // 稍微缩短一点提前量，防止压爆底层缓冲区
                        val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                        // 只有当需要等待的时间大于 5 毫秒时才去睡，彻底避开鸿蒙微小睡眠的不精确问题
                        if (sleepTime > 5) {
                            Thread.sleep(sleepTime)
                        }
                        // 批次清零，准备下一波爆发
                        chunksSentInBatch = 0
                    }
                }
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32 (Optimized Batch Mode).")
            }
        }.start()

    }'''

if start_idx != -1 and end_idx > start_idx:
    replaced = text[:start_idx] + new_func + text[end_idx:]
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(replaced)
    print('PATCH APPLIED')
else:
    print('COULD NOT FIND BLOCK')
