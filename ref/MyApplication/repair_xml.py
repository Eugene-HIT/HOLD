import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    xml_content = f.read()

# Extract inner of ScrollView
match = re.search(r'<LinearLayout.*?</LinearLayout>', xml_content, re.DOTALL)
if match:
    # Need to get all until the very last </ScrollView> 
    inner_match = re.search(r'(<LinearLayout.*)</ScrollView>', xml_content, re.DOTALL)
    inner_linear = inner_match.group(1) if inner_match else '<LinearLayout></LinearLayout>'
else:
    inner_linear = '<LinearLayout></LinearLayout>'

# Give IDs to the elements we want to reparent in Kotlin if they don't have them
# 1. AI Panel
inner_linear = inner_linear.replace('<!-- AI Debug Status Panel -->\n        <LinearLayout', '<!-- AI Debug Status Panel -->\n        <LinearLayout\n            android:id="@+id/ai_debug_panel"')


new_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:id="@+id/main"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#F6F1EB">

    <!-- Debug View (Original) -->
    <ScrollView
        android:id="@+id/debug_scroll"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:fillViewport="true"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottom_nav_container"
        android:visibility="gone">
        
        <LinearLayout android:id="@+id/debug_container" android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical">
            {{inner_linear}}
        </LinearLayout>
    </ScrollView>

    <!-- Pool View -->
    <LinearLayout
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
        android:visibility="visible">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="求助池"
            android:textSize="20sp"
            android:textStyle="bold"
            android:textColor="#9A6B45"
            android:layout_marginBottom="16dp"/>

        <ScrollView
            android:layout_width="match_parent"
            android:layout_height="match_parent">
            <LinearLayout
                android:id="@+id/poolListLayout"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="vertical" />
        </ScrollView>
    </LinearLayout>
    
    <!-- Detail View -->
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
        android:elevation="10dp">

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
                android:textSize="14sp" />

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

                <!-- This container will dynamically host the camera in detail view -->
                <LinearLayout
                    android:id="@+id/detail_camera_container"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:orientation="vertical" />
                    
                <!-- This container will dynamically host the AI panel in detail view -->
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
            android:elevation="12dp">
            <!-- PTT button will be moved here -->
        </LinearLayout>
    </LinearLayout>

    <LinearLayout
        android:id="@+id/bottom_nav_container"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent">

        <LinearLayout
            android:id="@+id/bottom_nav"
            android:layout_width="match_parent"
            android:layout_height="64dp"
            android:background="#FFFFFF"
            android:elevation="8dp"
            android:gravity="center_vertical"
            android:orientation="horizontal"
            android:paddingStart="8dp"
            android:paddingEnd="8dp">

            <Button
                android:id="@+id/tab_pool"
                android:layout_width="0dp"
                android:layout_height="48dp"
                android:layout_weight="1"
                android:backgroundTint="#E7EDF8"
                android:text="求助池"
                android:textColor="#3B82F6"
                android:textSize="16sp" />

            <Button
                android:id="@+id/tab_debug"
                android:layout_width="0dp"
                android:layout_height="48dp"
                android:layout_weight="1"
                android:layout_marginStart="8dp"
                android:backgroundTint="#F3F4F6"
                android:text="调试"
                android:textColor="#9CA3AF"
                android:textSize="16sp" />
        </LinearLayout>
        
        <View
            android:layout_width="match_parent"
            android:layout_height="32dp"
            android:background="#FFFFFF"/>
    </LinearLayout>

</androidx.constraintlayout.widget.ConstraintLayout>
'''.replace('{inner_linear}', inner_linear)

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(new_xml)
print("XML Repaired!")
