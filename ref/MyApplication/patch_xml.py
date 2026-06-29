import re

xml_path = 'app/src/main/res/layout/activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'(android:id="@+id/tv_detail_task"[\s\S]*?android:layout_marginTop="4dp" />\s*</LinearLayout>)'
replacement = '''\g<1>

                        <!-- NEWLY ADDED UI FOR DETAIL -->
                        <LinearLayout
                            android:layout_width="match_parent"
                            android:layout_height="wrap_content"
                            android:orientation="vertical"
                            android:background="#FFFFFF"
                            android:padding="16dp"
                            android:layout_marginTop="16dp"
                            android:layout_marginBottom="16dp"
                            android:elevation="2dp">
                            <TextView
                                android:layout_width="wrap_content"
                                android:layout_height="wrap_content"
                                android:text="STT 实录"
                                android:textSize="14sp"
                                android:textColor="#666666" />
                            <TextView
                                android:id="@+id/tv_detail_stt"
                                android:layout_width="match_parent"
                                android:layout_height="wrap_content"
                                android:text="等待语音输入..."
                                android:textSize="16sp"
                                android:textColor="#EA580C"
                                android:layout_marginTop="8dp" />
                        </LinearLayout>
                        
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
                                android:text="任务拆解"
                                android:textSize="14sp"
                                android:textColor="#666666"
                                android:layout_marginBottom="8dp" />
                            <LinearLayout
                                android:id="@+id/task_list_container"
                                android:layout_width="match_parent"
                                android:layout_height="wrap_content"
                                android:orientation="vertical" />
                        </LinearLayout>

                        <!-- Congratulations block -->
                        <LinearLayout
                            android:id="@+id/congrats_container"
                            android:layout_width="match_parent"
                            android:layout_height="wrap_content"
                            android:orientation="vertical"
                            android:background="#D1FAE5"
                            android:padding="20dp"
                            android:visibility="gone"
                            android:layout_marginBottom="16dp"
                            android:elevation="4dp"
                            android:gravity="center">
                            <TextView
                                android:layout_width="wrap_content"
                                android:layout_height="wrap_content"
                                android:text=" 恭喜完成全部拆解任务！"
                                android:textSize="18sp"
                                android:textStyle="bold"
                                android:textColor="#065F46" />
                            <Button
                                android:id="@+id/btn_detail_disconnect"
                                android:layout_width="wrap_content"
                                android:layout_height="wrap_content"
                                android:text="完成并返回求助池"
                                android:layout_marginTop="12dp"
                                android:backgroundTint="#059669"
                                android:textColor="#FFFFFF" />
                        </LinearLayout>
'''

if 'id="@+id/tv_detail_stt"' not in text:
    new_text = re.sub(pattern, replacement, text)
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("XML Patched!")
else:
    print("Already in XML")
