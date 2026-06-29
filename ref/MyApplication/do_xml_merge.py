import sys
import re

path_adhd = r'D:\ADHD\adhd\app\src\main\res\layout\activity_main.xml'
path_app = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'

with open(path_adhd, 'r', encoding='utf-8') as f:
    adhd_xml = f.read()

with open(path_app, 'r', encoding='utf-8') as f:
    app_xml = f.read()

app_inner_match = re.search(r'<TextView\s+android:id="@+id/tvStatus".*?(?=<ImageView)', app_xml, re.DOTALL)
if app_inner_match:
    app_inner = app_inner_match.group(0)
    
    # We also need the rest of the buttons
    rest_match = re.search(r'<ImageView.*?android:id="@+id/ivCamera".*?</LinearLayout>', app_xml, re.DOTALL)
    if rest_match:
        app_inner += rest_match.group(0)

    debug_section = f'''
        <!-- MYAPP DEBUG SECTION (BLE) -->
        <LinearLayout
            android:id="@+id/section_debug"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:background="#FFFFEE"
            android:visibility="visible">
            
            {app_inner}
            '''
            
    adhd_xml = re.sub(r'(</FrameLayout>)', r'\n' + debug_section + r'\1', adhd_xml, count=1)
    
    with open(path_app, 'w', encoding='utf-8') as f:
        f.write(adhd_xml)
    print("XML merged successfully!")
else:
    print("Failed to find MyApp inner views.")
