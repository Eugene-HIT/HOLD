import codecs

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

old_block = '''                // 🚀 恢复最初的单包发送大小
                val chunkSize = 240
                var offset = 0
                var bytesSent = 0
                val startTimeMs = System.currentTimeMillis()

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
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                    }

                    offset += length
                    bytesSent += length

                    // 🚀 完全恢复你最初在安卓上跑得最顺畅的神仙参数！
                    val expectedElapsedMs = (bytesSent / 32.0).toLong()
                    val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                    val leadTimeMs = 150L // 恢复 150ms 超大提前量缓冲
                    val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                    if (sleepTime > 0) {
                        try { Thread.sleep(sleepTime) } catch(e: Exception) {}  
                    } else {
                        // 恢复原生安卓最舒服的 2ms 微小让步休眠
                        try { Thread.sleep(2) } catch(e: Exception) {}
                    }
                }
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32 (Original Android Mode).")'''

new_block = '''                // 💡 鸿蒙适配版：利用批次降低 sleep 调用，配合 65KB DMA 池
                val chunkSize = 240
                val batchSize = 4
                var batchCounter = 0
                var offset = 0
                var bytesSent = 0
                val startTimeMs = System.currentTimeMillis()

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
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                    }

                    offset += length
                    bytesSent += length
                    batchCounter++

                    // 每发 batchSize 个包（约30ms音频）做一次时钟对齐，其余时间疯狂压榨 65KB 硬件缓冲
                    if (batchCounter >= batchSize) {
                        batchCounter = 0
                        val expectedElapsedMs = (bytesSent / 32.0).toLong()
                        val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                        // 预送量极大，不怕睡多
                        val leadTimeMs = 300L 
                        val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                        if (sleepTime > 0) {
                            try { Thread.sleep(sleepTime) } catch(e: Exception) {}  
                        } else {
                            try { Thread.sleep(3) } catch(e: Exception) {}
                        }
                    }
                }
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32 (HarmonyOS Batched + WideDMA Mode).")'''

if old_block in text:
    text = text.replace(old_block, new_block)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text)
    print("PATCH APPLIED SUCCESSFULLY!")
else:
    print("Failed to find exact block. Finding subset...")
    print(text.find('                // 🚀 恢复最初的单包发送大小'))
