import re

adhd_xml = open(r'D:\ADHD\adhd\app\src\main\res\layout\activity_main.xml', encoding='utf-8').read()
app_xml = open(r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', encoding='utf-8').read()

start_idx = app_xml.find('<TextView\n            android:id="@+id/tvStatus"')
if start_idx == -1:
    start_idx = app_xml.find('<TextView') # Fallback

if start_idx != -1:
    end_idx = app_xml.rfind('</LinearLayout>')
    if end_idx != -1:
        inner = app_xml[start_idx:end_idx]
        sec = f'''
        <!-- MYAPP DEBUG SECTION (BLE) -->
        <LinearLayout
            android:id="@+id/section_debug"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:orientation="vertical"
            android:background="#FFFFEE"
             android:visibility="gone">
            {inner}
        </LinearLayout>
        '''
        adhd_xml = adhd_xml.replace('</FrameLayout>', sec + '\n</FrameLayout>')
        open(r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', 'w', encoding='utf-8').write(adhd_xml)
        print("Merged!")
