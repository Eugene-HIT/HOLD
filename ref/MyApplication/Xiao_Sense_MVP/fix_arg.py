import codecs
import re

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

# I reverted it locally yesterday and did RequestBody.create by just doing:
t = t.replace('okhttp3.RequestBody.create(reqBodyJson.toString(), "application/json".toMediaTypeOrNull())',
              'okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())')

t = t.replace('okhttp3.RequestBody.create(jsonObj.toString(), "application/json; charset=utf-8".toMediaTypeOrNull())',
              'okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())')

# Also the media parse issue from earlier was "Too many arguments to String.toMediaTypeOrNull()". 
# The issue was actually: okhttp3.MediaType.Companion.toMediaTypeOrNull("...") 
# Let's import toRequestBody at the top if we need it, but let's just use:
t = t.replace('okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())',
              'okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json; charset=utf-8"), jsonObj.toString())')

t = t.replace('okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())',
              'okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json"), reqBodyJson.toString())')

codecs.open(p, 'w', 'utf-8').write(t)
print("Rollback arguments and use MediaType.parse")