import codecs
import re

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

# Add imports if missing
if 'import okhttp3.RequestBody.Companion.toRequestBody' not in t:
    t = t.replace('import okhttp3.OkHttpClient', 'import okhttp3.OkHttpClient\nimport okhttp3.RequestBody.Companion.toRequestBody\nimport okhttp3.MediaType.Companion.toMediaTypeOrNull')

t = re.sub(r'okhttp3\.RequestBody\.create\(\s*okhttp3\.MediaType\.parse\("([^"]+)"\),\s*([^)]+)\)',
           r'\2.toRequestBody("\1".toMediaTypeOrNull())',
           t)

codecs.open(p, 'w', 'utf-8').write(t)
print("Updated toRequestBody extension function!")
