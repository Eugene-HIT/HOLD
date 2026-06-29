# -*- coding: utf-8 -*-
import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

imports = '''import android.media.AudioRecord
import android.media.MediaRecorder
import java.io.ByteArrayOutputStream
import android.view.MotionEvent
'''
content = content.replace('import android.media.AudioTrack', 'import android.media.AudioTrack\n' + imports)

new_fields = '''
    private var pttAudioRecord: AudioRecord? = null
    private var isRecordingPtt = false
    private val pttAudioBuffer = ByteArrayOutputStream()
'''
content = re.sub(r'(private var isPlayingAudio = false\n)', r'\1' + new_fields, content)

ui_binding = '''
        val btnPushToTalk: Button = findViewById(R.id.btnPushToTalk)
        btnPushToTalk.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    btnPushToTalk.text = "Recording..."
                    startPttRecording()
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    btnPushToTalk.text = "Hold to Talk"
                    stopPttRecordingAndSend()
                    true
                }
                else -> false
            }
        }
'''
content = re.sub(r'(btnScan = findViewById\(R\.id\.btnScan\))', r'\1' + ui_binding, content)

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
                        @SuppressLint("MissingPermission")
                        val result = gatt.writeCharacteristic(spkChar)
                    } catch (e: Exception) {
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
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
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32.")
            }
        }.start()
    }

    @SuppressLint("MissingPermission")
    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }
        val minBufSize = AudioRecord.getMinBufferSize(22050, android.media.AudioFormat.CHANNEL_IN_MONO, android.media.AudioFormat.ENCODING_PCM_16BIT)
        pttAudioRecord = AudioRecord(MediaRecorder.AudioSource.MIC, 22050, android.media.AudioFormat.CHANNEL_IN_MONO, android.media.AudioFormat.ENCODING_PCM_16BIT, minBufSize * 2)
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

# To fix the stream bug, let's use another regex for the // Stream to ESP32 over BLE
regex_stream = r"// Stream to ESP32 over BLE[\s\S]*?\}\.start\(\)"

refactor_stream = '''
            // Stream to ESP32 over BLE
            if (audioBytes.size > 44) {
                val pcmBytes = ByteArray(audioBytes.size - 44)
                System.arraycopy(audioBytes, 44, pcmBytes, 0, pcmBytes.size)
                streamPcmToEsp32(pcmBytes)
            }
'''

content = re.sub(regex_stream, refactor_stream, content)

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)
