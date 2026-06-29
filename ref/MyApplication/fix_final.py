import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix pacing back to original
old_stream = '''                      val expectedElapsedMs = (bytesSent / 32.0).toLong()
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

new_stream = '''                      val expectedElapsedMs = (bytesSent / 32.0).toLong()
                      val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                      val leadTimeMs = 150L
                      val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                      if (sleepTime > 0) {
                          Thread.sleep(sleepTime)
                      } else {
                          Thread.sleep(2)
                      }'''
                      
text = text.replace(old_stream, new_stream)

# 2. Fix Downsampling
old_downsample = '''// Linear interpolation downsampling for smoother voice (removes severe chopping)
                      for (i in 0 until outLen) {
                          val exactIndex = i * ratio
                          val leftIndex = exactIndex.toInt()
                          val rightIndex = Math.min(leftIndex + 1, inShorts.size - 1)
                          val fraction = exactIndex - leftIndex
                          
                          val leftVal = inShorts[leftIndex].toDouble()
                          val rightVal = inShorts[rightIndex].toDouble()
                          
                          val interp = (leftVal + fraction * (rightVal - leftVal)) * 2.5
                          var v = interp.toInt()
                          if (v > 32767) v = 32767
                          if (v < -32768) v = -32768
                          outShorts[i] = v.toShort()
                      }'''

new_downsample = '''                      // Simple reliable nearest-neighbor standard downsampling (no clipping multipliers)
                      for (i in 0 until outLen) {
                          val inIndex = (i * ratio).toInt()
                          if (inIndex < inShorts.size) {
                              outShorts[i] = inShorts[inIndex]
                          }
                      }'''

text = text.replace(old_downsample, new_downsample)

# 3. Fix View Reparenting Button UI Issue
old_reparent = '''        btnPushToTalk.layoutParams = lpMatchWrap

        // Make button robust in scrollview
        btnPushToTalk.isFocusable = true
        btnPushToTalk.isClickable = true

        if (toDetail) {
            detailCameraContainer.addView(ivCamera)
            detailAiPanelContainer.addView(aiDebugPanel)
            detailPttContainer.addView(btnPushToTalk)
            
            // Bring them to front to catch touches
            detailPttContainer.bringToFront()
            btnPushToTalk.bringToFront()
        } else {
            debugContainer.addView(ivCamera, 3)
            debugContainer.addView(aiDebugPanel, 4)
            debugContainer.addView(btnPushToTalk, debugContainer.childCount)
        }
        
        ivCamera.requestLayout()
        btnPushToTalk.requestLayout()'''

new_reparent = '''        btnPushToTalk.layoutParams = lpMatchWrap
        
        // Remove artificial button property overrides that block standard touch events
        // (Just let the LinearLayout host the button naturally)

        if (toDetail) {
            detailCameraContainer.addView(ivCamera)
            detailAiPanelContainer.addView(aiDebugPanel)
            detailPttContainer.addView(btnPushToTalk)
        } else {
            debugContainer.addView(ivCamera, 0)
            debugContainer.addView(aiDebugPanel, 1)
            debugContainer.addView(btnPushToTalk, debugContainer.childCount)
        }'''

text = text.replace(old_reparent, new_reparent)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed pacing, clipping, and UI touch consumption!")
