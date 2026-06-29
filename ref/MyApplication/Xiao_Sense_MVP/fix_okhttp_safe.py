import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

# Add needed okhttp extension imports
if 'import okhttp3.RequestBody.Companion.toRequestBody' not in t:
    t = t.replace('import okhttp3.OkHttpClient', 
                  'import okhttp3.OkHttpClient\nimport okhttp3.RequestBody.Companion.toRequestBody\nimport okhttp3.MediaType.Companion.toMediaTypeOrNull')

# Fix LLM Call Body
s1 = 'val body = okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json"), reqBodyJson.toString())'
r1 = 'val body = reqBodyJson.toString().toRequestBody("application/json".toMediaTypeOrNull())'
t = t.replace(s1, r1)

# Fix Response Body deprecation
s2 = 'val respStr = response.body()?.string() ?: ""'
r2 = 'val respStr = response.body?.string() ?: ""'
t = t.replace(s2, r2)
s3 = 'val respStr = response.body?.string() ?: ""\n                try {' # wait, patch_final.py used .body()
# patch_final used `val respStr = response.body()?.string() ?: ""`
# Let's just do:
t = t.replace('response.body()?.string()', 'response.body?.string()')

# Fix cloud sync body RequestBody.create
s4 = """        val body = okhttp3.RequestBody.create(
            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),
            jsonObj.toString()
        )"""
r4 = """        val body = jsonObj.toString().toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())"""
t = t.replace(s4, r4)

# And another cloud sync one? No, there might be two. Let's just replace both.
t = t.replace('            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),\n            jsonObj.toString()\n        )',
              '        val body = jsonObj.toString().toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())')
# Wait, let's look at the exact strings for lines 1090/1120. They say: `Too many arguments for 'fun String.toMediaTypeOrNull(): MediaType?'.`
# This means it might be `"application/json; charset=utf-8".toMediaTypeOrNull(something)`? No, it means:
s_cloud_error1 = 'okhttp3.RequestBody.create(\n            "application/json; charset=utf-8".toMediaTypeOrNull(),\n            jsonObj.toString()\n        )'
s_cloud_error2 = 'okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())'
# I'll just use regex safely, ONLY targeting my faulty okhttp3.RequestBody.create!
import re
t = re.sub(r'okhttp3\.RequestBody\.create\(\s*okhttp3\.MediaType\.parse\("([^"]+)"\),\s*([^)]+)\)',
           r'\2.toRequestBody("\1".toMediaTypeOrNull())',
           t)
t = re.sub(r'okhttp3\.RequestBody\.create\(\s*(?:okhttp3\.MediaType\.Companion\.)?toMediaTypeOrNull\("([^"]+)"\),\s*([^)]+)\)',
           r'\2.toRequestBody("\1".toMediaTypeOrNull())',
           t)
t = re.sub(r'okhttp3\.RequestBody\.create\(\s*"([^"]+)".toMediaTypeOrNull\(\),\s*([^)]+)\)',
           r'\2.toRequestBody("\1".toMediaTypeOrNull())',
           t)

# For the escape sequence \ in `patch_logs.py`
t = t.replace('"\\ ', '"')

codecs.open(p, 'w', 'utf-8').write(t)
print("Explicit okhttp fixes applied!")
