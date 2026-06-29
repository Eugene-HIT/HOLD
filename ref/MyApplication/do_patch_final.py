import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_render_pool = '''private fun renderPool() {
        poolListLayout.removeAllViews()
        timerViews.clear()
        for (item in poolItems) {
            val card = android.widget.LinearLayout(this).apply {
                orientation = android.widget.LinearLayout.VERTICAL
                layoutParams = android.widget.LinearLayout.LayoutParams(
                    android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                    android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
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

            val headerLayout = android.widget.LinearLayout(this).apply {
                orientation = android.widget.LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
                layoutParams = android.widget.LinearLayout.LayoutParams(
                    android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                    android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
                )
            }

            val nameText = android.widget.TextView(this).apply {
                text = item.userName + " 的求助"
                textSize = 18f
                setTypeface(null, android.graphics.Typeface.BOLD)
                setTextColor(android.graphics.Color.parseColor("#374151"))
                layoutParams = android.widget.LinearLayout.LayoutParams(
                    0, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT, 1f
                )
            }

            val timeText = android.widget.TextView(this).apply {
                text = "等待 0s"
                textSize = 12f
                setTextColor(android.graphics.Color.parseColor("#EA580C"))
                setTypeface(null, android.graphics.Typeface.BOLD)
            }
            timerViews.add(Pair(timeText, item))

            headerLayout.addView(nameText)
            headerLayout.addView(timeText)

            val taskText = android.widget.TextView(this).apply {
                text = item.userAction
                textSize = 14f
                setTextColor(android.graphics.Color.parseColor("#6B7280"))
                layoutParams = android.widget.LinearLayout.LayoutParams(
                    android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                    android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(0, 12, 0, 0)
                }
            }

            card.addView(headerLayout)
            card.addView(taskText)

            card.setOnClickListener {
                poolView.visibility = android.view.View.GONE
                helpDetailView.visibility = android.view.View.VISIBLE
                tvDetailTitle.text = item.userName + " 的求助"
                tvDetailTask.text = "任务: " + item.userAction
                reparentViews(true)
                findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.GONE
            }
            poolListLayout.addView(card)
        }
        updatePoolTimers()
    }'''

content = re.sub(r'private fun renderPool\(\) \{.*?(?=override fun onCreate)', new_render_pool + '\n\n    ', content, flags=re.DOTALL)

old_anny = r'''poolItems.add(0, HelpRequest\("Anny", "想要\$\{userTask\}，状态是\$\{userState\}"\))
                          if \(poolItems.size > 10\) poolItems.removeAt\(poolItems.size - 1\)
                          renderPool\(\)'''
new_anny = '''val existingAnny = poolItems.find { it.userName == "Anny" }
                          if (existingAnny != null) {
                              existingAnny.userAction = "想要，状态是"
                              existingAnny.timestamp = System.currentTimeMillis()
                          } else {
                              poolItems.add(0, HelpRequest("Anny", "想要，状态是"))
                              if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                          }
                          renderPool()'''
content = re.sub(old_anny, new_anny, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Final patch complete")