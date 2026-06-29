$file = 'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
$code = Get-Content $file -Raw -Encoding UTF8

# 1. Imports
$imports = "import java.util.UUID
import okhttp3.*
import okio.ByteString.Companion.toByteString
import com.google.gson.Gson
import com.google.gson.JsonObject
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit
import android.media.MediaPlayer
import java.io.File
import java.io.FileOutputStream
import android.util.Base64
import android.os.Handler
import android.os.Looper"
$code = $code.Replace('import java.util.UUID', $imports)

# 2. Members
$members = "    // AI Constants & Status
    private val ALIYUN_KEY = "sk-2dde2d428b5f4871bb90ad450ae4a515"
    private val ZHIPU_KEY = "6781c79d4db14ec2bb75853a91352491.opzn28MO3bY2dho1"
    
    private var isRecordingLocal = false
    private var isAIThinking = false
    private val audioBufferQueue = mutableListOf<ByteArray>()
    private var silenceHandler = Handler(Looper.getMainLooper())
    private var silenceRunnable: Runnable? = null
    
    private val okHttpClient = OkHttpClient.Builder()
        .readTimeout(60, TimeUnit.SECONDS)
        .build()
    private var aliyunWebSocket: WebSocket? = null
    
    private val historyLog = mutableListOf<Pair<String, String>>()
    private var mediaPlayer: MediaPlayer? = null

    // Stats"
$code = $code.Replace('    // Stats', $members)

# 3. Audio Handle Logic
$oldAudio = "                if (isPlayingAudio) {
                    // Buffer smoothing logic to prevent Android AudioTrack from starving / choking
                    audioBuffer.addAll(data.toList())
                    if (audioBuffer.size >= MIN_BUFFER_SIZE_THRESHOLD) {
                        val playbackArray = audioBuffer.toByteArray()
                        audioBuffer.clear()
                        // ESP32 sends 8-bit unsigned PCM. Convert to 16-bit signed PCM for Android.
                        val shortArray = ShortArray(playbackArray.size)
                        for (i in playbackArray.indices) {
                            val unsignedByte = playbackArray[i].toInt() and 0xFF
                            shortArray[i] = ((unsignedByte - 128) * 256).toShort()
                        }
                        audioTrack?.write(shortArray, 0, shortArray.size)
                    }
                }"

$newAudio = "                // 1. Send to Local Hardware Playback Loop
                if (isPlayingAudio && !isAIThinking) {
                    audioBuffer.addAll(data.toList())
                    if (audioBuffer.size >= MIN_BUFFER_SIZE_THRESHOLD) {
                        val playbackArray = audioBuffer.toByteArray()
                        audioBuffer.clear()
                        val shortArray = ShortArray(playbackArray.size)
                        for (i in playbackArray.indices) {
                            val unsignedByte = playbackArray[i].toInt() and 0xFF
                            shortArray[i] = ((unsignedByte - 128) * 256).toShort()
                        }
                        audioTrack?.write(shortArray, 0, shortArray.size)
                    }
                }

                // 2. Extracted VAD AI Logic mirroring WeChat Miniapp
                if (!isAIThinking) {
                    var maxEnergy = 0
                    for (b in data) {
                        val unsignedByte = b.toInt() and 0xFF
                        val energy = Math.abs(unsignedByte - 128)
                        if (energy > maxEnergy) maxEnergy = energy
                    }

                    if (maxEnergy > 8) { // LOWERED THRESHOLD TO INCREASE SENSITIVITY (from 15 to 8)
                        if (!isRecordingLocal) {
                            Log.i("AI_DEBUG", "VAD trigger start")
                            isRecordingLocal = true
                            runOnUiThread { tvAiStatus.text = " 正在录音... (安静1.5秒发送)" }
                        }
                        audioBufferQueue.add(data)
                        
                        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                        silenceRunnable = Runnable {
                            Log.i("AI_DEBUG", "VAD trigger silence end")
                            isRecordingLocal = false
                            isAIThinking = true
                            runOnUiThread { tvAiStatus.text = " 打包上传音频推给 STT 中..." }
                            processAndUploadAudio()
                        }
                        silenceHandler.postDelayed(silenceRunnable!!, 1500)
                    } else {
                        if (isRecordingLocal) {
                            audioBufferQueue.add(data)
                        }
                    }
                }"
$code = $code.Replace($oldAudio, $newAudio)

# 4. Methods appending
$methods = "

    private fun processAndUploadAudio() {
        if (audioBufferQueue.isEmpty()) {
            resetAI()
            return
        }

        var originalLength = 0
        for (chunk in audioBufferQueue) {
            originalLength += chunk.size
        }
        
        val dataLength = originalLength * 4 
        val bufferSize = 44 + dataLength
        val headerExtBuffer = ByteBuffer.allocate(bufferSize).order(ByteOrder.LITTLE_ENDIAN)

        headerExtBuffer.put("RIFF".toByteArray())
        headerExtBuffer.putInt(36 + dataLength)
        headerExtBuffer.put("WAVE".toByteArray())
        headerExtBuffer.put("fmt ".toByteArray())
        headerExtBuffer.putInt(16)
        headerExtBuffer.putShort(1)
        headerExtBuffer.putShort(1)
        headerExtBuffer.putInt(16000)
        headerExtBuffer.putInt(16000 * 1 * 2)
        headerExtBuffer.putShort(2)
        headerExtBuffer.putShort(16)
        headerExtBuffer.put("data".toByteArray())
        headerExtBuffer.putInt(dataLength)

        for (chunk in audioBufferQueue) {
            for (b in chunk) {
                val unsignedValue = b.toInt() and 0xFF
                val floatSample = (unsignedValue - 128) / 128.0f
                var int16Sample = (floatSample * 32767 * 1.6f).toInt()
                if (int16Sample > 32767) int16Sample = 32767
                if (int16Sample < -32768) int16Sample = -32768
                
                headerExtBuffer.putShort(int16Sample.toShort())
                headerExtBuffer.putShort(int16Sample.toShort())
            }
        }
        
        audioBufferQueue.clear()
        val finalWavBytes = headerExtBuffer.array()
        uploadToRealAI(finalWavBytes)
    }

    private fun uploadToRealAI(audioData: ByteArray) {
        val taskId = "task_" + System.currentTimeMillis() + (Math.random() * 1000).toInt()
        val request = Request.Builder()
            .url("wss://dashscope.aliyuncs.com/api-ws/v1/inference/")
            .addHeader("Authorization", "Bearer " + ALIYUN_KEY)
            .build()
            
        var finalStr = ""
        
        aliyunWebSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                val runTaskCmd = "{\"header\":{\"action\":\"run-task\",\"task_id\":\"" + taskId + "\",\"streaming\":\"duplex\"},\"payload\":{\"task_group\":\"audio\",\"task\":\"asr\",\"function\":\"recognition\",\"model\":\"paraformer-realtime-v1\",\"parameters\":{\"format\":\"wav\",\"sample_rate\":16000},\"input\":{}}}"
                webSocket.send(runTaskCmd)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val jsonObj = JSONObject(text)
                    val header = jsonObj.getJSONObject("header")
                    val event = header.getString("event")
                    
                    if (event == "task-started") {
                        webSocket.send(audioData.toByteString())
                        Thread.sleep(300)
                        webSocket.send("{\"header\":{\"action\":\"finish-task\",\"task_id\":\"" + taskId + "\",\"streaming\":\"duplex\"},\"payload\":{\"input\":{}}}")
                    } else if (event == "result-generated") {
                        val outObj = jsonObj.optJSONObject("payload")?.optJSONObject("output")?.optJSONObject("sentence")
                        if (outObj != null && outObj.has("text")) {
                            finalStr += outObj.getString("text")
                        }
                    } else if (event == "task-finished") {
                        val outObj = jsonObj.optJSONObject("payload")?.optJSONObject("output")?.optJSONObject("sentence")
                        if (outObj != null && outObj.has("text")) {
                            finalStr += outObj.getString("text")
                        }
                        webSocket.close(1000, "Done")
                        
                        if (finalStr.trim().isEmpty()) {
                            Log.e("AI_DEBUG", "STT Empty result")
                            runOnUiThread { tvAiStatus.text = " 没听清你说啥..." }
                            resetAI(500)
                            return
                        }
                        
                        Log.i("AI_DEBUG", "STT Success: " + finalStr)
                        runOnUiThread { tvUserVoice.text = "我: " + finalStr; tvAiStatus.text = " STT成功，呼叫智谱大脑..." }
                        callLLMForReply(finalStr)
                    } else if (event == "task-failed") {
                        Log.e("AI_DEBUG", "STT Task Fail: " + text)
                        runOnUiThread { tvAiStatus.text = " STT 识别失败" }
                        resetAI(1500)
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e("AI_DEBUG", "STT WebSocket failed: " + t.message)
                runOnUiThread { tvAiStatus.text = " STT 网络链路断开" }
                resetAI(1500)
            }
        })
    }

    private fun callLLMForReply(userText: String) {
        val sysContent = "你是专属的ADHD行动引导教练。如果我正在拖延，不要一味责骂，而是坚定且温和地引导我开启行动：先问我真正该做的是什么；如果我说了任务，请帮我拆解，并只规划出最微小、哪怕只做一分钟的绝对第一步（例如先坐到桌前或只打开文档）。每次回复控制在30字内，口语化，像推心置腹的朋友一样鼓励我迈出第一步。"
        
        val messagesArray = com.google.gson.JsonArray()
        val sysMsg = JsonObject().apply { addProperty("role", "system"); addProperty("content", sysContent) }
        messagesArray.add(sysMsg)
        
        for (round in historyLog) {
            val uMsg = JsonObject().apply { addProperty("role", "user"); addProperty("content", round.first) }
            val aMsg = JsonObject().apply { addProperty("role", "assistant"); addProperty("content", round.second) }
            messagesArray.add(uMsg)
            messagesArray.add(aMsg)
        }
        
        val curMsg = JsonObject().apply { addProperty("role", "user"); addProperty("content", userText) }
        messagesArray.add(curMsg)
        
        val reqBodyJson = JsonObject().apply {
            addProperty("model", "glm-4-flash")
            add("messages", messagesArray)
        }
        
        val body = RequestBody.create(MediaType.parse("application/json"), reqBodyJson.toString())
        val request = Request.Builder()
            .url("https://open.bigmodel.cn/api/paas/v4/chat/completions")
            .addHeader("Authorization", "Bearer " + ZHIPU_KEY)
            .post(body)
            .build()
            
        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e("AI_DEBUG", "LLM Network Error: " + e.message)
                runOnUiThread { tvAiStatus.text = " LLM 网络错误" }
                resetAI(1500)
            }

            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body()?.string() ?: ""
                try {
                    val jsonObj = JSONObject(respStr)
                    val choices = jsonObj.getJSONArray("choices")
                    val replyText = choices.getJSONObject(0).getJSONObject("message").getString("content")
                    
                    historyLog.add(Pair(userText, replyText))
                    if (historyLog.size > 10) historyLog.removeAt(0)
                    
                    Log.i("AI_DEBUG", "LLM Success: " + replyText)
                    runOnUiThread { tvAiReply.text = "AI: " + replyText; tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..." }
                    callTTSForAudio(replyText)
                } catch (e: Exception) {
                    Log.e("AI_DEBUG", "LLM parse failed: " + e.message + " json: " + respStr)
                    runOnUiThread { tvAiStatus.text = " LLM 解析失败" }
                    resetAI(1500)
                }
            }
        })
    }

    private fun callTTSForAudio(textToRead: String) {
        val ttsPrompt = "请用坚定、温柔且鼓励的知心大姐姐声音，全自动朗读下面这句话，不需要加任何自己的话，直接读：\n\n" + textToRead
        
        val messagesArray = com.google.gson.JsonArray()
        val uMsg = JsonObject().apply { addProperty("role", "user"); addProperty("content", ttsPrompt) }
        messagesArray.add(uMsg)
        
        val reqBodyJson = JsonObject().apply {
            addProperty("model", "glm-4-voice")
            add("messages", messagesArray)
        }
        
        val body = RequestBody.create(MediaType.parse("application/json"), reqBodyJson.toString())
        val request = Request.Builder()
            .url("https://open.bigmodel.cn/api/paas/v4/chat/completions")
            .addHeader("Authorization", "Bearer " + ZHIPU_KEY)
            .post(body)
            .build()
            
        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e("AI_DEBUG", "TTS Network Err: " + e.message)
                runOnUiThread { tvAiStatus.text = " TTS 网络通信错误" }
                resetAI(1500)
            }

            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body()?.string() ?: ""
                try {
                    val jsonObj = JSONObject(respStr)
                    val msgObj = jsonObj.getJSONArray("choices").getJSONObject(0).getJSONObject("message")
                    val audioData = msgObj.getJSONObject("audio").getString("data")
                    Log.i("AI_DEBUG", "TTS Success, ready to play")
                    runOnUiThread { tvAiStatus.text = " 正在外放 AI 语音... (期间耳朵屏蔽)" }
                    playBase64Audio(audioData)
                } catch (e: Exception) {
                    Log.e("AI_DEBUG", "TTS parse failed: " + e.message + " json: " + respStr)
                    runOnUiThread { tvAiStatus.text = " TTS 生成失败 (可能限流或报错)" }
                    resetAI(1500)
                }
            }
        })
    }

    private fun playBase64Audio(base64Str: String) {
        try {
            val audioBytes = Base64.decode(base64Str, Base64.DEFAULT)
            val tempFile = File(cacheDir, "ai_reply.wav")
            FileOutputStream(tempFile).use { it.write(audioBytes) }
            
            Handler(Looper.getMainLooper()).post {
                mediaPlayer?.release()
                mediaPlayer = MediaPlayer().apply {
                    setDataSource(tempFile.absolutePath)
                    prepare()
                    start()
                    setOnCompletionListener {
                        Log.i("AI_DEBUG", "Audio play complete. Resetting AI.")
                        resetAI(1000)
                    }
                }
            }
        } catch (e: Exception) {
            Log.e("AI_DEBUG", "Play Local Audio Exception: " + e.message)
            e.printStackTrace()
            resetAI(1000)
        }
    }

    private fun resetAI(delayMs: Long = 0) {
        Handler(Looper.getMainLooper()).postDelayed({
            isAIThinking = false
            isRecordingLocal = false
            audioBufferQueue.clear()
            tvAiStatus.text = " AI 闲置就绪，等待听你讲话..."
        }, delayMs)
    }
}
"
$code = $code.Replace('}', '') + $methods
Set-Content $file -Value $code -Encoding UTF8
"Out"
