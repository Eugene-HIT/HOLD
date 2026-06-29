import re

xml_path = 'app/src/main/res/layout/activity_main.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'<LinearLayout\s*<!-- NEWLY ADDED UI FOR DETAIL -->'
text = re.sub(pattern, '<!-- NEWLY ADDED UI FOR DETAIL -->', text)

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Regex Fixed XML Syntax!")
