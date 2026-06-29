import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
t = codecs.open(p, 'r', 'utf-8').read()

# 1. Fix Duplicates
dup_decl = """    private lateinit var tvUserTask: TextView\n    private lateinit var tvUserState: TextView\n    private lateinit var tvActionSteps: TextView"""
if t.count(dup_decl) > 1:
    t = t.replace(dup_decl, "", 1)

dup_init = """        tvUserTask = findViewById(R.id.tvUserTask)\n        tvUserState = findViewById(R.id.tvUserState)\n        tvActionSteps = findViewById(R.id.tvActionSteps)"""
if t.count(dup_init) > 1:
    t = t.replace(dup_init, "", 1)

# 2. Fix MediaType create
t = t.replace('okhttp3.MediaType.parse("application/json")', '"application/json".toMediaTypeOrNull()')

# 3. Fix okhttp3.RequestBody.create argument order issue (extension function used wrong)
t = t.replace('okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json; charset=utf-8"), jsonObj.toString())', 'okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())')
t = t.replace('okhttp3.RequestBody.create(okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),\n            jsonObj.toString()\n        )', 'okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())')
t = t.replace('            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),\n            jsonObj.toString()\n        )', 'okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())')

# 4. Fix Logging Escape Sequences \ 
t = t.replace('"\\ ', '"')

# 5. Fix response.body()
t = t.replace('response.body()?.string()', 'response.body?.string()')

codecs.open(p, 'w', 'utf-8').write(t)
print("Code Cleaned!")
