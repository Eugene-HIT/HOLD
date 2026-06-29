import codecs
path = r'D:\ADHD\MyApplication\apply_pool_clean.py'
text = codecs.open(path, 'r', 'utf-8').read()
text = text.replace("text[:idx] + render_code + '\n  }'", "text[:idx] + render_code + '\\n}'")
codecs.open(path, 'w', 'utf-8').write(text)
