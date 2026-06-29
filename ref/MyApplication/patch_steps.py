import re

kt_path = 'app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update HelpRequest data class
old_hf = '''    data class HelpRequest(
        val userName: String,
        var userAction: String,
        var timestamp: Long = System.currentTimeMillis()
    )'''
new_hf = '''    data class HelpRequest(
        val userName: String,
        var userAction: String,
        var timestamp: Long = System.currentTimeMillis(),
        var steps: List<String> = emptyList()
    )'''
text = text.replace(old_hf, new_hf)

# 2. Update callLLMForReply where Anny is added
old_anny = '''                            val existingAnny = poolItems.find { it.userName == "Anny" }
                            if (existingAnny != null) {
                                existingAnny.userAction = "想要\，状态是\"
                                existingAnny.timestamp = System.currentTimeMillis()
                            } else {
                                poolItems.add(0, HelpRequest("Anny", "想要\，状态是\"))
                                if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                            }'''

new_anny = '''                            val extractedSteps = try {
                                val arr = parsedJson.getAsJsonArray("steps")
                                val list = mutableListOf<String>()
                                for (i in 0 until arr.size()) list.add(arr.get(i).asString)
                                list
                            } catch (e: Exception) {
                                emptyList<String>()
                            }

                            val existingAnny = poolItems.find { it.userName == "Anny" }
                            if (existingAnny != null) {
                                existingAnny.userAction = "想要\，状态是\"
                                existingAnny.timestamp = System.currentTimeMillis()
                                existingAnny.steps = extractedSteps
                            } else {
                                poolItems.add(0, HelpRequest("Anny", "想要\，状态是\", System.currentTimeMillis(), extractedSteps))
                                if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                            }'''
text = text.replace(old_anny, new_anny)

# 3. Update setupDetailTasks signature
old_setup = '''private fun setupDetailTasks(taskDesc: String) {
        completedTasks = 0
        congratsContainer.visibility = android.view.View.GONE
        taskListContainer.removeAllViews()
        tvDetailStt.text = "等待语音输入..."
        val sampleTasks = listOf("解析当前状态: " + taskDesc, "安抚鼓励用户", "完成微小动作(拍照打卡)")'''

new_setup = '''private fun setupDetailTasks(taskDesc: String, steps: List<String>) {
        completedTasks = 0
        congratsContainer.visibility = android.view.View.GONE
        taskListContainer.removeAllViews()
        tvDetailStt.text = "等待语音输入..."
        val sampleTasks = if (steps.isNotEmpty()) steps else listOf("解析当前状态: " + taskDesc, "安抚鼓励用户", "完成微小动作(拍照打卡)")'''
text = text.replace(old_setup, new_setup)

# 4. Update setupDetailTasks call
old_call = '''isInHelpDetail = true
                setupDetailTasks(item.userAction)'''
new_call = '''isInHelpDetail = true
                setupDetailTasks(item.userAction, item.steps)'''
text = text.replace(old_call, new_call)

# 5. Update audio playback condition
old_audio = '''// 1. Send to Local Hardware Playback (Native 16-bit PCM)
                  if (isPlayingAudio && !isAIThinking) {
                        try {
                            playbackBuffer.write(data)'''

new_audio = '''// 1. Send to Local Hardware Playback (Native 16-bit PCM)
                  val shouldPlay = isPlayingAudio || isInHelpDetail
                  val blockPlay = isAIThinking && !isInHelpDetail
                  if (shouldPlay && !blockPlay) {
                        try {
                            if (audioTrack?.playState != android.media.AudioTrack.PLAYSTATE_PLAYING) {
                                try { audioTrack?.play() } catch (e: Exception) {}
                            }
                            playbackBuffer.write(data)'''
text = text.replace(old_audio, new_audio)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied steps and playback fix!")
