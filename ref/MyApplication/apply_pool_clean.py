# -*- coding: utf-8 -*-
import sys
import re
import codecs

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Variables
old_vars = "    private lateinit var btnBackToPool: android.widget.Button"
new_vars = '''    private lateinit var btnBackToPool: android.widget.Button

    // Task and Pool UI
    private lateinit var tvDetailTask: android.widget.TextView
    private lateinit var tvDetailStt: android.widget.TextView
    private lateinit var taskListContainer: android.widget.LinearLayout
    private lateinit var poolListLayout: android.widget.LinearLayout
    private lateinit var congratsContainer: android.widget.LinearLayout

    private lateinit var tvUserTask: TextView
    private lateinit var tvUserState: TextView
    private lateinit var tvActionSteps: TextView

    data class HelpRequest(val userName: String, var userAction: String, var timestamp: Long, var steps: List<String> = emptyList())
    private val poolItems = mutableListOf<HelpRequest>()'''
if 'private val poolItems =' not in text:
    text = text.replace(old_vars, new_vars, 1)

# 2. Views
old_views = "        btnBackToPool = findViewById(R.id.btn_back_to_pool)"
new_views = '''        btnBackToPool = findViewById(R.id.btn_back_to_pool)

        tvDetailTask = findViewById(R.id.tv_detail_task)
        tvDetailStt = findViewById(R.id.tv_detail_stt)
        taskListContainer = findViewById(R.id.task_list_container)
        congratsContainer = findViewById(R.id.congrats_container)
        poolListLayout = findViewById(R.id.poolListLayout)

        tvUserTask = findViewById(R.id.tvUserTask)
        tvUserState = findViewById(R.id.tvUserState)
        tvActionSteps = findViewById(R.id.tvActionSteps)'''
if 'tvUserTask = findViewById(R.id.tvUserTask)' not in text:
    text = text.replace(old_views, new_views, 1)

# 3. JSON Call
idx1 = text.find('if (historyLog.size > 10) historyLog.removeAt(0)')
idx1 = text.find('Log.i("AI_DEBUG", "LLM Success: " + replyText)', idx1)
idx2 = text.find('callTTSForAudio(replyText)', idx1)
if idx1 > 0 and idx2 > 0 and 'var userTask = \"未知\"' not in text:
    old_str = text[idx1:idx2]
    new_str = '''Log.i("AI_DEBUG", "LLM Success: " + replyText)

                    var userTask = "未知"
                    var userState = "未知"
                    var stepsText = "等待识别..."
                    val extractedSteps = mutableListOf<String>()

                    try {
                        var contentStr = replyText.trim()
                        if (contentStr.startsWith("`json")) contentStr = contentStr.substring(7)
                        else if (contentStr.startsWith("`")) contentStr = contentStr.substring(3)
                        if (contentStr.endsWith("`")) contentStr = contentStr.substring(0, contentStr.length - 3)
                        contentStr = contentStr.trim()

                        val contentObj = org.json.JSONObject(contentStr)
                        val innerReply = contentObj.optString("reply")
                        if (innerReply.isNotEmpty()) replyText = innerReply
                        userTask = contentObj.optString("user_task", "未知")
                        userState = contentObj.optString("user_state", "未知")
                        val stepsArray = contentObj.optJSONArray("steps")
                        if (stepsArray != null && stepsArray.length() > 0) {
                            val sb = java.lang.StringBuilder()
                            for (i in 0 until stepsArray.length()) {
                                val s = stepsArray.getString(i)
                                extractedSteps.add(s)
                                sb.append(i + 1).append(". ").append(s).append("\\n")
                            }
                            stepsText = sb.toString().trim()
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }

                    runOnUiThread {
                        tvAiReply.text = "AI: " + replyText
                        tvAiStatus.text = "🔊 正在全自动生成逼真语音(TTS)..."
                        tvUserTask.text = "🎯 目标任务：" + userTask
                        tvUserState.text = "💡 当前状态：" + userState
                        tvActionSteps.text = "🪜 拆解步骤：\\n" + stepsText

                        val actionText = "想要" + userTask + "，状态是" + userState
                        val existingAnny = poolItems.find { it.userName == "Anny" }
                        if (existingAnny != null) {
                            existingAnny.userAction = actionText
                            existingAnny.timestamp = System.currentTimeMillis()
                            existingAnny.steps = extractedSteps
                        } else {
                            poolItems.add(0, HelpRequest("Anny", actionText, System.currentTimeMillis(), extractedSteps))
                            if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                        }
                        renderPool()
                    }
                    '''
    text = text.replace(old_str, new_str, 1)

# 4. Render code
render_code = '''
    private fun renderPool() {
        poolListLayout.removeAllViews()
        for (item in poolItems) {
            val view = layoutInflater.inflate(R.layout.pool_item, poolListLayout, false)
            val tvName = view.findViewById<TextView>(R.id.tv_pool_name)
            val tvAction = view.findViewById<TextView>(R.id.tv_pool_action)
            val tvTime = view.findViewById<TextView>(R.id.tv_pool_time)

            tvName.text = item.userName
            tvAction.text = item.userAction
            val minutesAgo = (System.currentTimeMillis() - item.timestamp) / 60000
            tvTime.text = "${minutesAgo}分钟前"

            view.setOnClickListener {
                showHelpDetail(item)
            }
            poolListLayout.addView(view)
        }
    }

    private fun showHelpDetail(item: HelpRequest) {
        poolView.visibility = android.view.View.GONE
        helpDetailView.visibility = android.view.View.VISIBLE

        tvDetailTask.text = "🎯 " + item.userAction

        taskListContainer.removeAllViews()
        for (i in item.steps.indices) {
            val stepView = layoutInflater.inflate(R.layout.task_item, taskListContainer, false)
            val cb = stepView.findViewById<android.widget.CheckBox>(R.id.cb_task)
            val title = stepView.findViewById<TextView>(R.id.tv_task_title)
            title.text = item.steps[i]

            cb.setOnCheckedChangeListener { _, isChecked ->
                title.paintFlags = if (isChecked) title.paintFlags or android.graphics.Paint.STRIKE_THRU_TEXT_FLAG else title.paintFlags and android.graphics.Paint.STRIKE_THRU_TEXT_FLAG.inv()
            }
            taskListContainer.addView(stepView)
        }
    }
'''

if "private fun renderPool" not in text:
    idx = text.rfind('}')
    text = text[:idx] + render_code + '\n}'

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Pool applied')
