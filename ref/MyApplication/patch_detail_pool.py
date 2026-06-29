import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update HelpRequest Data Class
old_help_request = '''    data class HelpRequest(
        val userName: String,
        val userAction: String
    )
    private val poolItems = mutableListOf<HelpRequest>()'''
new_help_request = '''    data class HelpRequest(
        val userName: String,
        var userAction: String,
        var timestamp: Long = System.currentTimeMillis()
    )
    private val poolItems = mutableListOf<HelpRequest>()
    private val timerViews = mutableListOf<Pair<TextView, HelpRequest>>()
    private val poolUpdateHandler = Handler(Looper.getMainLooper())
    private val poolUpdateRunnable = object : Runnable {
        override fun run() {
            updatePoolTimers()
            poolUpdateHandler.postDelayed(this, 1000)
        }
    }
    private fun updatePoolTimers() {
        val now = System.currentTimeMillis()
        for (pair in timerViews) {
            val tv = pair.first
            val item = pair.second
            val diffSeconds = (now - item.timestamp) / 1000
            tv.text = "等待 s"
        }
    }'''
content = content.replace(old_help_request, new_help_request)

# 2. Update renderPool implementation
old_render_pool = '''    private fun renderPool() {
        poolListLayout.removeAllViews()
        for (item in poolItems) {
            val tv = TextView(this)
            tv.text = "\ \"
            tv.textSize = 18f
            tv.setPadding(32, 32, 32, 32)
            tv.setBackgroundResource(android.R.drawable.dialog_holo_light_frame)
            tv.setOnClickListener {
                poolView.visibility = android.view.View.GONE
                helpDetailView.visibility = android.view.View.VISIBLE
                tvDetailTitle.text = "\ 的求助"
                tvDetailTask.text = "任务: \"
                reparentViews(true)
                findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.GONE
            }
            poolListLayout.addView(tv)
        }
    }'''

new_render_pool = '''    private fun renderPool() {
        poolListLayout.removeAllViews()
        timerViews.clear()
        for (item in poolItems) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(0, 0, 0, 24)
                }
                background = android.graphics.drawable.GradientDrawable().apply {
                    setColor(android.graphics.Color.WHITE)
                    cornerRadius = 24f
                }
                elevation = 8f
                setPadding(40, 40, 40, 40)
            }

            val headerLayout = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
            }

            val nameText = TextView(this).apply {
                text = "\ 的求助"
                textSize = 18f
                setTypeface(null, android.graphics.Typeface.BOLD)
                setTextColor(android.graphics.Color.parseColor("#374151"))
                layoutParams = LinearLayout.LayoutParams(
                    0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f
                )
            }

            val timeText = TextView(this).apply {
                text = "等待 0s"
                textSize = 12f
                setTextColor(android.graphics.Color.parseColor("#EA580C"))
                setTypeface(null, android.graphics.Typeface.BOLD)
            }
            timerViews.add(Pair(timeText, item))

            headerLayout.addView(nameText)
            headerLayout.addView(timeText)

            val taskText = TextView(this).apply {
                text = item.userAction
                textSize = 14f
                setTextColor(android.graphics.Color.parseColor("#6B7280"))
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(0, 12, 0, 0)
                }
            }

            card.addView(headerLayout)
            card.addView(taskText)

            card.setOnClickListener {
                poolView.visibility = android.view.View.GONE
                helpDetailView.visibility = android.view.View.VISIBLE
                tvDetailTitle.text = "\ 的求助"
                tvDetailTask.text = "任务: \"
                reparentViews(true)
                findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.GONE
            }
            poolListLayout.addView(card)
        }
        updatePoolTimers()
    }'''
content = content.replace(old_render_pool, new_render_pool)

# 3. Update reparentViews
old_reparent = '''    private fun reparentViews(toDetail: Boolean) {
        if (aiDebugPanel.parent != null) {
            (aiDebugPanel.parent as android.view.ViewGroup).removeView(aiDebugPanel)
        }
        if (ivCamera.parent != null) {
            (ivCamera.parent as android.view.ViewGroup).removeView(ivCamera)
        }
        if (tbPlayAudio.parent != null) {
            (tbPlayAudio.parent as android.view.ViewGroup).removeView(tbPlayAudio)
        }

        if (toDetail) {
            detailAiPanelContainer.addView(aiDebugPanel)
            detailCameraContainer.addView(ivCamera)
            detailPttContainer.addView(tbPlayAudio)
        } else {
            debugContainer.addView(aiDebugPanel)
            debugContainer.addView(ivCamera)
            debugContainer.addView(tbPlayAudio)
        }
    }'''

new_reparent = '''    private fun reparentViews(toDetail: Boolean) {
        val pttBtn = findViewById<Button>(R.id.btnPushToTalk)
        if (aiDebugPanel.parent != null) {
            (aiDebugPanel.parent as android.view.ViewGroup).removeView(aiDebugPanel)
        }
        if (ivCamera.parent != null) {
            (ivCamera.parent as android.view.ViewGroup).removeView(ivCamera)
        }
        if (pttBtn.parent != null) {
            (pttBtn.parent as android.view.ViewGroup).removeView(pttBtn)
        }

        if (toDetail) {
            detailAiPanelContainer.addView(aiDebugPanel)
            detailCameraContainer.addView(ivCamera)
            detailPttContainer.addView(pttBtn)
        } else {
            debugContainer.addView(aiDebugPanel)
            debugContainer.addView(ivCamera)
            debugContainer.addView(pttBtn)
        }
    }'''
content = content.replace(old_reparent, new_reparent)

# 4. Inject pool handler start
old_onCreate = '''        poolItems.add(HelpRequest("Tom", "不知道要做什么，状态是迷茫"))
        renderPool()'''
new_onCreate = '''        poolItems.add(HelpRequest("Tom", "不知道要做什么，状态是迷茫"))
        renderPool()
        poolUpdateHandler.post(poolUpdateRunnable)'''
content = content.replace(old_onCreate, new_onCreate)

# 5. Overwrite AI's creation of multiple Anny requests
old_anny_add = '''                          poolItems.add(0, HelpRequest("Anny", "想要\，状态是\"))
                          if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                          renderPool()'''
new_anny_add = '''                          val existingAnny = poolItems.find { it.userName == "Anny" }
                          if (existingAnny != null) {
                              existingAnny.userAction = "想要\，状态是\"
                          } else {
                              poolItems.add(0, HelpRequest("Anny", "想要\，状态是\"))
                          }
                          if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                          renderPool()'''
content = content.replace(old_anny_add, new_anny_add)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied")
