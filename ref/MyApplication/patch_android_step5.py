kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_code = f.read()

kt_code = kt_code.replace('while (offset < audioBytes.size) {', 'while (offset < audioBytes.size) {\\n                      if (isInterrupted) break')
kt_code = kt_code.replace('writeSemaphore.release() // Allow the first chunk to proceed immediately', 'isInterrupted = false\\n                  writeSemaphore.release() // Allow the first chunk to proceed immediately')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_code)
print("Step 5 complete!")