const fs = require('fs');

// 1. Update activity_main.xml
let xml = fs.readFileSync('D:/ADHD/MyApplication/app/src/main/res/layout/activity_main.xml', 'utf-8');

const newUIBlock = 
    <!-- AI Debug Status Panel -->
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:background="#E3F2FD"
        android:padding="8dp"
        android:layout_marginTop="12dp">
        
        <TextView
            android:id="@+id/tvAiStatus"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="AI 状态: 就绪，等待说话..."
            android:textSize="16sp"
            android:textStyle="bold"
            android:textColor="#0D47A1" />

        <TextView
            android:id="@+id/tvUserVoice"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="我: -"
            android:textSize="14sp"
            android:textColor="#1B5E20"
            android:layout_marginTop="4dp"/>

        <TextView
            android:id="@+id/tvAiReply"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="AI: -"
            android:textSize="14sp"
            android:textColor="#B71C1C"
            android:layout_marginTop="4dp"/>
    </LinearLayout>

    <ScrollView
;
if(!xml.includes('tvAiStatus')) {
    xml = xml.replace('<ScrollView\n', newUIBlock);
    fs.writeFileSync('D:/ADHD/MyApplication/app/src/main/res/layout/activity_main.xml', xml, 'utf-8');
}

// 2. Update MainActivity.kt
let ktCode = fs.readFileSync('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'utf-8');

if (!ktCode.includes('tvAiStatus')) {
    // Add members
    ktCode = ktCode.replace('private lateinit var tbPlayAudio: ToggleButton', 
      'private lateinit var tbPlayAudio: ToggleButton\\n' +
      '    private lateinit var tvAiStatus: TextView\\n' +
      '    private lateinit var tvUserVoice: TextView\\n' +
      '    private lateinit var tvAiReply: TextView\\n'
    );

    // Init members
    ktCode = ktCode.replace('tbPlayAudio = findViewById(R.id.tbPlayAudio)',
      'tbPlayAudio = findViewById(R.id.tbPlayAudio)\\n' +
      '        tvAiStatus = findViewById(R.id.tvAiStatus)\\n' +
      '        tvUserVoice = findViewById(R.id.tvUserVoice)\\n' +
      '        tvAiReply = findViewById(R.id.tvAiReply)\\n'
    );

    // Modify UI Updates
    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = " 正在录音... (说完请安静1.5秒)" }', 
      'runOnUiThread { tvAiStatus.text = " 正在录音... (说完请安静1.5秒)" }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = " 打包上传 AI 翻译中..." }', 
      'runOnUiThread { tvAiStatus.text = " 打包上传 STT 翻译中..." }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "没听清你说啥..." }', 
      'Log.e("AI_DEBUG", "STT Result Empty"); runOnUiThread { tvAiStatus.text = " 没听清你说啥..." }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "STT完成: \\n正在呼叫智谱大模型..." }', 
      'Log.i("AI_DEBUG", "STT Success: " + finalStr); runOnUiThread { tvUserVoice.text = "我: " + finalStr; tvAiStatus.text = " STT完成，呼叫智谱..." }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "STT 识别失败" }', 
      'Log.e("AI_DEBUG", "STT Error Event"); runOnUiThread { tvAiStatus.text = " STT 识别失败 / 被终止" }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "STT 网络错误" }', 
      'Log.e("AI_DEBUG", "STT WebSocket Auth/Failure: " + t?.message); runOnUiThread { tvAiStatus.text = " STT 网网络错误: " + t?.message }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "LLM 网络错误" }', 
      'Log.e("AI_DEBUG", "LLM Network Error: " + e.message); runOnUiThread { tvAiStatus.text = " LLM 网络错误" }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "AI回复: \\n正在生成语音..." }', 
      'Log.i("AI_DEBUG", "LLM Reply: " + replyText); runOnUiThread { tvAiReply.text = "AI: " + replyText; tvAiStatus.text = " 正在生成语音(TTS)..." }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "LLM 解析失败" }', 
      'Log.e("AI_DEBUG", "LLM Parse Error: " + e.message); runOnUiThread { tvAiStatus.text = " LLM 结果解析崩溃" }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "TTS 网络错误" }', 
      'Log.e("AI_DEBUG", "TTS Network Error: " + e.message); runOnUiThread { tvAiStatus.text = " TTS 网络错误" }');

    ktCode = ktCode.replace('runOnUiThread { tvStatus.text = "TTS 生成失败" }', 
      'Log.e("AI_DEBUG", "TTS Parse Error: " + e.message + "\\nJSON: " + respStr); runOnUiThread { tvAiStatus.text = " TTS 生成失败 (可能没额度或限制)" }');

    ktCode = ktCode.replace('playBase64Audio(audioData)', 
      'Log.i("AI_DEBUG", "TTS Success, Playing Audio..."); runOnUiThread { tvAiStatus.text = " 正在播放 AI 姐姐语音..." }; playBase64Audio(audioData)');

    ktCode = ktCode.replace('tvStatus.text = "就绪，等待语音..."', 
      'tvAiStatus.text = " AI 闲置中，等待听你讲话..."\\n            tvUserVoice.text = "我: -"\\n            tvAiReply.text = "AI: -"');

    fs.writeFileSync('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', ktCode, 'utf-8');
}
console.log("UI Update Complete.");
