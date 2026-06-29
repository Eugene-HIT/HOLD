import re
import os

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_block = r'''            \} else if \(uuid == CAM_IMAGE_CHAR_UUID\) \{
                  if \(data\.size >= 2 && \(data\[0\]\.toInt\(\) and 0xFF\) == 0xFF && \(data\[1\]\.toInt\(\) and 0xFF\) == 0xD8\) \{
.*?\} else if \(uuid == MIC_AUDIO_CHAR_UUID\) \{'''

new_block = '''            } else if (uuid == CAM_IMAGE_CHAR_UUID) {
                  if (data.contentEquals(lastCamData)) {
                       return
                  }
                  lastCamData = data.clone()

                  if (data.size >= 2 && (data[0].toInt() and 0xFF) == 0xFF && (data[1].toInt() and 0xFF) == 0xD8) {
                      imageBuffer.reset()
                      runOnUiThread { tvStatus.text = " 正在接入镜头..." }
                  }

                  if (imageBuffer.size() > 0 || (data.size >= 2 && (data[0].toInt() and 0xFF) == 0xFF && (data[1].toInt() and 0xFF) == 0xD8)) {
                      imageBuffer.write(data)
                  } else {
                      return
                  }

                  val bufferData = imageBuffer.toByteArray()

                  if (bufferData.size % 1000 < 250) {
                      runOnUiThread { tvStatus.text = "图像接收中 " + bufferData.size + " B" }
                  }

                  if (bufferData.size > 2000) {
                      var foundEoi = false
                      var eoiIndex = -1
                      val scanStart = java.lang.Math.max(0, bufferData.size - data.size - 2)
                      for (i in scanStart until bufferData.size - 1) {        
                          if ((bufferData[i].toInt() and 0xFF) == 0xFF && (bufferData[i+1].toInt() and 0xFF) == 0xD9) {
                              foundEoi = true
                              eoiIndex = i
                              break
                          }
                      }

                      if (foundEoi) {
                          runOnUiThread {
                              try {
                                  val exactSize = eoiIndex + 2
                                  val bitmap = android.graphics.BitmapFactory.decodeByteArray(bufferData, 0, exactSize)
                                  if (bitmap != null) {
                                      ivCamera.setImageBitmap(bitmap)
                                  }
                              } catch (e: Exception) {
                                  e.printStackTrace()
                              }
                          }
                          imageBuffer.reset()
                      }
                  }
              } else if (uuid == MIC_AUDIO_CHAR_UUID) {'''

text = re.sub(old_block, new_block, text, flags=re.DOTALL)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Kotlin reverted.')