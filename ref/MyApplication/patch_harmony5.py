# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

pattern = re.compile(r'// [^\n]*?鸿蒙适配版.*?\n\s+android\.util\.Log\.i\("BLE_DEBUG", "Sent PCM to ESP32 \(HarmonyOS Batched \+ WideDMA Mode\)\."\)', re.DOTALL)

new_block = '''// 💡 鸿蒙适配版 V2：精细限流版，防止栈溢出并利用大容量DMA
                val chunkSize = 240 // 7.5ms 的音频块
                val leadTimeMs = 150L // 允许提前缓存 150ms
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

                    val expectedElapsedMs = (bytesSent / 32.0).toLong()
                    val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                    val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                    if (sleepTime > 0) {
                        Thread.sleep(sleepTime) 
                    } else {
                        // 遇到落后或预载阶段，必须严格延迟至少2ms。
                        // 因为鸿蒙系统和部分安卓机的BLE无线队列极小，
                        // 无延迟连发（0ms间隙）会导致协议栈过载堵塞丢包，导致"沾满卡顿"
                        Thread.sleep(2)
                    }
                }
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32 (HarmonyOS Paced V2 Mode).")'''

text_normalized = text.replace('\r\n', '\n')
new_normalized = new_block.replace('\r\n', '\n')

matches = pattern.findall(text_normalized)
if matches:
    text_normalized = text_normalized.replace(matches[0], new_normalized)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text_normalized)
    print("PATCH APPLIED SUCCESSFULLY!")
else:
    print("MATCH NOT FOUND!")

