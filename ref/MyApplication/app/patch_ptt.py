import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Add imports if missing
imports = [
    "import android.media.AudioRecord",
    "import android.media.MediaRecorder",
    "import java.io.ByteArrayOutputStream",
    "import android.view.MotionEvent"
]

for imp in imports:
    if imp not in content:
        content = content.replace("import android.media.AudioTrack\n", f"import android.media.AudioTrack\n{imp}\n")

# Add class fields
new_fields = '''
    private var pttAudioRecord: AudioRecord? = null
    private var isRecordingPtt = false
    private val pttAudioBuffer = ByteArrayOutputStream()
'''
content = re.sub(r'(private var isPlayingAudio = false\n)', r'\1' + new_fields, content)

# Add UI binding and Event Listener
ui_binding = '''
        val btnPushToTalk: Button = findViewById(R.id.btnPushToTalk)
        btnPushToTalk.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    btnPushToTalk.text = "录音中..."
                    startPttRecording()
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    btnPushToTalk.text = "按住录音，松开发送"
                    stopPttRecordingAndSend()
                    true
                }
                else -> false
            }
        }
'''
content = re.sub(r'(btnScan = findViewById\(R\.id\.btnScan\)\n)', r'\1' + ui_binding, content)

# Extract stream method
extract_stream = '''
    private fun streamPcmToEsp32(audioBytes: ByteArray) {
        Thread {
            val gatt = bluetoothGatt
            val service = gatt?.getService(SERVICE_UUID)
            val spkChar = service?.getCharacteristic(SPK_AUDIO_CHAR_UUID)

            if (gatt != null && spkChar != null && audioBytes.isNotEmpty()) {
                val chunkSize = 240
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
                        // Suppress permission check error
                        @SuppressLint("MissingPermission")
                        val result = gatt.writeCharacteristic(spkChar)
                    } catch (e: Exception) {
                        Log.e("BLE_DEBUG", "Error writing audio chunk: ")
                    }

                    offset += length
                    bytesSent += length

                    val expectedElapsedMs = (bytesSent / 44.1).toLong()
                    val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                    val leadTimeMs = 600L
                    val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                    if (sleepTime > 0) {
                        Thread.sleep(sleepTime)
                    } else {
                        Thread.sleep(2)
                    }
                }
                Log.i("BLE_DEBUG", "Sent PTT/AI audio to ESP32.")
            } else {
                Log.e("BLE_DEBUG", "Cannot stream to ESP32, missing GATT or SPK Char.")
            }
        }.start()
    }

    @SuppressLint("MissingPermission")
    private fun startPttRecording() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "请先授予录音权限", Toast.LENGTH_SHORT).show()
            return
        }
        val minBufSize = AudioRecord.getMinBufferSize(22050, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        pttAudioRecord = AudioRecord(MediaRecorder.AudioSource.MIC, 22050, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, minBufSize)
        pttAudioBuffer.reset()
        isRecordingPtt = true
        pttAudioRecord?.startRecording()
        Thread {
            val buffer = ByteArray(minBufSize)
            while (isRecordingPtt) {
                val read = pttAudioRecord?.read(buffer, 0, buffer.size) ?: 0
                if (read > 0) {
                    pttAudioBuffer.write(buffer, 0, read)
                }
            }
        }.start()
    }

    private fun stopPttRecordingAndSend() {
        isRecordingPtt = false
        pttAudioRecord?.stop()
        pttAudioRecord?.release()
        pttAudioRecord = null
        val recordedBytes = pttAudioBuffer.toByteArray()
        if (recordedBytes.isNotEmpty()) {
            streamPcmToEsp32(recordedBytes)
        }
    }
'''

content = content.replace("private fun processAndUploadAudio() {", extract_stream + "\n    private fun processAndUploadAudio() {")

# Refactor playBase64Audio to use streamPcmToEsp32
refactor_stream = '''
            // Stream to ESP32 over BLE
            Thread {
                val gatt = bluetoothGatt
                val service = gatt?.getService(SERVICE_UUID)
                val spkChar = service?.getCharacteristic(SPK_AUDIO_CHAR_UUID)

                if (gatt != null && spkChar != null && audioBytes.size > 44) {
                    val pcmBytes = ByteArray(audioBytes.size - 44)
                    System.arraycopy(audioBytes, 44, pcmBytes, 0, pcmBytes.size)
                    streamPcmToEsp32(pcmBytes)
                } else {
                    Log.e("BLE_DEBUG", "Cannot stream to ESP32, missing GATT or SPK Char.")
                }
            }.start()
'''

# Wait, we need to replace the old stream logic.
# I'll just use regex to replace it
content = re.sub(r'// Stream to ESP32 over BLE[\s\S]*?Log\.i\("BLE_DEBUG", "Sent all AI audio chunks to ESP32\."\)[\s\S]*?\} else \{[\s\S]*?Log\.e\("BLE_DEBUG", "Cannot stream to ESP32, missing GATT or SPK Char\."\)[\s\S]*?\}.start\(\)', refactor_stream, content)

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)
