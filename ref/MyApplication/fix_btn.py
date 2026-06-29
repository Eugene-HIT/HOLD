kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_content = f.read()

kt_content = kt_content.replace('val btnPushToTalk: Button = findViewById(R.id.btnPushToTalk)', 'btnPushToTalk = findViewById(R.id.btnPushToTalk)')
if 'private lateinit var btnPushToTalk: android.widget.Button' not in kt_content:
    kt_content = kt_content.replace('private lateinit var debugContainer: android.widget.LinearLayout', 'private lateinit var btnPushToTalk: android.widget.Button\n    private lateinit var debugContainer: android.widget.LinearLayout')

kt_content = kt_content.replace('ViewGroup', 'android.view.ViewGroup')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_content)
