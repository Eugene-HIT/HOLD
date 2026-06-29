import sys

path = r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# I need to fix the broken JSON setup for LLM.
target = '''        val reqBodyJson = JsonObject().apply {
              addProperty("model", "glm-4-flash")
              add("messages", messagesArray)
                val formatObj = JsonObject()
                formatObj.addProperty("type", "json_object")
                add("response_format", formatObj)
          val request = Request.Builder()'''

replacement = '''        val reqBodyJson = JsonObject().apply {
              addProperty("model", "glm-4-flash")
              add("messages", messagesArray)
              val formatObj = JsonObject()
              formatObj.addProperty("type", "json_object")
              add("response_format", formatObj)
          }

          val body = okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())
          val request = Request.Builder()'''

text = text.replace(target, replacement)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("done kt fix")
