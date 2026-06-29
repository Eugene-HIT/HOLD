import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update renderPool
old_render = '''private fun renderPool() {
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

new_render = '''private fun renderPool() {
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

if old_render in content:
    content = content.replace(old_render, new_render)
    print("renderPool patched")
else:
    print("renderPool NOT patched!!")

# 2. Update Anny replacement
old_anny = '''poolItems.add(0, HelpRequest("Anny", "想要\，状态是\"))
                          if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                          renderPool()'''
new_anny = '''val existingAnny = poolItems.find { it.userName == "Anny" }
                          if (existingAnny != null) {
                              existingAnny.userAction = "想要\，状态是\"
                          } else {
                              poolItems.add(0, HelpRequest("Anny", "想要\，状态是\"))
                              if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                          }
                          renderPool()'''

if old_anny in content:
    content = content.replace(old_anny, new_anny)
    print("anny patched")
else:
    print("anny NOT patched!!")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

