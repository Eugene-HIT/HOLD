import re

kt_path = 'app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add variables
var_pattern = r'(private lateinit var detailPttContainer: android\.widget\.LinearLayout\s+private lateinit var aiDebugPanel: android\.view\.View)'
var_repl = r'''\1

    // Detail UI newly added
    private var isInHelpDetail = false
    private var completedTasks = 0
    private lateinit var tvDetailStt: TextView
    private lateinit var taskListContainer: LinearLayout
    private lateinit var congratsContainer: LinearLayout
    private lateinit var btnDetailDisconnect: Button
'''
text = re.sub(var_pattern, var_repl, text)

# 2. Add findView logic
find_pattern = r'(detailPttContainer = findViewById\(R\.id\.detail_ptt_container\)\s+aiDebugPanel = findViewById\(R\.id\.ai_debug_panel\))'
find_repl = r'''\1

        tvDetailStt = findViewById(R.id.tv_detail_stt)
        taskListContainer = findViewById(R.id.task_list_container)
        congratsContainer = findViewById(R.id.congrats_container)
        btnDetailDisconnect = findViewById(R.id.btn_detail_disconnect)
        
        btnDetailDisconnect.setOnClickListener {
            // Just simulate going back
            btnBackToPool.performClick()
        }
'''
text = re.sub(find_pattern, find_repl, text)

# 3. Add to btnBackToPool
back_pattern = r'(btnBackToPool\.setOnClickListener \{[\s\S]*?findViewById<android\.view\.View>\(R\.id\.bottom_nav_container\)\.visibility = android\.view\.View\.VISIBLE\s*\})'
back_repl = r'''btnBackToPool.setOnClickListener {
            helpDetailView.visibility = android.view.View.GONE
            reparentViews(false)
            poolView.visibility = android.view.View.VISIBLE
            findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.VISIBLE
            isInHelpDetail = false
            completedTasks = 0
        }'''
text = re.sub(back_pattern, back_repl, text)

# 4. Modify STT
stt_pattern = r'(Log\.i\("AI_DEBUG", "STT Success: " \+ finalStr\)\s+runOnUiThread \{ tvUserVoice\.text = "[^"]*" \+ finalStr; tvAiStatus\.text = "[^"]*" \}\s+)callLLMForReply\(finalStr\)'
stt_repl = r'''\1if (isInHelpDetail) {
                            runOnUiThread {
                                tvDetailStt.text = finalStr
                                tvAiStatus.text = " 手动介入模式，系统只记录对话"
                            }
                            resetAI(500) // skip calling LLM, just reset AI STT states for next recording
                        } else {
                            callLLMForReply(finalStr)
                        }'''
text = re.sub(stt_pattern, stt_repl, text)

# 5. Modify card.setOnClickListener
card_pattern = r'(card\.setOnClickListener \{[\s\S]*?reparentViews\(true\)[\s\S]*?findViewById<android\.view\.View>\(R\.id\.bottom_nav_container\)\.visibility = android\.view\.View\.GONE)'
card_repl = r'''\1
                isInHelpDetail = true
                setupDetailTasks(item.userAction)'''
text = re.sub(card_pattern, card_repl, text)

# 6. Add setupDetailTasks function
setup_tasks_code = r'''
    private fun setupDetailTasks(taskDesc: String) {
        completedTasks = 0
        congratsContainer.visibility = android.view.View.GONE
        taskListContainer.removeAllViews()
        tvDetailStt.text = "等待长辈语音输入..."
        val sampleTasks = listOf("解析当前状态: " + taskDesc, "安抚情绪并准备", "执行微小动作(拍照自动确认)")
        for (i in sampleTasks.indices) {
            val itemLayout = android.widget.LinearLayout(this).apply {
                orientation = android.widget.LinearLayout.HORIZONTAL
                layoutParams = android.widget.LinearLayout.LayoutParams(
                    android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                    android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { setMargins(0, 12, 0, 12) }
                gravity = android.view.Gravity.CENTER_VERTICAL
            }
            val tvTask = TextView(this).apply {
                text = ". "
                textSize = 16f
                setTextColor(android.graphics.Color.parseColor("#333333"))
                layoutParams = android.widget.LinearLayout.LayoutParams(0, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }
            val cbTask = android.widget.CheckBox(this).apply {
                isClickable = false
                buttonTintList = android.content.res.ColorStateList.valueOf(android.graphics.Color.parseColor("#059669"))
                tag = "task_cb_"
            }
            itemLayout.addView(tvTask)
            itemLayout.addView(cbTask)
            taskListContainer.addView(itemLayout)
        }
    }
'''
if 'fun setupDetailTasks' not in text:
    # Just append it before the last brace
    text = text.rsprint('}', 1) # wait, rsprint is not python.
    last_brace_index = text.rfind('}')
    text = text[:last_brace_index] + setup_tasks_code + text[last_brace_index:]

# 7. Image completion hook
img_pattern = r'(val bitmap = android\.graphics\.BitmapFactory\.decodeByteArray\(bufferData, 0, exactSize\)\s+if \(bitmap != null\) \{\s+ivCamera\.setImageBitmap\(bitmap\))'
img_repl = r'''\1
                                        if (isInHelpDetail && completedTasks < 3) {
                                            val cbTask = taskListContainer.findViewWithTag<android.widget.CheckBox>("task_cb_")
                                            cbTask?.isChecked = true
                                            completedTasks++
                                            if (completedTasks >= 3) {
                                                congratsContainer.visibility = android.view.View.VISIBLE
                                            }
                                        }'''
text = re.sub(img_pattern, img_repl, text)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("KT Patched!")
