import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's cleanly inject the pool UI logic and tab listeners in onCreate
insert_str = '''
        // Pool UI setup
        poolListLayout = findViewById(R.id.poolListLayout)
        tabPool = findViewById(R.id.tab_pool)
        tabDebug = findViewById(R.id.tab_debug)
        poolView = findViewById(R.id.pool_view)
        debugScroll = findViewById(R.id.debug_scroll)
        helpDetailView = findViewById(R.id.help_detail_view)
        btnBackToPool = findViewById(R.id.btn_back_to_pool)
        tvDetailTitle = findViewById(R.id.tv_detail_title)
        tvDetailTask = findViewById(R.id.tv_detail_task)

        debugContainer = findViewById(R.id.debug_container)
        detailCameraContainer = findViewById(R.id.detail_camera_container)
        detailAiPanelContainer = findViewById(R.id.detail_ai_panel_container)
        detailPttContainer = findViewById(R.id.detail_ptt_container)
        aiDebugPanel = findViewById(R.id.ai_debug_panel)

        btnBackToPool.setOnClickListener {
            helpDetailView.visibility = android.view.View.GONE
            reparentViews(false)
            poolView.visibility = android.view.View.VISIBLE
            findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.VISIBLE
        }

        tabPool.setOnClickListener {
            debugScroll.visibility = android.view.View.GONE
            poolView.visibility = android.view.View.VISIBLE
            tabPool.backgroundTintList = android.content.res.ColorStateList.valueOf(android.graphics.Color.parseColor("#E7EDF8"))
            tabPool.setTextColor(android.graphics.Color.parseColor("#3B82F6"))
            tabDebug.backgroundTintList = android.content.res.ColorStateList.valueOf(android.graphics.Color.parseColor("#F3F4F6"))
            tabDebug.setTextColor(android.graphics.Color.parseColor("#9CA3AF"))
        }

        tabDebug.setOnClickListener {
            poolView.visibility = android.view.View.GONE
            debugScroll.visibility = android.view.View.VISIBLE
            tabDebug.backgroundTintList = android.content.res.ColorStateList.valueOf(android.graphics.Color.parseColor("#E7EDF8"))
            tabDebug.setTextColor(android.graphics.Color.parseColor("#3B82F6"))
            tabPool.backgroundTintList = android.content.res.ColorStateList.valueOf(android.graphics.Color.parseColor("#F3F4F6"))
            tabPool.setTextColor(android.graphics.Color.parseColor("#9CA3AF"))
        }

        poolItems.add(HelpRequest("Anny", "想吃苹果，状态是感觉很饿"))
        poolItems.add(HelpRequest("Tom", "不知道要做什么，状态是迷茫"))
'''

if 'poolListLayout = findViewById(R.id.poolListLayout)' not in text:
    text = text.replace('setContentView(R.layout.activity_main)', 'setContentView(R.layout.activity_main)\n' + insert_str)
    with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected UI setup")
else:
    print("UI setup already exists")

