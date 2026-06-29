import re
kt_path = 'app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add variable declarations at the start of class
class_start = text.find('class MainActivity : AppCompatActivity() {')
if class_start != -1:
    idx = text.find('{', class_start) + 1
    decl = '''
    private var isInHelpDetail = false
    private var completedTasks = 0
    private lateinit var tvDetailStt: android.widget.TextView
    private lateinit var taskListContainer: android.widget.LinearLayout
    private lateinit var congratsContainer: android.widget.LinearLayout
    private lateinit var btnDetailDisconnect: android.widget.Button
    private lateinit var detailPttContainer: android.widget.LinearLayout
'''
    text = text[:idx] + decl + text[idx:]

# Find view instances in onCreate
on_create_start = text.find('setContentView(R.layout.activity_main)')
if on_create_start != -1:
    idx = text.find('\n', on_create_start) + 1
    init = '''
        tvDetailStt = findViewById(R.id.tv_detail_stt)
        taskListContainer = findViewById(R.id.task_list_container)
        congratsContainer = findViewById(R.id.congrats_container)
        btnDetailDisconnect = findViewById(R.id.btn_detail_disconnect)
        detailPttContainer = findViewById(R.id.detail_ptt_container)
        
        btnDetailDisconnect.setOnClickListener {
            findViewById<android.widget.Button>(R.id.btn_back_to_pool).performClick()
        }
'''
    text = text[:idx] + init + text[idx:]

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Declarations forced!")
