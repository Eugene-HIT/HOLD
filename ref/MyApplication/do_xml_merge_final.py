import re

path_adhd = r'D:\ADHD\adhd\app\src\main\res\layout\activity_main.xml'
path_app = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'

adhd_xml = open(path_adhd, encoding='utf-8').read()
app_xml = open(path_app, encoding='utf-8').read()

start_idx = app_xml.find('<TextView\n            android:id="@+id/tvStatus"')
if start_idx == -1:
    start_idx = app_xml.find('<TextView') # Fallback

if start_idx != -1:
    end_idx = app_xml.rfind('</LinearLayout>')
    if end_idx != -1:
        inner = app_xml[start_idx:end_idx]
        sec = f'''
        <!-- MYAPP DEBUG SECTION (BLE) -->
        <ScrollView
            android:id="@+id/section_debug"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:background="#FFFFEE"
            android:visibility="gone">
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="vertical">
                {inner}
            </LinearLayout>
        </ScrollView>
        '''
        adhd_xml = adhd_xml.replace('</FrameLayout>', sec + '\n</FrameLayout>')
        # Add a button in the top bar to toggle debug section
        btn = '<Button android:id="@+id/btn_toggle_debug" android:layout_width="wrap_content" android:layout_height="wrap_content" android:text="Debug"/>'
        adhd_xml = adhd_xml.replace('<View\n                android:layout_width="0dp"\n                android:layout_height="0dp"\n                android:layout_weight="1" />', btn)
        
        open(path_app, 'w', encoding='utf-8').write(adhd_xml)
        print("Merged XML successfully!")
