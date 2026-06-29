# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_json_extract = '''                    try {
                        var cleanJson = replyText.trim()
                        if (cleanJson.startsWith("`json")) cleanJson = cleanJson.substring(7)
                        else if (cleanJson.startsWith("`")) cleanJson = cleanJson.substring(3)
                        if (cleanJson.endsWith("`")) cleanJson = cleanJson.substring(0, cleanJson.length - 3)
                        cleanJson = cleanJson.trim()

                        val aiData = org.json.JSONObject(cleanJson)'''

new_json_extract = '''                    try {
                        var cleanJson = replyText.trim()
                        val startIndex = cleanJson.indexOf("{")
                        val endIndex = cleanJson.lastIndexOf("}")
                        if (startIndex != -1 && endIndex != -1 && endIndex >= startIndex) {
                            cleanJson = cleanJson.substring(startIndex, endIndex + 1)
                        } else {
                            throw Exception("No JSON braces found in reply")
                        }

                        val aiData = org.json.JSONObject(cleanJson)'''

if old_json_extract in text:
    text = text.replace(old_json_extract, new_json_extract)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Robust JSON extraction applied.")
else:
    print("Could not find the json extract block.")
