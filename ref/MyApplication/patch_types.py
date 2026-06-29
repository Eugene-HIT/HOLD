import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("private lateinit var detailCameraContainer: android.widget.FrameLayout", "private lateinit var detailCameraContainer: android.widget.LinearLayout")
text = text.replace("private lateinit var detailAiPanelContainer: android.widget.FrameLayout", "private lateinit var detailAiPanelContainer: android.widget.LinearLayout")
text = text.replace("private lateinit var detailPttContainer: android.widget.FrameLayout", "private lateinit var detailPttContainer: android.widget.LinearLayout")

# Wait, let's fix any other class cast potential.
# tabPool - is it TextView or LinearLayout?
# In activity_main.xml, R.id.tab_pool is a TextView. It was instantiated as TextView in `fix_pool_vars.py`. Let's verify `tab_pool` in xml.

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("done!")
