# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

old_loop = '''                        // 强制等待上一个包真正离开手机底层发射队列。
                        bleWriteSemaphore.tryAcquire(20, java.util.concurrent.TimeUnit.MILLISECONDS)
                        
                        // 🌟 解决硬件播放“加速、跳包”问题：强行做发流限速 (Pacing)。
                        // 400字节 = 12.5ms 的播放量。如果发太快 ESP32 蓝牙缓冲会爆掉直接丢包，导致声音变细变快。
                        // 这里我们加上强制 10-12ms 的休眠，完美匹配它的真实播放速度 (软实时)。
                        Thread.sleep(12)

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

                    offset += length'''

new_loop = '''                        // 强制等待上一个包真正离开手机底层发射队列。给200ms超时防死锁。
                        bleWriteSemaphore.tryAcquire(200, java.util.concurrent.TimeUnit.MILLISECONDS)

                        @SuppressLint("MissingPermission")
                        val result = gatt.writeCharacteristic(spkChar)
                        if (!result) {
                            // 若没塞进去，这是底层低功耗蓝牙缓存满了，直接 continue 重试这个块，坚决不能增加 offset 丢包！
                            bleWriteSemaphore.release()
                            Thread.sleep(5)
                            continue
                        }
                    } catch (e: Exception) {
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                        bleWriteSemaphore.release()
                    }

                    offset += length'''

if old_loop in t:
    t = t.replace(old_loop, new_loop)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(t)
    print("Patched pacing success")
else:
    print("Failed string match. Trying CRLF...")
    old_loop_crlf = old_loop.replace('\n', '\r\n')
    new_loop_crlf = new_loop.replace('\n', '\r\n')
    if old_loop_crlf in t:
        t = t.replace(old_loop_crlf, new_loop_crlf)
        with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
            f.write(t)
        print("Patched pacing success with CRLF")
    else:
        print("Total failure.")
