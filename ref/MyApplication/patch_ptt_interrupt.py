import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

# Add to startPttRecording()
ptt = """    @SuppressLint("MissingPermission")
    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }
        
        isInterrupted = true
        isAIThinking = false
        isPlayingAudio = false
        try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
        try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
        runOnUiThread { tvAiStatus.text = "用户打断AI，录音中..." }
"""
if 'isInterrupted = true\n        isAIThinking = false' not in t.split('private fun startPttRecording()')[1][:500]:
    t = t.replace("""    @SuppressLint("MissingPermission")
    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }""", ptt)


# Add MediaPlayer reset to resetAI
if 'mediaPlayer?.stop()' not in t.split('private fun resetAI(')[1][:300]:
    t = t.replace('            playbackBuffer.reset()\n            audioTrack?.pause()', 
                  '            playbackBuffer.reset()\n            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}\n            audioTrack?.pause()')


# Add MediaPlayer reset to VAD logic
vad_interrupt = """                            android.util.Log.i("AI_DEBUG", "INTERRUPT TRIGGERED!")
                            isInterrupted = true
                            isPlayingAudio = false
                            isAIThinking = false
                            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
                            // WriteSemaphore removed
                            try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}"""

old_vad = """                            android.util.Log.i("AI_DEBUG", "INTERRUPT TRIGGERED!")
                            isInterrupted = true
                            isPlayingAudio = false
                            isAIThinking = false
                            // WriteSemaphore removed 
                            try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}"""
if 'mediaPlayer?.stop()' not in old_vad:
    t = t.replace(old_vad, vad_interrupt)

with codecs.open(p, 'w', 'utf-8') as f:
    f.write(t)

print("Full PTT and TTS Interruption Support patched!")
