import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    xml_content = f.read()

# Make the header absolutely unbreakable
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
                android:text=" 返回 "
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

# Replace the old LinearLayout header
xml_content = re.sub(r'<LinearLayout[^>]*>[\s\S]*?<Button\s+android:id="@+id/btn_back_to_pool"[\s\S]*?<TextView\s+android:id="@+id/tv_detail_title"[\s\S]*?<View[\s\S]*?</LinearLayout>', better_header, xml_content)

# Remove the weird android drawable that might crash
xml_content = xml_content.replace('android:background="@android:drawable/dialog_holo_light_frame"', 'android:background="#FFFFFF"')

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(xml_content)
