# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

pattern = re.compile(r'val chunkSize = 240.*?\n\s+android\.util\.Log\.i\("BLE_DEBUG", "Sent PCM to ESP32\."\)', re.DOTALL)

new_block = '''// 💡 鸿蒙适配版：利用批次降低 sleep 调用，配合 65KB DMA 池
                val chunkSize = 240
                val batchSize = 4
                var batchCounter = 0
                var offset = 0
                var bytesSent = 0
                val startTimeMs = System.currentTimeMillis()

                while (offset < audioBytes.size) {
                    var length = Math.min(chunkSize, audioBytes.size - offset)
                    if (length % 2 != 0) length -= 1
                    if (length <= 0) break

                    val chunk = ByteArray(length)
                    System.arraycopy(audioBytes, offset, chunk, 0, length) 

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
                    batchCounter++

                    // 每发 batchSize 个包（约30ms音频）做一次时钟对齐，其余时间直接推入 65KB 硬件缓冲
                    if (batchCounter >= batchSize) {
                        batchCounter = 0
                        val expectedElapsedMs = (bytesSent / 32.0).toLong()
                        val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                        // 给 300ms 安全预取时间，不怕多送数据，硬件缓冲现在极大
                        val leadTimeMs = 300L 
                        val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                        if (sleepTime > 0) {
                            Thread.sleep(sleepTime)
                        } else {
                            Thread.sleep(4) // 遇到欠载休眠4ms，减少被系统降频的处罚
                        }
                    }
                }
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32 (HarmonyOS Batched + WideDMA Mode).")'''

text_normalized = text.replace('\r\n', '\n')
new_normalized = new_block.replace('\r\n', '\n')

matches = pattern.findall(text_normalized)
if matches:
    text_normalized = text_normalized.replace(matches[0], new_normalized)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text_normalized)
    print("PATCH APPLIED SUCCESSFULLY!")
else:
    print("MATCH NOT FOUND")

