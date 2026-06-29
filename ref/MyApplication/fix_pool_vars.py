import re
path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

vars_to_add = """
    private lateinit var poolListLayout: LinearLayout
    private lateinit var tabPool: TextView
    private lateinit var tabDebug: TextView
    private lateinit var poolView: android.view.View
    private lateinit var debugScroll: android.widget.ScrollView
    
    private lateinit var helpDetailView: android.view.View
    private lateinit var btnBackToPool: android.widget.Button
    private lateinit var tvDetailTitle: TextView
    private lateinit var tvDetailTask: TextView
    
    private lateinit var debugContainer: LinearLayout
    private lateinit var detailCameraContainer: android.widget.FrameLayout
    private lateinit var detailAiPanelContainer: android.widget.FrameLayout
    private lateinit var detailPttContainer: android.widget.FrameLayout
    private lateinit var aiDebugPanel: android.view.View
    
    data class HelpRequest(
        val userName: String,
        val userAction: String
    )
    private val poolItems = mutableListOf<HelpRequest>()
"""

if "poolListLayout" not in content[:content.find("onCreate")]:
    content = content.replace("class MainActivity : AppCompatActivity() {", "class MainActivity : AppCompatActivity() {\n" + vars_to_add)

if "private fun reparentViews" not in content and "fun reparentViews" not in content:
    reparent_code = """
    private fun reparentViews(toDetail: Boolean) {
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
    }
    
    private fun renderPool() {
        poolListLayout.removeAllViews()
        for (item in poolItems) {
            val tv = TextView(this)
            tv.text = "${item.userName} ${item.userAction}"
            tv.textSize = 18f
            tv.setPadding(32, 32, 32, 32)
            tv.setBackgroundResource(android.R.drawable.dialog_holo_light_frame)
            tv.setOnClickListener {
                poolView.visibility = android.view.View.GONE
                helpDetailView.visibility = android.view.View.VISIBLE
                tvDetailTitle.text = "${item.userName} 的求助"
                tvDetailTask.text = "任务: ${item.userAction}"
                reparentViews(true)
                findViewById<android.view.View>(R.id.bottom_nav_container).visibility = android.view.View.GONE
            }
            poolListLayout.addView(tv)
        }
    }
"""
    content = content.replace("override fun onCreate", reparent_code + "\n    override fun onCreate")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
