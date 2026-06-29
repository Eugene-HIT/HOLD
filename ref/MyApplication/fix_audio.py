import re

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

target = r"""                  // 1. Send to Local Hardware Playback \(Native 16-bit PCM\)
                    if \(isPlayingAudio && !isAIThinking\) \{
                        try \{
                            playbackBuffer.write\(data\)"""

replacement = """                  // 1. Send to Local Hardware Playback (Native 16-bit PCM)
                    val shouldPlay = isPlayingAudio || isInHelpDetail
                    val blockPlay = isAIThinking && !isInHelpDetail
                    if (shouldPlay && !blockPlay) {
                        try {
                            if (audioTrack?.playState != android.media.AudioTrack.PLAYSTATE_PLAYING) {
                                try { audioTrack?.play() } catch (e: Exception) {}
                            }
                            playbackBuffer.write(data)"""

text = re.sub(target, replacement, text)

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Audio playback fix applied!")
