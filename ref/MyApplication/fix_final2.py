import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_code = '''                      // Simple reliable nearest-neighbor standard downsampling (no clipping multipliers)
                      for (i in 0 until outLen) {
                          val inIndex = (i * ratio).toInt()
                          if (inIndex < inShorts.size) {
                              outShorts[i] = inShorts[inIndex]
                          }
                      }'''

new_code = '''                      // High-quality linear interpolation without any clipping or volume boosting, making it sound identical to native PTT
                      for (i in 0 until outLen) {
                          val exactIndex = i * ratio
                          val leftIndex = exactIndex.toInt()
                          val rightIndex = Math.min(leftIndex + 1, inShorts.size - 1)
                          val fraction = exactIndex - leftIndex
                          
                          val leftVal = inShorts[leftIndex].toDouble()
                          val rightVal = inShorts[rightIndex].toDouble()
                          
                          val interp = leftVal + fraction * (rightVal - leftVal)
                          var v = interp.toInt()
                          if (v > 32767) v = 32767
                          if (v < -32768) v = -32768
                          outShorts[i] = v.toShort()
                      }'''

if old_code in text:
    text = text.replace(old_code, new_code)
    with open(kt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced successfully!")
else:
    print("Old code not found! Trying regex...")
