with open('app/src/main/res/layout/activity_main.xml', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('android:layout_width="match_parent"\\n            android:gravity="center"', 'android:layout_width="match_parent"\n            android:gravity="center"')

with open('app/src/main/res/layout/activity_main.xml', 'w', encoding='utf-8') as f:
    f.write(text)
print("XML Fix applied!")
