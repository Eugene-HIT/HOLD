import sys

with open('restore.txt', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('    data class HelpRequest')
idx2 = text.find('    override fun onCreate')
idx3 = text.find('        checkAndRequestPermissions()')
idx4 = text.find('    private fun reparentViews')

with open('extracted.txt', 'w', encoding='utf-8') as out:
    out.write("=== VARS ===\n" + text[idx1:idx2] + "\n\n")
    out.write("=== ONCREATE ===\n" + text[idx2:idx3] + "\n\n")
    out.write("=== METHODS ===\n" + text[idx4:] + "\n\n")
