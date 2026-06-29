import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the inner LinearLayout header with RelativeLayout
start_str = '''        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:padding="16dp"
            android:gravity="center_vertical"
            android:background="#FFFFFF"
            android:elevation="4dp">'''

res = re.search(r'        <LinearLayout\s+android:layout_width="match_parent"\s+android:layout_height="wrap_content"\s+android:orientation="horizontal"\s+android:padding="16dp"\s+android:gravity="center_vertical"\s+android:background="#FFFFFF"\s+android:elevation="4dp">\s*<Button.*?minWidth="64dp" />\s*</LinearLayout>', text, re.DOTALL)
if res:
    better_header = '''        <RelativeLayout
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
    
    text = text.replace(res.group(0), better_header)
else:
    print("WARNING: Could not find header block")

text = text.replace('@android:drawable/dialog_holo_light_frame', '#FFFFFF')
with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(text)

