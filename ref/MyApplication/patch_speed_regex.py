# -*- coding: utf-8 -*-
import codecs
import re

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

old_regex = r'// 强制等待上一个包真正离开手机底层发射队列。[\s\S]*?bleWriteSemaphore\.tryAcquire\(20,\s+java\.util\.concurrent\.TimeUnit\.MILLISECONDS\)[\s\S]*?Thread\.sleep\(12\)[\s\S]*?@SuppressLint\("MissingPermission"\)[\s\S]*?val result = gatt\.writeCharacteristic\(spkChar\)[\s\S]*?if \(!result\) \{[\s\S]*?// 若没塞进去，放回 Permit 给下一次重试，并稍微歇一帧[\s\S]*?bleWriteSemaphore\.release\(\)[\s\S]*?Thread\.sleep\(5\)[\s\S]*?\}[\s\S]*?\} catch \(e: Exception\) \{[\s\S]*?android\.util\.Log\.e\("BLE_DEBUG", "Error writing chunk: " \+ e\.message\)[\s\S]*?bleWriteSemaphore\.release\(\)[\s\S]*?\}[\s\S]*?offset \+= length'

new_repl = '''// 强制等待上一个包真正离开手机底层发射队列。
                        bleWriteSemaphore.tryAcquire(200, java.util.concurrent.TimeUnit.MILLISECONDS)

                        @SuppressLint("MissingPermission")
                        val result = gatt.writeCharacteristic(spkChar)
                        if (!result) {
                            // 若底层低功耗蓝牙缓存满了发不出去：释放permit，歇一会儿，并用 continue 阻止 offset 增加，达到重发同一包的目的，彻底告别丢包/快进死循环！
                            bleWriteSemaphore.release()
                            Thread.sleep(5)
                            continue
                        }
                    } catch (e: Exception) {
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                        bleWriteSemaphore.release()
                    }

                    offset += length'''

if re.search(old_regex, t):
    t = re.sub(old_regex, new_repl.replace('\n', '\r\n'), t)
    with codecs.open(p, 'w', 'utf-8') as f:
        f.write(t)
    print("Success Regex Replace")
else:
    print("Failed Regex")

