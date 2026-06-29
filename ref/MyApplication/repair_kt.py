import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_content = f.read()

# Add necessary variables at top of class
vars_to_add = '''
    private lateinit var debugContainer: LinearLayout
    private lateinit var detailCameraContainer: LinearLayout
    private lateinit var detailAiPanelContainer: LinearLayout
    private lateinit var detailPttContainer: LinearLayout
    private lateinit var aiDebugPanel: LinearLayout
'''
if 'private lateinit var debugContainer' not in kt_content:
    kt_content = kt_content.replace('private lateinit var tvDetailTask: TextView', 'private lateinit var tvDetailTask: TextView' + vars_to_add)

# Map views in onCreate
map_to_add = '''
        debugContainer = findViewById(R.id.debug_container)
        detailCameraContainer = findViewById(R.id.detail_camera_container)
        detailAiPanelContainer = findViewById(R.id.detail_ai_panel_container)
        detailPttContainer = findViewById(R.id.detail_ptt_container)
        aiDebugPanel = findViewById(R.id.ai_debug_panel)
'''
if 'findViewById(R.id.debug_container)' not in kt_content:
    kt_content = kt_content.replace('tvDetailTask = findViewById(R.id.tv_detail_task)', 'tvDetailTask = findViewById(R.id.tv_detail_task)\n' + map_to_add)

# Create a reparent function
reparent_fn = '''
    private fun reparentViews(toDetail: Boolean) {
        // Remove from current parents
        (ivCamera.parent as? ViewGroup)?.removeView(ivCamera)
        (aiDebugPanel.parent as? ViewGroup)?.removeView(aiDebugPanel)
        (btnPushToTalk.parent as? ViewGroup)?.removeView(btnPushToTalk)

        if (toDetail) {
            detailCameraContainer.addView(ivCamera)
            detailAiPanelContainer.addView(aiDebugPanel)
            detailPttContainer.addView(btnPushToTalk)
        } else {
            // Put them back to debug container in original order
            // Here we just add them to the end, but normally we'd respect order. Since we only transition out of detail, appending or ensuring correct layout is fine, 
            // but realistically we should put them back inside debug_container.
            // For simplicity, debug_container is a LinearLayout. 
            debugContainer.addView(ivCamera, 0)
            debugContainer.addView(aiDebugPanel, 1)
            debugContainer.addView(btnPushToTalk, debugContainer.childCount)
        }
    }
'''
if 'private fun reparentViews' not in kt_content:
    kt_content = kt_content.replace('private fun renderPool()', reparent_fn + '\n    private fun renderPool()')

# Call reparentViews when opening detail
if 'helpDetailView.visibility = View.VISIBLE' in kt_content and 'reparentViews(true)' not in kt_content:
    kt_content = kt_content.replace('helpDetailView.visibility = View.VISIBLE', 'helpDetailView.visibility = View.VISIBLE\n                reparentViews(true)\n                debugContainer.visibility = View.GONE\n                debugScroll.visibility = View.GONE\n                tabPool.visibility = View.GONE\n                tabDebug.visibility = View.GONE')

# Call reparentViews when going back
if 'helpDetailView.visibility = View.GONE' in kt_content and 'reparentViews(false)' not in kt_content:
    kt_content = kt_content.replace('helpDetailView.visibility = View.GONE', 'helpDetailView.visibility = View.GONE\n            reparentViews(false)\n            tabPool.visibility = View.VISIBLE\n            tabDebug.visibility = View.VISIBLE')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_content)
print("Kotlin Repaired!")
