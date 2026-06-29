import wave
import struct

def analyze(wav_file):
    with wave.open(wav_file, 'rb') as w:
        frames = w.readframes(w.getnframes())
        shorts = struct.unpack('<' + 'h' * (len(frames)//2), frames)
        max_val = max(shorts)
        min_val = min(shorts)
        avg_val = sum(abs(x) for x in shorts) / len(shorts)
        print(f"{wav_file}: max={max_val}, min={min_val}, avg={avg_val}")
        
    # count how many sequential zero-crossings or high-frequency jumps 
    # to measure "choppiness"/aliasing
    jumps = 0
    for i in range(1, len(shorts)):
        if abs(shorts[i] - shorts[i-1]) > 10000:
            jumps += 1
    print(f"{wav_file}: >10k jumps = {jumps}\n")

analyze('nn_test.wav')
analyze('li_test.wav')
