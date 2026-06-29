import codecs
import re
path = r'D:\ADHD\MyApplication\apply_pool_clean.py'
text = codecs.open(path, 'r', 'utf-8').read()
text = re.sub(r'\\+\'', r"'", text) # clean up
text = re.sub(r"text = text\[:idx\] \+ render_code \+ '.*", "text = text[:idx] + render_code + r'\\n}'", text, flags=re.DOTALL)
codecs.open(path, 'w', 'utf-8').write(text)
