import sys
import re

path = r'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update signature of streamPcmToEsp32
text = text.replace('private fun streamPcmToEsp32(audioBytes: ByteArray) {', 'private fun streamPcmToEsp32(audioBytes: ByteArray, reqSessionId: Int) {')

# 2. Add interruption check in the streaming loop
old_loop_start = """                while (offset < audioBytes.size) {
                    var length = Math.min(chunkSize, audioBytes.size - offset)"""
new_loop_start = """                while (offset < audioBytes.size) {
                    if (reqSessionId != currentInterruptSessionId) {
                        android.util.Log.i("BLE_DEBUG", "Streaming interrupted by session ID.")
                        break
                    }
                    var length = Math.min(chunkSize, audioBytes.size - offset)"""
text = text.replace(old_loop_start, new_loop_start)

# 3. Update first caller (stopPttRecordingAndSend)
text = text.replace('streamPcmToEsp32(recordedBytes)', 'streamPcmToEsp32(recordedBytes, currentInterruptSessionId)')

# 4. Update second caller (playBase64Audio)
# streamPcmToEsp32(finalPcm)
text = text.replace('streamPcmToEsp32(finalPcm)', 'streamPcmToEsp32(finalPcm, reqSessionId)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Patched streamPcmToEsp32 successfully!")
