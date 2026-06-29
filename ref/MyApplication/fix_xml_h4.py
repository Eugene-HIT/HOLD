import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

# I will just replace the entire help_detail_view.
# First find <LinearLayout android:id="@+id/help_detail_view"
idx = text.find('android:id="@+id/help_detail_view"')
start_idx = text.rfind('<LinearLayout', 0, idx)
end_idx = text.find('<!-- bottom_nav_container -->') # wait, what's next?
if end_idx == -1:
    end_idx = text.find('<LinearLayout\n        android:id="@+id/bottom_nav_container"')

if start_idx != -1 and end_idx != -1:
    better_detail = '''    <!-- Detail View -->
    <LinearLayout
        android:id="@+id/help_detail_view"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:orientation="vertical"
        android:background="#F6F1EB"
        android:visibility="gone"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintBottom_toBottomOf="parent"
        android:elevation="10dp"
        android:clickable="true"
        android:focusable="true">

        <RelativeLayout
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
                android:textColor="#9A6B45" />
        </RelativeLayout>

        <ScrollView
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="1"
            android:fillViewport="true">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="vertical"
                android:padding="16dp">

                <LinearLayout
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:orientation="vertical"
                    android:background="#FFFFFF"
                    android:padding="16dp"
                    android:layout_marginBottom="16dp"
                    android:elevation="2dp">
                    
                    <TextView
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="大任务"
                        android:textSize="14sp"
                        android:textColor="#666666" />
                        
                    <TextView
                        android:id="@+id/tv_detail_task"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:text="写论文"
                        android:textSize="22sp"
                        android:textStyle="bold"
                        android:textColor="#333333"
                        android:layout_marginTop="4dp" />
                </LinearLayout>

                <LinearLayout
                    android:id="@+id/detail_camera_container"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:orientation="vertical" />
                    
                <LinearLayout
                    android:id="@+id/detail_ai_panel_container"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:orientation="vertical" />

            </LinearLayout>
        </ScrollView>

        <LinearLayout
            android:id="@+id/detail_ptt_container"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:background="#FFFFFF"
            android:padding="16dp"
            android:elevation="12dp"
            android:orientation="vertical">
        </LinearLayout>
    </LinearLayout>

'''
    # We replace from start_idx to end_idx
    text = text[:start_idx] + better_detail + text[end_idx:]

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Replaced Full Detail View Safely.")
