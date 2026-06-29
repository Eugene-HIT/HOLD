import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix layout params for reparented views
reparent_fn_old = '''    private fun reparentViews(toDetail: Boolean) {
        // Remove from current parents
        (ivCamera.parent as? android.view.ViewGroup)?.removeView(ivCamera)
        (aiDebugPanel.parent as? android.view.ViewGroup)?.removeView(aiDebugPanel)
        (btnPushToTalk.parent as? android.view.ViewGroup)?.removeView(btnPushToTalk)

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
    }'''

reparent_fn_new = '''    private fun reparentViews(toDetail: Boolean) {
        // Remove from current parents
        (ivCamera.parent as? android.view.ViewGroup)?.removeView(ivCamera)
        (aiDebugPanel.parent as? android.view.ViewGroup)?.removeView(aiDebugPanel)
        (btnPushToTalk.parent as? android.view.ViewGroup)?.removeView(btnPushToTalk)

        // Ensure proper LayoutParams so they don't shrink or become unusable
        val lpMatchWrap = android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
            android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply { setMargins(0, 24, 0, 0) }
        
        val lpCamera = android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
            (240 * resources.displayMetrics.density).toInt()
        ).apply { setMargins(0, 24, 0, 0) }

        ivCamera.layoutParams = lpCamera
        aiDebugPanel.layoutParams = lpMatchWrap
        btnPushToTalk.layoutParams = lpMatchWrap

        // Make button robust in scrollview
        btnPushToTalk.isFocusable = true
        btnPushToTalk.isClickable = true

        if (toDetail) {
            detailCameraContainer.addView(ivCamera)
            detailAiPanelContainer.addView(aiDebugPanel)
            detailPttContainer.addView(btnPushToTalk)
            
            // Bring them to front to catch touches
            detailPttContainer.bringToFront()
            btnPushToTalk.bringToFront()
        } else {
            debugContainer.addView(ivCamera, 3)
            debugContainer.addView(aiDebugPanel, 4)
            debugContainer.addView(btnPushToTalk, debugContainer.childCount)
        }
        
        ivCamera.requestLayout()
        btnPushToTalk.requestLayout()
    }'''

text = text.replace(reparent_fn_old, reparent_fn_new)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
