import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('android:id="@+id/btn_back_to_pool"')
if idx != -1:
    end_idx = text.find('</LinearLayout>', idx)
    start_idx = text.rfind('<LinearLayout', 0, idx)
    
    better_header = '''<RelativeLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:padding="16dp"
            android:background="#FFFFFF"
            android:elevation="4dp">

            <Button
                android:id="@+id/btn_back_to_pool"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="返回"
                android:layout_alignParentStart="true"
                android:layout_centerVertical="true"
                android:backgroundTint="#E5E7EB"
                android:textColor="#374151"
                android:textSize="14sp" />

            <TextView
                android:id="@+id/tv_detail_title"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_centerInParent="true"
                android:text="求助详情"
                android:textSize="20sp"
                android:textStyle="bold"
                android:textColor="#000000" />
        </RelativeLayout>'''
        
    text = text[:start_idx] + better_header + text[end_idx+15:]
    
text = text.replace('@android:drawable/dialog_holo_light_frame', '#FFFFFF')

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done!")
