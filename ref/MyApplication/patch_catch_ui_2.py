# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_catch = '''                    } catch (e: Exception) {
                        android.util.Log.e("AI_DEBUG", "Not JSON, fallback to raw: ")

                        val linesArray = replyText.split("\\n")'''

new_catch = '''                    } catch (e: Exception) {
                        val errMsg = e.message ?: "Unknown Error"
                        android.util.Log.e("AI_DEBUG", "Not JSON: \. Raw: \")
                        runOnUiThread { tvUserTask.text = "JSON失败: \" }
                        
                        val linesArray = replyText.split("\\n")'''

if old_catch in text:
    text = text.replace(old_catch, new_catch)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched catch block")
else:
    print("Could not find old_catch block!")
