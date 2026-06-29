import os
import re

# 1. FIX ESP32
cpp_path = r'D:\ADHD\Xiao_Sense_MVP\src\main.cpp'
with open(cpp_path, 'r', encoding='utf-8') as f:
    cpp_code = f.read()

cpp_code = cpp_code.replace("size_t chunk_size = 120; // 瓒呯ǔ濡ョ殑 120 瀛楄妭鍒囩墖", "size_t chunk_size = 244; // 更大更保险")
cpp_code = cpp_code.replace("size_t chunk_size = 120;", "size_t chunk_size = 244;")
cpp_code = cpp_code.replace("delay(30);", "delay(40);")
cpp_code = cpp_code.replace("放慢发包速度 30ms", "放慢发包速度 40ms")

with open(cpp_path, 'w', encoding='utf-8') as f:
    f.write(cpp_code)
print('ESP32 fixed.')
