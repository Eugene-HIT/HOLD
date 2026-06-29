import codecs
path = r'D:\ADHD\MyApplication\apply_pool_clean.py'
text = codecs.open(path, 'r', 'utf-8').read()
text = text.replace('"\分', '"\分')
text = text.replace(r'\n}', '\n}')
text = text.replace(r'\\n}', '\n}')
codecs.open(path, 'w', 'utf-8').write(text)
