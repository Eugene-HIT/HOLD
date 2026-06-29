# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

# 1. Top constants
p1_old = '    private val ZHIPU_KEY = "6781c79d4db14ec2bb75853a91352491.opzn28MO3bY2dho1"'
p1_new = '''    private val ZHIPU_KEY = "6781c79d4db14ec2bb75853a91352491.opzn28MO3bY2dho1"
    
    // 🌟 新增 1：云开发通信地址
    private val cloudMediaUrl = "https://cloud1-2g65h7na8576f841-1418292974.ap-shanghai.app.tcloudbase.com/update"'''

if p1_old in t and 'cloudMediaUrl' not in t:
    t = t.replace(p1_old, p1_new)
    print("Injected 1 (Constants)")

# 2. At the end of the file
p2_new = '''
    // 🌟 新增 2：专门发图片和语音的邮递员
    private fun uploadMediaToCloud(fileType: String, fileBytes: ByteArray) {
        val base64Str = android.util.Base64.encodeToString(fileBytes, android.util.Base64.NO_WRAP)
        val jsonObj = org.json.JSONObject()
        jsonObj.put("fileType", fileType)
        jsonObj.put("fileBase64", base64Str)

        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "媒体上传失败: " + e.message)
            }
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                android.util.Log.i("Gulu_Cloud", "云端返回: " + response.body?.string())
            }
        })
    }

    // 🌟 新增 3：专门发对话文字的邮递员
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

        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "文本同步失败: " + e.message)
            }
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                android.util.Log.i("Gulu_Cloud", "文本同步成功: " + response.body?.string())
            }
        })
    }
}'''

if 'uploadMediaToCloud' not in t:
    # replace last } with the methods and closing brace
    t = re.sub(r'\}\s*$', p2_new, t)
    print("Injected 2 & 3 (Functions)")

# 3. processAndUploadAudio Trigger
p3_old = r'val finalWavBytes = headerExtBuffer\.array\(\)(?:\s|\r|\n)*uploadToRealAI\(finalWavBytes\)'
p3_new = '''val finalWavBytes = headerExtBuffer.array()

          // 🌟 新增 4：把录好的硬件声音发给小程序！
          uploadMediaToCloud("audio", finalWavBytes)

          uploadToRealAI(finalWavBytes)'''

if re.search(p3_old, t) and 'uploadMediaToCloud("audio", finalWavBytes)' not in t:
    t = re.sub(p3_old, p3_new, t)
    print("Injected 4 (Audio trigger)")

# 4. uploadToRealAI STT trigger
p4_old = r'Log\.i\("AI_DEBUG", "STT Success: " \+ finalStr\)(?:\s|\r|\n)*runOnUiThread \{ tvUserVoice\.text'
p4_new = '''Log.i("AI_DEBUG", "STT Success: " + finalStr)
                        
                        // 🌟 新增 5：把 STT 识别到的你的话同步给小程序！
                        syncDialogueToCloud(finalStr, null, null)

                        runOnUiThread { tvUserVoice.text'''

if re.search(p4_old, t) and 'syncDialogueToCloud(finalStr, null, null)' not in t:
    t = re.sub(p4_old, p4_new, t)
    print("Injected 5 (STT trigger)")

# 5. callLLMForReply NLP trigger
p5_old = r'val finalReply = parsed\.optString\("reply", "好的"\)(?:\s|\r|\n)*runOnUiThread \{'
p5_new = '''val finalReply = parsed.optString("reply", "好的")
                        
                        // 🌟 新增 6：把大姐姐的回复和拆解的任务发给小程序！
                        syncDialogueToCloud(userText, finalReply, stepsList)

                        runOnUiThread {'''

if re.search(p5_old, t) and 'syncDialogueToCloud(userText, finalReply, stepsList)' not in t:
    t = re.sub(p5_old, p5_new, t)
    print("Injected 6 (LLM trigger)")
    
# also fix UI task icon optionally if needed by user
t = re.sub(r'it\.text = "【当前目标】：" \+ target', r'it.text = "🎯 【当前目标】：" + target', t)
t = re.sub(r'it\.text = "【当前状态】：" \+ state', r'it.text = "❤️ 【当前状态】：" + state', t)
t = re.sub(r'it\.text = "【行动建议】：" \+', r'it.text = "✅ 【行动建议】：" +', t)


with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t)

print("Patching Finished.")
