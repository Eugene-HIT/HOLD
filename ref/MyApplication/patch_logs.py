# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

pattern1 = r'''        okHttpClient\.newCall\(request\)\.enqueue\(object : okhttp3\.Callback \{\s+override fun onFailure\(call: okhttp3\.Call, e: java\.io\.IOException\) \{\}\s+override fun onResponse\(call: okhttp3\.Call, response: okhttp3\.Response\) \{\}\s+\}\)\s+\}

    // --- 新增：专门发对话文字的邮递员 ---'''

replacement1 = '''        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                // 🌟 加了这行，失败了你就能在 Logcat 看到！
                android.util.Log.e("Gulu_Cloud", "\ 媒体上传失败: \")
            }
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                // 🌟 加了这行，成功了也能看到云端的回复！
                android.util.Log.i("Gulu_Cloud", "\ 云端返回: \")
            }
        })
    }

    // --- 新增：专门发对话文字的邮递员 ---'''
    
pattern2 = r'''        okHttpClient\.newCall\(request\)\.enqueue\(object : okhttp3\.Callback \{\s+override fun onFailure\(call: okhttp3\.Call, e: java\.io\.IOException\) \{\}\s+override fun onResponse\(call: okhttp3\.Call, response: okhttp3\.Response\) \{\}\s+\}\)\s+\}\s+\}'''

replacement2 = '''        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "文本同步失败: \")
            }
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                android.util.Log.i("Gulu_Cloud", "文本同步成功: \")
            }
        })
    }
}'''

text = re.sub(pattern1, replacement1, text)
text = re.sub(pattern2, replacement2, text)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)

print("Logs added successfully.")
