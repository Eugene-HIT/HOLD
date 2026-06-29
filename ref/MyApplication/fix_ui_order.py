import sys

with open(r'd:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', 'r', encoding='utf-8') as f:
    text = f.read()

# Make pool visible and debug gone by default, to solve the overlapping non-clickable issue immediately
text = text.replace('''    <ScrollView
        android:id="@+id/debug_scroll"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:fillViewport="true"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"
        android:visibility="visible">''', '''    <ScrollView
        android:id="@+id/debug_scroll"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:fillViewport="true"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"
        android:visibility="gone">''')

text = text.replace('''    <LinearLayout
        android:id="@+id/pool_view"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:orientation="vertical"
        android:background="#F6F1EB"
        android:padding="16dp"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"
        android:visibility="gone">''', '''    <LinearLayout
        android:id="@+id/pool_view"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:orientation="vertical"
        android:background="#F6F1EB"
        android:padding="16dp"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"
        android:visibility="visible">''')

with open(r'd:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', 'w', encoding='utf-8') as f:
    f.write(text)

