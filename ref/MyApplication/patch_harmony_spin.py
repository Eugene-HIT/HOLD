# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

pattern = re.compile(r'// [^\n]*?鸿蒙适配版.*?\n\s+android\.util\.Log\.i\("BLE_DEBUG", "Sent PCM to ESP32 \(HarmonyOS Paced V2 Mode\)\."\)', re.DOTALL)

new_block = '''// 💡 鸿蒙特供版 V3：使用“自旋锁(Spin-Wait)”绕过OS睡眠惩罚
                val chunkSize = 240 // 7.5ms 的音频块
                val leadTimeMs = 400L // 放宽预存，由巨大硬件缓冲兜底
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
                    val sleepTimeMs = expectedElapsedMs - leadTimeMs - actualElapsedMs

                    if (sleepTimeMs > 20) {
                        // 只有非常大的等待（大于20ms）才交出CPU执行权
                        // 扣除掉15ms作为缓冲，防止系统一下睡过头
                        Thread.sleep(sleepTimeMs - 15)
                    }
                    
                    // 核心黑科技：精确到纳秒的空转（Busy-Wait）。
                    // 鸿蒙系统没法剥夺正在死循环的CPU周期。这保证了哪怕是2ms的延迟也能精准实现。
                    // 也是为了给底层蓝牙协议栈留出射频清理TX队列的喘息时间，防止瞬间撑爆。
                    var remainingNano = (expectedElapsedMs - leadTimeMs - (System.currentTimeMillis() - startTimeMs)) * 1_000_000L
                    if (remainingNano < 2_500_000L) {
                        remainingNano = 2_500_000L // 保底锁定绝对 2.5ms 的硬件发包处理时间
                    }
                    
                    val targetNano = System.nanoTime() + remainingNano
                    while (System.nanoTime() < targetNano) {
                        // 自旋空转，强占CPU度过微秒级岁月
                    }
                }
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32 (HarmonyOS Spin-Wait V3 Mode).")'''

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
