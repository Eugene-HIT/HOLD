import re

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# find exact index
idx = text.find('// 1. Send to Local Hardware Playback')

if idx != -1:
    end_idx = text.find('playbackBuffer.write(data)', idx)
    if end_idx != -1:
        end_idx += len('playbackBuffer.write(data)')
        chunk = text[idx:end_idx]
        print("Found:", repr(chunk))
        
        replacement = """// 1. Send to Local Hardware Playback (Native 16-bit PCM)
                    val shouldPlay = isPlayingAudio || isInHelpDetail
                    val blockPlay = isAIThinking && !isInHelpDetail
                    if (shouldPlay && !blockPlay) {
                        try {
                            if (audioTrack?.playState != android.media.AudioTrack.PLAYSTATE_PLAYING) {
                                try { audioTrack?.play() } catch (e: Exception) {}
                            }
                            playbackBuffer.write(data)"""
        text = text[:idx] + replacement + text[end_idx:]
        with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Replaced successfully!")
