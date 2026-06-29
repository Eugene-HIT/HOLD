# -*- coding: utf-8 -*-
import re

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: timers
target1 = '''      private fun updatePoolTimers() {
          val now = System.currentTimeMillis()
          for (pair in timerViews) {
              val tv = pair.first
              val item = pair.second
              val diffSeconds = (now - item.timestamp) / 1000
              tv.text = "等待 s"
          }
      }'''
      
new1 = '''      private fun updatePoolTimers() {
          val now = System.currentTimeMillis()
          for (pair in timerViews) {
              val tv = pair.first
              val item = pair.second
              val diffSeconds = (now - item.timestamp) / 1000
              tv.text = "已等待 ${diffSeconds}s"
          }
      }'''
      
text = text.replace(target1, new1)


# Fix 2: reparentViews hiding debug
target2 = '''          if (toDetail) {
              detailAiPanelContainer.addView(aiDebugPanel)
              detailCameraContainer.addView(ivCamera)
              detailPttContainer.addView(pttBtn)
          } else {'''

new2 = '''          if (toDetail) {
              detailCameraContainer.addView(ivCamera)
              detailPttContainer.addView(pttBtn)
          } else {'''

text = text.replace(target2, new2)

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

with open('app/src/main/res/layout/activity_main.xml', 'r', encoding='utf-8') as f:
    xml_text = f.read()

# Fix 3: Center 求助池. Find it exactly. First, locate the pool_view section.
pool_start = xml_text.find('android:id="@+id/pool_view"')
if pool_start != -1:
    tv_start = xml_text.find('<TextView', pool_start)
    tv_end = xml_text.find('/>', tv_start) + 2
    tv_chunk = xml_text[tv_start:tv_end]
    if 'wrap_content' in tv_chunk and ('求助池' in tv_chunk or '姹傚姪姹' in tv_chunk):
        new_tv_chunk = tv_chunk.replace('android:layout_width="wrap_content"', 'android:layout_width="match_parent"\\n            android:gravity="center"')
        xml_text = xml_text[:tv_start] + new_tv_chunk + xml_text[tv_end:]
        with open('app/src/main/res/layout/activity_main.xml', 'w', encoding='utf-8') as f:
            f.write(xml_text)
        print("XML updated!")

print("Fixes applied successfully!")
