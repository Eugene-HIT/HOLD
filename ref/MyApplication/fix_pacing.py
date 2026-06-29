import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix TTS downsampling to boost volume and improve pacing
tts_old = '''                          val interp = leftVal + fraction * (rightVal - leftVal)
                          outShorts[i] = interp.toInt().toShort()'''

tts_new = '''                          val interp = (leftVal + fraction * (rightVal - leftVal)) * 2.5
                          var v = interp.toInt()
                          if (v > 32767) v = 32767
                          if (v < -32768) v = -32768
                          outShorts[i] = v.toShort()'''

text = text.replace(tts_old, tts_new)

# Fix streamPcmToEsp32 pacing loop
stream_old = '''                      val expectedElapsedMs = (bytesSent / 32.0).toLong()
                      val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                      val leadTimeMs = 150L
                      val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                      if (sleepTime > 0) {
                          Thread.sleep(sleepTime)
                      } else {
                          Thread.sleep(2)
                      }'''

stream_new = '''                      val expectedElapsedMs = (bytesSent / 32.0).toLong()
                      val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                      val leadTimeMs = 150L
                      
                      val diff = expectedElapsedMs - actualElapsedMs
                      if (diff > leadTimeMs) {
                          // we are too far ahead, sleep to let hardware catch up
                          val sleepMs = diff - leadTimeMs + 5
                          Thread.sleep(sleepMs)
                      } else {
                          // we are behind or just fine, blast the next packet!
                          // Just yield occasionally to avoid killing the OS ble stack
                          if ((bytesSent / chunkSize) % 5 == 0) Thread.yield()
                      }'''

text = text.replace(stream_old, stream_new)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
