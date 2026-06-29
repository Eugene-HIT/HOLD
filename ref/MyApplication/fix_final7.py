import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace BLE writing block using Regex
write_pattern = r'spkChar\.writeType = BluetoothGattCharacteristic\.WRITE_TYPE_NO_RESPONSE\s*try \{\s*@SuppressLint\("MissingPermission"\)\s*val result = gatt\.writeCharacteristic\(spkChar\)\s*\} catch \(e: Exception\) \{\s*android\.util\.Log\.e\("BLE_DEBUG", "Error writing chunk: " \+ e\.message\)\s*\}'

new_write = '''spkChar.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                      
                      var success = false
                      var retryCount = 0
                      while (!success && retryCount < 100) {
                          try {
                              @SuppressLint("MissingPermission")
                              val result = gatt.writeCharacteristic(spkChar)
                              if (result) {
                                  success = true
                              } else {
                                  // 关键修复点：安卓系统底层的 BLE 发送缓存(内存)满了！
                                  // 如果不在这里等待并重试，这个数据包就被直接丢弃了（所以前半段不卡，后半段缓存满了就开始疯狂丢包导致极度卡顿爆音）。
                                  Thread.sleep(12) 
                                  retryCount++
                              }
                          } catch (e: Exception) {
                              android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                              break
                          }
                      }'''

text = re.sub(write_pattern, new_write, text, flags=re.DOTALL)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Retry loop applied successfully!")
