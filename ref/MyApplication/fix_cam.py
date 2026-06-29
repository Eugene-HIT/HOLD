# -*- coding: utf-8 -*-
import sys

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Restore Camera Logic
camera_find = '} else if (uuid == CAM_IMAGE_CHAR_UUID) {'
camera_end = '} else if (uuid == MIC_AUDIO_CHAR_UUID) {'

cam_start = text.find(camera_find)
cam_end = text.find(camera_end, cam_start)

if cam_start != -1 and cam_end != -1:
    new_cam_block = '''} else if (uuid == CAM_IMAGE_CHAR_UUID) {
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
                    runOnUiThread { tvStatus.text = "图像接收中: " + bufferData.size + " B" }
                }

                if (bufferData.size >= 2 && (bufferData[bufferData.size - 2].toInt() and 0xFF) == 0xFF && (bufferData[bufferData.size - 1].toInt() and 0xFF) == 0xD9) {
                    runOnUiThread {
                        val bitmap = android.graphics.BitmapFactory.decodeByteArray(bufferData, 0, bufferData.size)
                        if (bitmap != null) {
                            ivCamera.setImageBitmap(bitmap)
                        }
                    }
                    imageBuffer.reset()
                }
            '''
    text = text[:cam_start] + new_cam_block + text[cam_end:]


with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Camera logic restored")
