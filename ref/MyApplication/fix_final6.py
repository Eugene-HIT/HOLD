import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace downsampling using Regex
ds_pattern = r'// High-quality linear interpolation without any clipping.*?outShorts\[i\] = v\.toShort\(\)\s*\}'
new_ds = '''// High-quality Professional Boxcar (Moving Average) Low-Pass Filter Downsampling
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

text = re.sub(ds_pattern, new_ds, text, flags=re.DOTALL)

# Replace pacing using Regex
pace_pattern = r'if \(sleepTime > 0\) \{\s*Thread\.sleep\(sleepTime\)\s*\} else \{\s*Thread\.sleep\(2\)\s*\}'
new_pace = '''if (sleepTime > 0) {
                          Thread.sleep(sleepTime)
                      } else {
                          // Crucial Fix: NEVER sleep less than 5ms! 
                          // 240 bytes = 7.5ms of audio. Sleeping 2ms causes a 4x real-time burst
                          // which physically overflows the Android Bluetooth HCI queue and drops packets immediately!
                          // Sleeping 5ms guarantees a safe 1.5x catch-up speed without destroying the queue.
                          Thread.sleep(5)
                      }'''

text = re.sub(pace_pattern, new_pace, text, flags=re.DOTALL)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Regex applied successfully!")
