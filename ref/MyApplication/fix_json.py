with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

import re

old_code = '''                    try {
                        var contentStr = replyText.trim()
                        if (contentStr.startsWith("`json")) contentStr = contentStr.substring(7)
                        else if (contentStr.startsWith("`")) contentStr = contentStr.substring(3)
                        if (contentStr.endsWith("`")) contentStr = contentStr.substring(0, contentStr.length - 3)
                        contentStr = contentStr.trim()'''

new_code = '''                    try {
                        var contentStr = replyText.trim()
                        if (contentStr.startsWith("```json")) { contentStr = contentStr.substring(7) }
                        else if (contentStr.startsWith("```")) { contentStr = contentStr.substring(3) }
                        
                        if (contentStr.endsWith("```")) { contentStr = contentStr.substring(0, contentStr.length - 3) }
                        contentStr = contentStr.trim()'''

if old_code in text:
    text = text.replace(old_code, new_code)
    with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Fixed JSON parsing backticks!')
else:
    print('Pattern not found!')
