# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# 1. URL
if 'cloudMediaUrl' not in text:
    text = text.replace(
        'class MainActivity : AppCompatActivity() {',
        'class MainActivity : AppCompatActivity() {\n    private val cloudMediaUrl = "https://cloud1-2g65h7na8576f841-1418292974.ap-shanghai.app.tcloudbase.com/update"\n'
    )

# 2. Helper functions at end
helpers = '''
    // --- 新增：专门发图片和语音的邮递员 ---
    private fun uploadMediaToCloud(fileType: String, fileBytes: ByteArray) {
        val base64Str = android.util.Base64.encodeToString(fileBytes, android.util.Base64.NO_WRAP)
        val jsonObj = org.json.JSONObject()
        jsonObj.put("fileType", fileType)
        jsonObj.put("fileBase64", base64Str)

        val body = okhttp3.RequestBody.create(
            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),
            jsonObj.toString()
        )
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {}
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {}
        })
    }

    // --- 新增：专门发对话文字的邮递员 ---
    private fun syncDialogueToCloud(userText: String?, aiText: String?, steps: List<String>?) {
        val jsonObj = org.json.JSONObject()
        jsonObj.put("user_voice_text", userText ?: "")
        jsonObj.put("ai_reply_text", aiText ?: "")
        if (steps != null) {
            val jsonArray = org.json.JSONArray()
            steps.forEach { jsonArray.put(it) }
            jsonObj.put("ai_steps", jsonArray)
        }
        jsonObj.put("status", if (aiText != null) "🤖 Gulu已回复" else "🎤 Gulu正在思考...")

        val body = okhttp3.RequestBody.create(
            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),
            jsonObj.toString()
        )
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {}
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {}
        })
    }
}'''

if 'uploadMediaToCloud' not in text:
    text = text.rsplit('}', 1)[0] + helpers

# 3. Audio upload
if 'uploadMediaToCloud("audio", finalWavBytes)' not in text:
    text = text.replace(
        'uploadToRealAI(finalWavBytes)',
        'uploadMediaToCloud("audio", finalWavBytes)\n        uploadToRealAI(finalWavBytes)'
    )

# 4. Image upload
if 'uploadMediaToCloud("image", finalJpgBytes)' not in text:
    target_img = 'if (bufferData.size >= 2 && (bufferData[bufferData.size - 2].toInt() and 0xFF) == 0xFF && (bufferData[bufferData.size - 1].toInt() and 0xFF) == 0xD9) {\n                    runOnUiThread {'
    rep_img = 'if (bufferData.size >= 2 && (bufferData[bufferData.size - 2].toInt() and 0xFF) == 0xFF && (bufferData[bufferData.size - 1].toInt() and 0xFF) == 0xD9) {\n                    val finalJpgBytes = bufferData.clone()\n                    uploadMediaToCloud("image", finalJpgBytes)\n                    runOnUiThread {'
    if target_img in text:
        text = text.replace(target_img, rep_img)
    else:
        # Fallback regex
        text = re.sub(
            r'(\(bufferData\[bufferData\.size - 1\]\.toInt\(\) and 0xFF\) == 0xD9\)\s*\{\s*)(runOnUiThread\s*\{)',
            r'\1val finalJpgBytes = bufferData.clone()\n                    uploadMediaToCloud("image", finalJpgBytes)\n                    \2',
            text
        )

# 5. STT upload
if 'syncDialogueToCloud(finalStr' not in text:
    text = text.replace(
        'Log.i("AI_DEBUG", "STT Success: " + finalStr)',
        'Log.i("AI_DEBUG", "STT Success: " + finalStr)\n                            syncDialogueToCloud(finalStr, null, null)'
    )

# 6. LLM upload
if 'syncDialogueToCloud(userText' not in text:
    text = text.replace(
        'Log.i("AI_DEBUG", "LLM Success: " + replyText)',
        'Log.i("AI_DEBUG", "LLM Success: " + replyText)\n                    syncDialogueToCloud(userText, replyText, null)'
    )

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)

print("ALL PATCHES APPLIED!")
