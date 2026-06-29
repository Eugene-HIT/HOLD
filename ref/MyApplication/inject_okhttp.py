import sys
content = open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8').read()

import_lines = '''import android.widget.EditText\nimport android.widget.Toast\n'''
content = content.replace('import android.widget.Button\n', 'import android.widget.Button\n' + import_lines)

code_to_insert = '''
        val etStatusInput = findViewById<EditText>(R.id.et_status_input)
        val btnSend = findViewById<Button>(R.id.btn_send_to_cloud)
        val cloudUrl = "https://cloud1-2g65h7na8576f841-1418292974.ap-shanghai.app.tcloudbase.com/update"

        btnSend?.setOnClickListener {
            val statusText = etStatusInput?.text?.toString() ?: ""
            if (statusText.isEmpty()) {
                Toast.makeText(this@MainActivity, "先写点状态再发嘛！", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val jsonObj = JSONObject()
            jsonObj.put("status", statusText)
            jsonObj.put("device_id", "Gulu_Android_001")
            jsonObj.put("heart_rate", 75)

            val body = okhttp3.RequestBody.create(
                "application/json; charset=utf-8".toMediaTypeOrNull(),
                jsonObj.toString()
            )
            val request = Request.Builder().url(cloudUrl).post(body).build()

            okHttpClient.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    Log.e("Gulu_Network", "发送失败: ${e.message}")
                    runOnUiThread {
                        Toast.makeText(this@MainActivity, "发送失败，看Logcat！", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onResponse(call: Call, response: Response) {
                    val responseData = response.body?.string()
                    Log.d("Gulu_Network", "云端返回: $responseData")
                    runOnUiThread {
                        Toast.makeText(this@MainActivity, "✅ 发送成功！快看小程序", Toast.LENGTH_SHORT).show()
                        etStatusInput?.text?.clear()
                    }
                }
            })
        }
'''

# Find the end of onCreate
# The last part of onCreate is:
end_of_oncreate = '''            } else {

                audioTrack?.pause()

                audioTrack?.flush()

            }

        }

    }'''

replacement = '''            } else {
                audioTrack?.pause()
                audioTrack?.flush()
            }
        }
#CODE_INSERT#
    }'''

if end_of_oncreate in content:
    content = content.replace(end_of_oncreate, replacement.replace('#CODE_INSERT#', code_to_insert))
    with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected OKHttp logic!")
else:
    print("Could not find end of onCreate. Trying another search str.")
    
    end2 = '''            } else {
                audioTrack?.pause()
                audioTrack?.flush()
            }
        }
    }'''
    if end2 in content:
        content = content.replace(end2, replacement.replace('#CODE_INSERT#', code_to_insert))
        with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Injected OKHttp logic! (via fallback)")
    else:
        print("Still could not find it.")
