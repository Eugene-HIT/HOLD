import re

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

target = r"""                            val extractedSteps = try \{
                                val arr = parsedJson.getAsJsonArray\("steps"\)    
                                val list = mutableListOf<String>\(\)
                                if \(arr != null\) \{
                                    for \(i in 0 until arr.size\(\)\) list.add\(arr.get\(i\).asString\)                                                                                                 \}
                                list
                            \} catch \(e: Exception\) \{
                                emptyList<String>\(\)
                            \}"""

# Fallback basic string replace if regex gets awkward
search_str = """                            val extractedSteps = try {
                                val arr = parsedJson.getAsJsonArray("steps")    
                                val list = mutableListOf<String>()
                                if (arr != null) {
                                    for (i in 0 until arr.size()) list.add(arr.get(i).asString)
                                }
                                list
                            } catch (e: Exception) {
                                emptyList<String>()
                            }"""

replacement = """                            val extractedSteps = try {
                                val arr = contentObj.optJSONArray("steps")
                                val list = mutableListOf<String>()
                                if (arr != null) {
                                    for (i in 0 until arr.length()) list.add(arr.getString(i))
                                }
                                list
                            } catch (e: Exception) {
                                emptyList<String>()
                            }"""

text = text.replace(search_str, replacement)

# sometimes formatting changes slightly, let's just do a manual index replace for 'parsedJson.getAsJsonArray("steps")' and 'arr.size()'
text = text.replace('parsedJson.getAsJsonArray("steps")', 'contentObj.optJSONArray("steps")')
text = text.replace('arr.size()', 'arr.length()')
text = text.replace('arr.get(i).asString', 'arr.getString(i)')

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fix applied!")
