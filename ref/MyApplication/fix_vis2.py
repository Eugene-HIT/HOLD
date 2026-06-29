import sys

xml_path = r'd:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Instead of complex regex, let's just do targeted string replaces
# It's an exact replace.
text = text.replace('android:id="@+id/debug_scroll"\n        android:layout_width="0dp"\n        android:layout_height="0dp"\n        android:fillViewport="true"\n        app:layout_constraintTop_toTopOf="parent"\n        app:layout_constraintStart_toStartOf="parent"\n        app:layout_constraintEnd_toEndOf="parent"\n        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"\n        android:visibility="gone"', 
                    'android:id="@+id/debug_scroll"\n        android:layout_width="0dp"\n        android:layout_height="0dp"\n        android:fillViewport="true"\n        app:layout_constraintTop_toTopOf="parent"\n        app:layout_constraintStart_toStartOf="parent"\n        app:layout_constraintEnd_toEndOf="parent"\n        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"\n        android:visibility="visible"')

text = text.replace('android:id="@+id/pool_view"\n        android:layout_width="0dp"\n        android:layout_height="0dp"\n        android:orientation="vertical"\n        android:background="#F6F1EB"\n        android:padding="16dp"\n        app:layout_constraintTop_toTopOf="parent"\n        app:layout_constraintStart_toStartOf="parent"\n        app:layout_constraintEnd_toEndOf="parent"\n        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"\n        android:visibility="visible"',
                    'android:id="@+id/pool_view"\n        android:layout_width="0dp"\n        android:layout_height="0dp"\n        android:orientation="vertical"\n        android:background="#F6F1EB"\n        android:padding="16dp"\n        app:layout_constraintTop_toTopOf="parent"\n        app:layout_constraintStart_toStartOf="parent"\n        app:layout_constraintEnd_toEndOf="parent"\n        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"\n        android:visibility="gone"')


with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("done string replace")
