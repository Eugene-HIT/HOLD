import sys

old_path = r'D:\ADHD\MainActivity_fluent_audio_backup.kt'
new_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'

with open(old_path, 'r', encoding='utf-8') as f:
    old_text = f.read()

with open(new_path, 'r', encoding='utf-8') as f:
    new_text = f.read()

# Restore Camera Logic from Fluent Backup
camera_find = '} else if (uuid == CAM_IMAGE_CHAR_UUID) {'
camera_end = '} else if (uuid == MIC_AUDIO_CHAR_UUID) {'

old_cam_start = old_text.find(camera_find)
old_cam_end = old_text.find(camera_end, old_cam_start)
old_cam_block = old_text[old_cam_start:old_cam_end]

new_cam_start = new_text.find(camera_find)
new_cam_end = new_text.find(camera_end, new_cam_start)

if new_cam_start != -1 and new_cam_end != -1 and old_cam_start != -1:
    new_text = new_text[:new_cam_start] + old_cam_block + new_text[new_cam_end:]

with open(new_path, 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Camera logic completely restored from fluent backup")
