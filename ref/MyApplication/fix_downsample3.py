import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

idx_start = text.find('// Stream to ESP32 over BLE')
idx_end = text.find('} catch (e: Exception) {', idx_start)

if idx_start != -1 and idx_end != -1:
    old_block = text[idx_start:idx_end]
    new_processing = '''// Stream to ESP32 over BLE
              if (audioBytes.size > 44) {
                  // Parse WAV Header for Sample Rate (bytes 24-27) safely
                  val inRate = (audioBytes[24].toInt() and 0xFF) or
                          ((audioBytes[25].toInt() and 0xFF) shl 8) or
                          ((audioBytes[26].toInt() and 0xFF) shl 16) or
                          ((audioBytes[27].toInt() and 0xFF) shl 24)

                  // Safely find the "data" chunk because WAV headers can vary and skipping blindly causes horrible noise
                  var dataOffset = 44
                  for (i in 12 until Math.min(audioBytes.size - 4, 300)) {
                      if (audioBytes[i] == 'd'.code.toByte() && audioBytes[i+1] == 'a'.code.toByte() && audioBytes[i+2] == 't'.code.toByte() && audioBytes[i+3] == 'a'.code.toByte()) {
                          dataOffset = i + 8
                          break
                      }
                  }

                  val pcmBytes = ByteArray(audioBytes.size - dataOffset)
                  System.arraycopy(audioBytes, dataOffset, pcmBytes, 0, pcmBytes.size)

                  val targetRate = 16000
                  val finalPcm = if (inRate != targetRate && inRate > 0) {
                      android.util.Log.i("AI_DEBUG", "Advanced Downsampling TTS from \ to \")
                      val inShorts = ShortArray(pcmBytes.size / 2)
                      java.nio.ByteBuffer.wrap(pcmBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(inShorts)

                      val ratio = inRate.toDouble() / targetRate.toDouble()
                      val outLen = (inShorts.size / ratio).toInt()
                      val outShorts = ShortArray(outLen)
                      // Linear interpolation downsampling for smoother voice (removes severe chopping)
                      for (i in 0 until outLen) {
                          val exactIndex = i * ratio
                          val leftIndex = exactIndex.toInt()
                          val rightIndex = Math.min(leftIndex + 1, inShorts.size - 1)
                          val fraction = exactIndex - leftIndex
                          
                          val leftVal = inShorts[leftIndex].toDouble()
                          val rightVal = inShorts[rightIndex].toDouble()
                          
                          val interp = leftVal + fraction * (rightVal - leftVal)
                          outShorts[i] = interp.toInt().toShort()
                      }
                      
                      val outBytes = ByteArray(outShorts.size * 2)
                      java.nio.ByteBuffer.wrap(outBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(outShorts)
                      outBytes
                  } else {
                      pcmBytes
                  }

                  streamPcmToEsp32(finalPcm)
              }

          '''
    text = text[:idx_start] + new_processing + text[idx_end:]
    with open(kt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced by index!")
else:
    print("Could not find index.")
