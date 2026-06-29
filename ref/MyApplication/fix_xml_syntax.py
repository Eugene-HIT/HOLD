import re

xml_path = 'app/src/main/res/layout/activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the malformed tag:
bad_part = """<LinearLayout

                        <!-- NEWLY ADDED UI FOR DETAIL -->"""
good_part = """<!-- NEWLY ADDED UI FOR DETAIL -->"""

if bad_part in text:
    text = text.replace(bad_part, good_part)
    
bad_part2 = """<LinearLayout
                            android:id="@+id/detail_camera_container"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:orientation="vertical" />"""
good_part2 = """<LinearLayout
                        android:id="@+id/detail_camera_container"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:orientation="vertical" />"""
text = text.replace(bad_part2, good_part2)

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Fix XML Syntax!")
