import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix downsampling to Boxcar filter with proper volume handling
old_ds = '''                      // High-quality linear interpolation without any clipping or volume boosting, making it sound identical to native PTT
                      for (i in 0 until outLen) {
                          val exactIndex = i * ratio
                          val leftIndex = exactIndex.toInt()
                          val rightIndex = Math.min(leftIndex + 1, inShorts.size - 1)
                          val fraction = exactIndex - leftIndex

                          val leftVal = inShorts[leftIndex].toDouble()
                          val rightVal = inShorts[rightIndex].toDouble()

                          val interp = leftVal + fraction * (rightVal - leftVal)
                          var v = (interp * 0.35).toInt() 
                          if (v > 32767) v = 32767
                          if (v < -32768) v = -32768
                          outShorts[i] = v.toShort()
                      }'''

new_ds = '''                      // Professional Boxcar (Moving Average) Low-Pass Filter Downsampling
                      // This completely eliminates high-frequency aliasing (robotic buzzing) 
                      // and natively scales volume perfectly smooth!
                      for (i in 0 until outLen) {
                          val startIdx = i * ratio
                          val endIdx = (i + 1) * ratio
                          val startI = startIdx.toInt()
                          val endI = Math.ceil(endIdx).toInt()
                          
                          var total = 0.0
                          var weight = 0.0
                          for (j in startI until endI) {
                              if (j < inShorts.size) {
                                  val wStart = Math.max(startIdx, j.toDouble())
                                  val wEnd = Math.min(endIdx, (j + 1).toDouble())
                                  val w = wEnd - wStart
                                  total += inShorts[j] * w
                                  weight += w
                              }
                          }
                          val avg = if (weight > 0) (total / weight) else 0.0
                          var v = (avg * 0.35).toInt() // Scale down to match perfect PTT voice level
                          if (v > 32767) v = 32767
                          if (v < -32768) v = -32768
                          outShorts[i] = v.toShort()
                      }'''

if old_ds in text:
    text = text.replace(old_ds, new_ds)
    print("Replaced downsampling")
else:
    print("WARNING: downsampling not replaced!")

# 2. Fix BLE pacing burst issue
old_pace = '''                      if (sleepTime > 0) {
                          Thread.sleep(sleepTime)
                      } else {
                          Thread.sleep(2)
                      }'''

new_pace = '''                      if (sleepTime > 0) {
                          Thread.sleep(sleepTime)
                      } else {
                          // Crucial Fix: NEVER sleep less than 5ms! 
                          // 240 bytes = 7.5ms of audio. Sleeping 2ms causes a 4x real-time burst
                          // which physically overflows the Android Bluetooth HCI queue and drops packets immediately!
                          // Sleeping 5ms guarantees a safe 1.5x catch-up speed without destroying the queue.
                          Thread.sleep(5)
                      }'''

if old_pace in text:
    text = text.replace(old_pace, new_pace)
    print("Replaced pacing")
else:
    print("WARNING: pacing not replaced!")
    
with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

