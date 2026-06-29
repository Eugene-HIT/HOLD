import sys

with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

if 'private var currentTurnId = 0L' not in text:
    text = text.replace('private var resetAIRunnable: Runnable? = null', 'private var resetAIRunnable: Runnable? = null\n    private var currentTurnId = 0L')

old_reset = '''    private fun resetAI(delayMs: Long = 0) {
        resetAIRunnable?.let { resetAIHandler.removeCallbacks(it) }
        resetAIRunnable = Runnable {
            if (isRecordingLocal) return@Runnable 
            isAIThinking = false'''

new_reset = '''    private fun resetAI(delayMs: Long = 0) {
        val capturedTurnId = currentTurnId
        resetAIRunnable?.let { resetAIHandler.removeCallbacks(it) }
        resetAIRunnable = Runnable {
            if (capturedTurnId != currentTurnId) return@Runnable
            if (isRecordingLocal) return@Runnable 
            isAIThinking = false'''

text = text.replace(old_reset, new_reset)

old_0x02 = '''                    if (data[0].toInt() == 0x02) {
                        android.util.Log.i("AI_DEBUG", "HARDWARE LONG PRESS INTERRUPT")
                        isInterrupted = true
                        isAIThinking = false'''

new_0x02 = '''                    if (data[0].toInt() == 0x02) {
                        ++currentTurnId
                        android.util.Log.i("AI_DEBUG", "HARDWARE LONG PRESS INTERRUPT")
                        isInterrupted = true
                        isAIThinking = false'''

text = text.replace(old_0x02, new_0x02)

with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print('Patched successfully!')

text = text.replace('try { mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}', 'try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}')
text = text.replace('if (data[0].toInt() == 0x04) {', 'if (data[0].toInt() == 0x04) {\n                        ++currentTurnId')
with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f2:
    f2.write(text)
