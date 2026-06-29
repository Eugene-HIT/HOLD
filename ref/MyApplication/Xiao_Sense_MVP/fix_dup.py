import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

lines = t.split('\n')

# Find where 'private lateinit var tvUserTask: TextView' is, remove duplicates
var_start = -1
for i, line in enumerate(lines):
    if 'private lateinit var tvUserTask: TextView' in line:
        var_start = i
        break

if var_start != -1 and 'private lateinit var tvUserTask: TextView' in lines[var_start + 3]:
    del lines[var_start + 3 : var_start + 3 + 3]

# Do same for assignment
init_start = -1
for i, line in enumerate(lines):
    if 'tvUserTask = findViewById(R.id.tvUserTask)' in line:
        init_start = i
        break

if init_start != -1 and 'tvUserTask = findViewById(R.id.tvUserTask)' in lines[init_start + 3]:
    del lines[init_start + 3 : init_start + 3 + 3]

t = '\n'.join(lines)

# Fix Too many arguments for 'fun String.toMediaTypeOrNull(): MediaType?'
# Since we replaced the string with `toMediaTypeOrNull()`, `RequestBody.create` takes MediaType?, String
# Wait, no. `RequestBody.create()` for String is extension function in okhttp3 4.x:
# `jsonStr.toRequestBody("application/json".toMediaTypeOrNull())`
# Let's fix that.
t = t.replace('        val body = okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json"), reqBodyJson.toString())', 
              '        val body = okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())')

# The cloud sync okhttp also has a weird RequestBody.create
#  okhttp3.RequestBody.create(\n            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),\n            jsonObj.toString()\n        )
import re
t = re.sub(r'okhttp3\.RequestBody\.create\(\s*okhttp3\.MediaType\.Companion\.toMediaTypeOrNull\("application/json;\s*charset=utf-8"\),\s*jsonObj\.toString\(\)\s*\)',
           'okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())', t)

# Fix extension function deprecations: string.toRequestBody() is better but this works too if we fix args matching.
t = t.replace('okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())', 'okhttp3.RequestBody.create(jsonObj.toString(), "application/json; charset=utf-8".toMediaTypeOrNull())')
t = t.replace('okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())', 'okhttp3.RequestBody.create(reqBodyJson.toString(), "application/json".toMediaTypeOrNull())')


codecs.open(p, 'w', 'utf-8').write(t)
print("Dups and deprecated stuff cleaned!")
