import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

target = '''<TextView
                  android:id="@+id/tvAiReply"
                  android:layout_width="match_parent"
                  android:layout_height="wrap_content"
                  android:text="AI: -"
                  android:textSize="14sp"
                  android:textColor="#B71C1C"
                  android:layout_marginTop="4dp"/>'''

ui_inject = '''<TextView
                  android:id="@+id/tvAiReply"
                  android:layout_width="match_parent"
                  android:layout_height="wrap_content"
                  android:text="AI: -"
                  android:textSize="14sp"
                  android:textColor="#B71C1C"
                  android:layout_marginTop="4dp"/>
                  
              <LinearLayout
                  android:layout_width="match_parent"
                  android:layout_height="wrap_content"
                  android:orientation="vertical"
                  android:background="#FFF3E0"
                  android:padding="8dp"
                  android:layout_marginTop="8dp"
                  android:elevation="2dp">
                  
                  <TextView
                      android:id="@+id/tvUserTask"
                      android:layout_width="match_parent"
                      android:layout_height="wrap_content"
                      android:text=" 目标任务：未知"
                      android:textSize="14sp"
                      android:textStyle="bold"
                      android:textColor="#EF6C00"/>
                      
                  <TextView
                      android:id="@+id/tvUserState"
                      android:layout_width="match_parent"
                      android:layout_height="wrap_content"
                      android:text=" 当前状态：未知"
                      android:textSize="14sp"
                      android:textStyle="bold"
                      android:textColor="#1565C0"
                      android:layout_marginTop="4dp"/>
                      
                  <TextView
                      android:id="@+id/tvActionSteps"
                      android:layout_width="match_parent"
                      android:layout_height="wrap_content"
                      android:text=" 拆解步骤：\n等待识别..."
                      android:textSize="14sp"
                      android:textColor="#37474F"
                      android:layout_marginTop="4dp"/>
              </LinearLayout>'''
              
text = text.replace(target, ui_inject)
with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("XML Injected precisely")
