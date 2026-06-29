import re
with open(r'd:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix debug_scroll visibility
text = re.sub(r'(<ScrollView[^>]*android:id="@+id/debug_scroll"[^>]*android:visibility=")gone(")', r'\g<1>visible\2', text)
# Fix pool_view visibility
text = re.sub(r'(<LinearLayout[^>]*android:id="@+id/pool_view"[^>]*android:visibility=")visible(")', r'\g<1>gone\2', text)

with open(r'd:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', 'w', encoding='utf-8') as f:
    f.write(text)
print("Visibilities fixed.")
