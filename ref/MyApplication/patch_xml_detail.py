import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    xml_content = f.read()

# Try to find and extract the AI Debug Status Panel, ivCamera, and btnPushToTalk
ai_panel_regex = r'(<!-- AI Debug Status Panel -->\s*<LinearLayout[\s\S]*?</LinearLayout>)'
iv_camera_regex = r'(<ImageView\s+android:id="@+id/ivCamera"[\s\S]*?/>)'
btn_ptt_regex = r'(<Button\s+android:id="@+id/btnPushToTalk"[\s\S]*?/>)'

ai_panel_match = re.search(ai_panel_regex, xml_content)
iv_camera_match = re.search(iv_camera_regex, xml_content)
btn_ptt_match = re.search(btn_ptt_regex, xml_content)

ai_panel = ai_panel_match.group(1) if ai_panel_match else ""
iv_camera = iv_camera_match.group(1) if iv_camera_match else ""
btn_ptt = btn_ptt_match.group(1) if btn_ptt_match else ""

# Remove them from their original location
if ai_panel: xml_content = xml_content.replace(ai_panel, '')
if iv_camera: xml_content = xml_content.replace(iv_camera, '')
if btn_ptt: xml_content = xml_content.replace(btn_ptt, '')

# Construct the new Detail View
new_detail_view = f'''
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
        app:layout_constraintBottom_toBottomOf="parent">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:padding="16dp"
            android:gravity="center_vertical"
            android:background="#FFFFFF"
            android:elevation="4dp">

            <Button
                android:id="@+id/btn_back_to_pool"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text=" 返回"
                android:backgroundTint="#E5E7EB"
                android:textColor="#374151"
                android:textSize="14sp"
                style="?android:attr/buttonBarButtonStyle" />

            <TextView
                android:id="@+id/tv_detail_title"
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="wrap_content"
                android:gravity="center"
                android:text="求助详情"
                android:textSize="18sp"
                android:textStyle="bold"
                android:textColor="#9A6B45" />
                
            <View
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:minWidth="64dp" />
        </LinearLayout>

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
                    android:background="@android:drawable/dialog_holo_light_frame"
                    android:padding="16dp"
                    android:layout_marginBottom="16dp">
                    
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

                {iv_camera}
                
                {ai_panel}

            </LinearLayout>
        </ScrollView>

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:background="#FFFFFF"
            android:padding="16dp"
            android:elevation="12dp">
            {btn_ptt}
        </LinearLayout>
    </LinearLayout>
'''

# Insert the new view right before the closing tag of ConstraintLayout
xml_content = xml_content.replace('</androidx.constraintlayout.widget.ConstraintLayout>', new_detail_view + '\n</androidx.constraintlayout.widget.ConstraintLayout>')

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(xml_content)
print("XML Updated.")
