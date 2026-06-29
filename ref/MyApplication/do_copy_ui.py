import os
import shutil

src_model = r'D:\ADHD\adhd\app\src\main\java\com\example\adhd\model'
src_service = r'D:\ADHD\adhd\app\src\main\java\com\example\adhd\service'

dst_model = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\model'
dst_service = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\service'

if os.path.exists(dst_model): shutil.rmtree(dst_model)
if os.path.exists(dst_service): shutil.rmtree(dst_service)

shutil.copytree(src_model, dst_model)
shutil.copytree(src_service, dst_service)

def replace_package(d):
    for root, dirs, files in os.walk(d):
        for file in files:
            if file.endswith('.kt'):
                p = os.path.join(root, file)
                for enc in ['utf-8', 'gbk']:
                    try:
                        with open(p, 'r', encoding=enc) as f:
                            text = f.read()
                        text = text.replace('com.example.adhd', 'com.example.myapplication')
                        with open(p, 'w', encoding='utf-8') as f:
                            f.write(text)
                        break
                    except UnicodeDecodeError:
                        continue

replace_package(dst_model)
replace_package(dst_service)
print('Copied safely!')
