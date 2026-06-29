import re
kt_path = 'app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

dup_block = """    private var isInHelpDetail = false
    private var completedTasks = 0
    private lateinit var tvDetailStt: android.widget.TextView
    private lateinit var taskListContainer: android.widget.LinearLayout
    private lateinit var congratsContainer: android.widget.LinearLayout
    private lateinit var btnDetailDisconnect: android.widget.Button
    private lateinit var detailPttContainer: android.widget.LinearLayout"""

# Remove all duplicates and keep only 1
count = text.count(dup_block)
if count > 1:
    text = text.replace(dup_block, '', count - 1)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Deduplicated decls!")
