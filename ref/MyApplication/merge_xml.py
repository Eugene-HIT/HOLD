import xml.etree.ElementTree as ET
import os

adhd_xml_path = r'D:\ADHD\adhd\app\src\main\res\layout\activity_main.xml'
old_xml_path = r'D:\ADHD\MyApplication\old_debug_ui.xml'
out_xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'

with open(adhd_xml_path, 'r', encoding='utf-8') as f:
    adhd_xml = f.read()

with open(old_xml_path, 'r', encoding='utf-8') as f:
    old_xml = f.read()

# Extract inner layout of old_xml
old_lines = old_xml.split('\n')
inner_old = []
found = False
for line in old_lines:
    if '<LinearLayout' in line and not found:
        found = True
        inner_old.append(line.replace('match_parent', 'wrap_content', 1))
    elif found:
        # Stop at the closing ScrollView
        if '</ScrollView>' in line:
            break
        inner_old.append(line)

inner_str = '\n'.join(inner_old)
inner_str = f'''
    <!-- INJECTED DEBUG UI FOR COMPATIBILITY -->
    <ScrollView
        android:id="@+id/section_debug"
        android:layout_width="match_parent"
        android:layout_height="200dp"
        app:layout_constraintBottom_toBottomOf="parent"
        android:visibility="visible">
        <LinearLayout android:orientation="vertical" android:layout_width="match_parent" android:layout_height="wrap_content">
{inner_str}
        </LinearLayout>
    </ScrollView>
'''

# Find the closing tag of the root in adhd_xml
idx = adhd_xml.rfind('</androidx.constraintlayout.widget.ConstraintLayout>')
if idx != -1:
    merged_xml = adhd_xml[:idx] + inner_str + adhd_xml[idx:]
    with open(out_xml_path, 'w', encoding='utf-8') as f:
        f.write(merged_xml)
    print('Merged successfully')
else:
    print('Closing tag not found')
