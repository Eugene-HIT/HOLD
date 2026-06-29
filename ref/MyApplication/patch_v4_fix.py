# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

pattern = re.compile(r'try \{\s*// 强制等待上一个包真正离开手机.*?\s*offset \+= length', re.DOTALL)

fixed_block = '''try {
                        // 强制等待上一个包真正离开手机底层发射队列。
                        val acquired = bleWriteSemaphore.tryAcquire(200, java.util.concurrent.TimeUnit.MILLISECONDS)
                        if (!acquired) {
                            // 极其罕见：手机底层卡死了200ms还没发出去，为了防死任务强制推进，但保留一点缓冲
                            bleWriteSemaphore.release() 
                        }
                        
                        @SuppressLint("MissingPermission")
                        val result = gatt.writeCharacteristic(spkChar)
                        if (!result) {
                            // 若没塞进去，放回 Permit 给下一次重试，不推进 offset (重传本包)
                            bleWriteSemaphore.release()
                            Thread.sleep(5)
                            continue // 核心修复：没发出去就必须重试本包，否则就是跳包(俗称倍速变音)！
                        }
                        
                        // 发送成功，正常推进位移
                        offset += length
                    } catch (e: Exception) {
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                        bleWriteSemaphore.release()
                        offset += length // 遇到崩溃等异常，不得已跳过
                    }'''

text_normalized = text.replace('\r\n', '\n')
fixed_normalized = fixed_block.replace('\r\n', '\n')

matches = pattern.findall(text_normalized)
if matches:
    text_normalized = text_normalized.replace(matches[0], fixed_normalized)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text_normalized)
    print("PATCH APPLIED SUCCESSFULLY!")
else:
    print("MATCH NOT FOUND")
