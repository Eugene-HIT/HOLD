kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_content = f.read()

if 'import android.view.ViewGroup' not in kt_content:
    kt_content = kt_content.replace('import android.view.View', 'import android.view.View\nimport android.view.ViewGroup')

# Also wait, when adding to debugContainer, we should know the indices!
# ivCamera was first, AI panel was second, btnPushToTalk was last.
# Let's fix reparentViews because if we naively addView without removing them, they throw 'Child already has a parent'. I handled it!

# We need to make sure the indices in debugContainer are somewhat correct.
# ivCamera might have been index 0, or index 2 depending on what textviews were there. Let's look at activity_main.xml.

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_content)
