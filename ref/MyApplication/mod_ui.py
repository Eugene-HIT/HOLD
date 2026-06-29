with open(r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', 'r', encoding='utf-8') as f:
    text = f.read()

injection = '''
        <EditText
            android:id="@+id/et_status_input"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="输入想发送给小程序的状态..."
            android:textSize="18sp"
            android:layout_marginTop="20dp" />

        <Button
            android:id="@+id/btn_send_to_cloud"
            android:layout_width="match_parent"
            android:layout_height="60dp"
            android:text="🚀 发送到微信云端"
            android:textSize="20sp"
            android:layout_marginBottom="20dp"/>
'''

if 'et_status_input' not in text:
    text = text.replace('    </LinearLayout>\n\n        </LinearLayout>\n    </ScrollView>', injection + '\n    </LinearLayout>\n\n        </LinearLayout>\n    </ScrollView>')
    with open(r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', 'w', encoding='utf-8') as f:
        f.write(text)
    print('UI modified successfully!')
else:
    print('UI already modified')
