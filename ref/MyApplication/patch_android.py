import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

with codecs.open('old_block.txt', 'r', 'utf-8') as f:
    old_block = f.read()

new_func = r'''    private fun streamPcmToEsp32(audioBytes: ByteArray) {
        Thread {
            val gatt = bluetoothGatt
            val service = gatt?.getService(SERVICE_UUID)
            val spkChar = service?.getCharacteristic(SPK_AUDIO_CHAR_UUID)

            if (gatt != null && spkChar != null && audioBytes.isNotEmpty()) {
                val chunkSize = 240
                var offset = 0
                val startTimeMs = System.currentTimeMillis()
                var bytesSent = 0
                val batchSize = 4
                var chunksSentInBatch = 0

                isInterrupted = false
                while (offset < audioBytes.size) {
                    if (isInterrupted) {
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
                    }
                    offset += length
                    bytesSent += length
                    chunksSentInBatch++

                    if (chunksSentInBatch >= batchSize) {
                        val expectedElapsedMs = (bytesSent / 32.0).toLong() // 16000Hz 16bit = 32KB/s
                        val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                        val leadTimeMs = 100L
                        val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs                        
                        if (sleepTime > 5) {
                            try { Thread.sleep(sleepTime) } catch(e: Exception) {}
                        }
                        chunksSentInBatch = 0
                    }
                }
            }
        }.start()
    }'''

if old_block in text:
    replaced = text.replace(old_block, new_func)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(replaced)
    print('SUCCESSFULLY PATCHED AND WRITTEN!')
else:
    print('OLD BLOCK NOT FOUND IN TEXT!')

