import codecs

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

start_str = 'spkChar.value = chunk'
old_block_end = 'android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)\n\n                    }'
start_idx = text.find(start_str)
end_idx = text.find(old_block_end, start_idx)

if start_idx != -1 and end_idx != -1:
    end_idx += len(old_block_end)
    replaced = text[start_idx:end_idx]
    
    new_write = '''spkChar.value = chunk
                    spkChar.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                    var success = false
                    var retryCount = 0
                    while (!success && retryCount < 50) {
                        try {
                            @SuppressLint("MissingPermission")
                            val result = gatt.writeCharacteristic(spkChar)
                            if (result) {
                                success = true
                            } else {
                                Thread.sleep(2)
                                retryCount++
                            }
                        } catch (e: Exception) {
                            android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                            break
                        }
                    }
                    if (!success) {
                        android.util.Log.e("BLE_DEBUG", "Dropped audio chunk after 50 retries")
                    }'''
                    
    text = text[:start_idx] + new_write + text[end_idx:]
    
    text = text.replace('@Volatile private var isInterrupted = false', 
                        '@Volatile private var isInterrupted = false\n\n    @Volatile private var negotiatedMtu = 240')
    
    # Use generic string for onMtuChanged
    text = text.replace('android.util.Log.i("BLE_DEBUG", "MTU changed to: " + mtu + "\\", Status: " + status)',
                        'android.util.Log.i("BLE_DEBUG", "MTU changed to: " + mtu + "\\", Status: " + status)\n            negotiatedMtu = mtu')
    
    text = text.replace('val chunkSize = 240 // 回退到240：为了保证跨手机兼容性，因为很多手机的底层并不能完美支持拉满 490 的 MTU',
                        'val chunkSize = Math.min(240, negotiatedMtu - 3) // 自适应 MTU 切片，最大发 240，防止超出底层缓冲区')
    
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text)
    
    print('PATCH SUCCESSFUL')
else:
    print('Cannot find boundaries', start_idx, end_idx)
