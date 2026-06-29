import re

cpp_path = 'D:/ADHD/Xiao_Sense_MVP/src/main.cpp'
with open(cpp_path, 'r', encoding='utf-8') as f:
    cpp_code = f.read()

# Comment out the mute logic
old_logic = '''            if (millis() - last_play_time < 1200) {
                // Drop read data to avoid speaker echo (wait 1.2s after last playback chunk)
                samples_read = 0;
            }'''

new_logic = '''            // if (millis() - last_play_time < 1200) {
            //     // Drop read data to avoid speaker echo (wait 1.2s after last playback chunk)
            //     samples_read = 0;
            // }'''

if old_logic in cpp_code:
    cpp_code = cpp_code.replace(old_logic, new_logic)
    with open(cpp_path, 'w', encoding='utf-8') as f:
        f.write(cpp_code)
    print("PATCH APPLIED: ESP32 Duplex mode enabled")
else:
    print("LOGIC NOT FOUND OR ALREADY PATCHED")