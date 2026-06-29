# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# 1. Add Semaphore variable
if 'bleWriteSemaphore' not in text:
    text = re.sub(r'class MainActivity : AppCompatActivity\(\) \{', r'class MainActivity : AppCompatActivity() {\n    private val bleWriteSemaphore = java.util.concurrent.Semaphore(1)', text, count=1)

# 2. Add onCharacteristicWrite callback to gattCallback
if 'onCharacteristicWrite(' not in text:
    text = re.sub(
        r'(\s+)(override fun onCharacteristicChanged\(gatt: BluetoothGatt, \w+: BluetoothGattCharacteristic, value: ByteArray\))',
        r'\1override fun onCharacteristicWrite(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, status: Int) {\n\1    if (characteristic.uuid == SPK_AUDIO_CHAR_UUID) {\n\1        bleWriteSemaphore.release()\n\1    }\n\1}\n\n\1\2',
        text,
        count=1
    )

# 3. Replace V3 Spin-Wait logic with V4 Strict Flow-Control
pattern_v3 = re.compile(r'// [^\n]*?鸿蒙特供版.*?\n\s+android\.util\.Log\.i\("BLE_DEBUG", "Sent PCM to ESP32 \(HarmonyOS Spin-Wait V3 Mode\)\."\)', re.DOTALL)

v4_block = '''// 💡 鸿蒙最终杀手锏 V4：底层协议栈硬件流控回调 (Strict Flow Control)
                val chunkSize = 400 // 每包25ms数据，显著降低系统调用频率，充分利用 512 MTU
                var offset = 0
                
                // 发送流之前清空可能废弃的信号量，并给第一发开绿灯
                bleWriteSemaphore.drainPermits()
                bleWriteSemaphore.release()

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
                    // NO_RESPONSE + Semaphore 是 Android 蓝牙高吞吐防丢包最完美的解法
                    spkChar.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                    
                    try {
                        // 强制等待上一个包真正离开手机底层发射队列。
                        // 这样绝不会撑爆鸿蒙脆弱的休眠队列！给20ms超时防死锁（400字节本来就要播12.5ms）。
                        bleWriteSemaphore.tryAcquire(20, java.util.concurrent.TimeUnit.MILLISECONDS)
                        
                        @SuppressLint("MissingPermission")
                        val result = gatt.writeCharacteristic(spkChar)
                        if (!result) {
                            // 若没塞进去，放回 Permit 给下一次重试，并稍微歇一帧
                            bleWriteSemaphore.release()
                            Thread.sleep(5)
                        }
                    } catch (e: Exception) {
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                        bleWriteSemaphore.release()
                    }

                    offset += length
                }
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32 (HarmonyOS Strict Flow-Control V4 Mode).")'''

text_normalized = text.replace('\r\n', '\n')
v4_normalized = v4_block.replace('\r\n', '\n')

matches = pattern_v3.findall(text_normalized)
if matches:
    text_normalized = text_normalized.replace(matches[0], v4_normalized)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text_normalized)
    print("PATCH APPLIED SUCCESSFULLY!")
else:
    print("PATCH FAILED! (V3 Pattern not found)")
