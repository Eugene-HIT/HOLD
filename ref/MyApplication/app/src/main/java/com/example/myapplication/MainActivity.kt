package com.example.myapplication

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.media.AudioRecord
import java.io.ByteArrayOutputStream
import android.view.MotionEvent
import android.view.GestureDetector
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.SeekBar
import android.widget.ToggleButton
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.ContextCompat.startForegroundService
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okio.ByteString.Companion.toByteString
import com.google.gson.JsonObject
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit
import android.media.MediaPlayer
import java.io.File
import java.io.FileOutputStream
import android.os.Handler
import android.os.Looper

class MainActivity : AppCompatActivity() {
    private data class ParsedAssistantReply(
        val reply: String?,
        val userTask: String?,
        val userState: String?,
        val steps: List<String>
    )

    private data class SupervisorStepPreview(
        val title: String,
        val prompter: String
    )

    private data class SupervisorPreview(
        val mainGoal: String,
        val userState: String,
        val interventionNeed: String,
        val steps: List<SupervisorStepPreview>,
        val sourceHint: String,
        val currentStepLabel: String? = null,
        val supervisorAdvice: String? = null
    )

    private data class SupervisorTaskItem(
        val order: Int,
        val title: String,
        val detail: String,
        val done: Boolean
    )

    private data class SupervisorTaskBreakdown(
        val mode: String?,
        val goal: String?,
        val steps: List<SupervisorTaskItem>
    )

    private data class SupervisorProgressReview(
        val currentStepOrder: Int?,
        val currentStepTitle: String?,
        val userState: String?,
        val advice: String?,
        val interventionNeed: String?
    )

    private fun InterruptAgent() {
        runOnUiThread {
            tvStatus.text = "检测到硬件中断 (0x02)"
            tvAiStatus.text = "硬件触发，正在录音中..."
            try {
                audioTrack?.pause()
                audioTrack?.flush()
            } catch(e: Exception){}
        }
        isAIThinking = false
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
    }

    private var currentInterruptSessionId = 0
    var hardwareVolumeMultiplier = 1.0f

    private lateinit var tvStatus: TextView
    private lateinit var btnScan: Button
    private lateinit var llDeviceList: LinearLayout
    private lateinit var tvImuData: TextView
    private lateinit var tvAudioData: TextView
    private lateinit var tbPlayAudio: ToggleButton

    // AI Views
    private lateinit var tvAiStatus: TextView
    private lateinit var tvUserVoice: TextView
    private lateinit var tvAiReply: TextView
    private lateinit var ivCamera: android.widget.ImageView
    private lateinit var tabPool: android.widget.Button
    private lateinit var tabDebug: android.widget.Button
    private lateinit var poolView: android.view.View
    private lateinit var debugScroll: android.view.View
    private lateinit var helpDetailView: android.view.View
    private lateinit var btnBackToPool: android.widget.Button

    // Task and Pool UI
    private lateinit var tvDetailTask: android.widget.TextView
    private lateinit var tvDetailStt: android.widget.TextView
    private lateinit var taskListContainer: android.widget.LinearLayout
    private lateinit var poolListLayout: android.widget.LinearLayout
    private lateinit var congratsContainer: android.widget.LinearLayout
    private lateinit var tvUserTask: TextView
    private lateinit var tvUserState: TextView
    private lateinit var tvActionSteps: TextView
    private lateinit var tvSupervisorMainGoal: TextView
    private lateinit var tvSupervisorUserState: TextView
    private lateinit var tvSupervisorIntervention: TextView
    private lateinit var tvSupervisorPlan: TextView

    data class HelpRequest(val userName: String, var userAction: String, var timestamp: Long, var steps: List<String> = emptyList())
    private val poolItems = mutableListOf<HelpRequest>()

    // Camera Image Buffer
    private val imageBuffer = java.io.ByteArrayOutputStream()
    private var isScanning = false
    private var bluetoothAdapter: BluetoothAdapter? = null
    private var bluetoothGatt: BluetoothGatt? = null
    private var lastConnectedDeviceAddress: String? = null
    private val foundDevices = mutableListOf<BluetoothDevice>()
    private val reconnectHandler = Handler(Looper.getMainLooper())
    private var reconnectRunnable: Runnable? = null
    private val scanTimeoutHandler = Handler(Looper.getMainLooper())
    private var scanTimeoutRunnable: Runnable? = null

    // Bluetooth Service & Characteristics
    private val SERVICE_UUID = UUID.fromString("19B10000-E8F2-537E-4F6C-D104768A1214")
    private val IMU_CHAR_UUID = UUID.fromString("19B10001-E8F2-537E-4F6C-D104768A1214")
    private val MIC_AUDIO_CHAR_UUID = UUID.fromString("19B10002-E8F2-537E-4F6C-D104768A1214")
    private val SPK_AUDIO_CHAR_UUID = UUID.fromString("19B10003-E8F2-537E-4F6C-D104768A1214")
    private val CAM_IMAGE_CHAR_UUID = UUID.fromString("19B10004-E8F2-537E-4F6C-D104768A1214")
    private val CMD_CHAR_UUID = UUID.fromString("19B10005-E8F2-537E-4F6C-D104768A1214")
    private val CCCD_UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

    // AI Constants & Status
    private val ALIYUN_KEY = "sk-2dde2d428b5f4871bb90ad450ae4a515"
    private val KIMI_KEY = "sk-UbBC4stpTma7yTY89hPbjPTDfbsEt5VRaLy3H0W8JCYo4l8U"
    private val KIMI_MODEL = "moonshot-v1-8k"
    private val ZHIPU_KEY = "6781c79d4db14ec2bb75853a91352491.opzn28MO3bY2dho1"
    private val VOLCENGINE_TTS_APP_ID = "2278522339"
    private val VOLCENGINE_TTS_ACCESS_TOKEN = "Q-wccpgWtPazM9Lq47CA0DMZ2TgK0gLA"
    private val VOLCENGINE_TTS_RESOURCE_ID = "seed-tts-2.0"
    private val VOLCENGINE_TTS_SPEAKER = "zh_female_xiaohe_uranus_bigtts"

    // 全局云端地址
    private val cloudMediaUrl = "https://cloud1-2g65h7na8576f841-1418292974.ap-shanghai.app.tcloudbase.com/update"

    private var isRecordingLocal = false
    private var isAIThinking = false
    private var hasGreeted = false

    private var isHumanIntervened = false
    private var isAppInForeground = true
    private val mutePhoneSpeakerWhenAppBackgrounded = true

    private var commandPollHandler = Handler(Looper.getMainLooper())

    private var commandPollRunnable: Runnable? = null
    private val audioBufferQueue = java.util.concurrent.CopyOnWriteArrayList<ByteArray>()
    private var silenceHandler = Handler(Looper.getMainLooper())
    private var silenceRunnable: Runnable? = null
    private var resetAIHandler = Handler(Looper.getMainLooper())
    private var resetAIRunnable: Runnable? = null
    private var currentTurnId = 0L

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS) // 🌟 增加连接耐心
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()
    private var aliyunWebSocket: WebSocket? = null
    private val historyLog = mutableListOf<Pair<String, String>>()
    private val maxHistoryRounds = 50
    private var lastKnownTask = "未知"
    private var lastKnownState = "未知"
    private var lastKnownStepsText = "暂无步骤"
    private val lastKnownStepsList = mutableListOf<String>()
    private var lockedSupervisorPlan: SupervisorTaskBreakdown? = null
    private var lockedSupervisorState = "未知"
    private var lastSupervisorProgress: SupervisorProgressReview? = null
    private var mediaPlayer: MediaPlayer? = null

    // Stats
    private var totalAudioBytes = 0L
    private var lastUiUpdateTime = 0L

    // Audio Player
    @Volatile private var isInterrupted = false
    private var interruptFrames = 0 // 🌟 新增：用于边听边打断的状态器

    private var audioTrack: AudioTrack? = null
    private var isPlayingAudio = false
    private var pttAudioRecord: AudioRecord? = null
    private var isRecordingPtt = false
    private var isHardwarePtt = false
    private var isSimulatedHardwarePttActive = false
    private var isSimulatedHardwareMode = false
    private val pttAudioBuffer = ByteArrayOutputStream()

    private val playbackBuffer = java.io.ByteArrayOutputStream()
    private val audioExecutor = java.util.concurrent.ThreadPoolExecutor(
        1, 1, 0L, java.util.concurrent.TimeUnit.MILLISECONDS,
        java.util.concurrent.LinkedBlockingQueue<Runnable>()
    )
    private val MIN_BUFFER_SIZE_THRESHOLD = 3200
    private val reconnectDelayMs = 2000L
    private val scanTimeoutMs = 12000L

    companion object {
        private const val BLE_PREFS = "ble_connection_prefs"
        private const val LAST_DEVICE_ADDRESS_KEY = "last_device_address"
    }

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.entries.all { it.value }
        if (allGranted) {
            tvStatus.text = "权限已授予，准备就绪"
        } else {
            tvStatus.text = "没有蓝牙权限"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        startAppKeepAliveService()

        tvStatus = findViewById(R.id.tvStatus)
        btnScan = findViewById(R.id.btnScan)
        val btnPushToTalk: Button = findViewById(R.id.btnPushToTalk)
        val btnSimulateHardware: Button = findViewById(R.id.btnSimulateHardware)
        btnPushToTalk.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    btnPushToTalk.text = "录音中..."
                    startPttRecording()
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    btnPushToTalk.text = "按住录音，松开发送"
                    stopPttRecordingAndSend()
                    true
                }
                else -> false
            }
        }

        val simulateHardwareGestureDetector = GestureDetector(this, object : GestureDetector.SimpleOnGestureListener() {
            override fun onDown(e: MotionEvent): Boolean = true

            override fun onLongPress(e: MotionEvent) {
                if (!isSimulatedHardwarePttActive) {
                    enableSimulatedHardwareModeIfNeeded()
                    isSimulatedHardwarePttActive = true
                    btnSimulateHardware.text = "模拟硬件：讲话中，松开发送"
                    runOnUiThread {
                        tvAiStatus.text = "🎙️ 模拟硬件长按讲话中..."
                    }
                    startPttRecording()
                }
            }

            override fun onSingleTapConfirmed(e: MotionEvent): Boolean {
                btnSimulateHardware.text = "模拟硬件：长按讲话 / 单击拍照 / 双击结束"
                if (lastKnownStepsList.isNotEmpty()) {
                    handlePhotoProgressUpdate()
                } else {
                    runOnUiThread {
                        tvAiStatus.text = "📷 暂无进行中的步骤，先让 AI 建立任务后再模拟拍照。"
                    }
                }
                return true
            }

            override fun onDoubleTap(e: MotionEvent): Boolean {
                btnSimulateHardware.text = "模拟硬件：长按讲话 / 单击拍照 / 双击结束"
                handleTaskCompletedByHardware()
                return true
            }
        })

        btnSimulateHardware.setOnTouchListener { _, event ->
            simulateHardwareGestureDetector.onTouchEvent(event)
            if ((event.action == MotionEvent.ACTION_UP || event.action == MotionEvent.ACTION_CANCEL) && isSimulatedHardwarePttActive) {
                isSimulatedHardwarePttActive = false
                btnSimulateHardware.text = "模拟硬件：长按讲话 / 单击拍照 / 双击结束"
                stopSimulatedHardwarePttRecordingAndSendToAi()
                true
            } else {
                true
            }
        }

        llDeviceList = findViewById(R.id.llDeviceList)
        tvImuData = findViewById(R.id.tvImuData)
        tvAudioData = findViewById(R.id.tvAudioData)
        tbPlayAudio = findViewById(R.id.tbPlayAudio)

        tvAiStatus = findViewById(R.id.tvAiStatus)
        tvUserVoice = findViewById(R.id.tvUserVoice)
        tvAiReply = findViewById(R.id.tvAiReply)
        ivCamera = findViewById(R.id.ivCamera)

        tabPool = findViewById(R.id.tab_pool)
        tabDebug = findViewById(R.id.tab_debug)
        poolView = findViewById(R.id.pool_view)
        debugScroll = findViewById(R.id.debug_scroll)
        helpDetailView = findViewById(R.id.help_detail_view)
        btnBackToPool = findViewById(R.id.btn_back_to_pool)
        tvDetailTask = findViewById(R.id.tv_detail_task)
        tvDetailStt = findViewById(R.id.tv_detail_stt)
        taskListContainer = findViewById(R.id.task_list_container)
        congratsContainer = findViewById(R.id.congrats_container)
        poolListLayout = findViewById(R.id.poolListLayout)

        tvUserTask = findViewById(R.id.tvUserTask)
        tvUserState = findViewById(R.id.tvUserState)
        tvActionSteps = findViewById(R.id.tvActionSteps)
        tvSupervisorMainGoal = findViewById(R.id.tvSupervisorMainGoal)
        tvSupervisorUserState = findViewById(R.id.tvSupervisorUserState)
        tvSupervisorIntervention = findViewById(R.id.tvSupervisorIntervention)
        tvSupervisorPlan = findViewById(R.id.tvSupervisorPlan)
        renderSupervisorPreview(buildLocalSupervisorPreview(lastKnownTask, lastKnownState, emptyList()))

        tabPool.setOnClickListener {
            poolView.visibility = android.view.View.VISIBLE
            debugScroll.visibility = android.view.View.GONE
            helpDetailView.visibility = android.view.View.GONE
            tabPool.setBackgroundColor(ContextCompat.getColor(this, android.R.color.darker_gray))
            tabDebug.setBackgroundColor(ContextCompat.getColor(this, android.R.color.transparent))
        }

        tabDebug.setOnClickListener {
            poolView.visibility = android.view.View.GONE
            debugScroll.visibility = android.view.View.VISIBLE
            helpDetailView.visibility = android.view.View.GONE
            tabDebug.setBackgroundColor(ContextCompat.getColor(this, android.R.color.darker_gray))
            tabPool.setBackgroundColor(ContextCompat.getColor(this, android.R.color.transparent))
        }

        btnBackToPool.setOnClickListener {
            helpDetailView.visibility = android.view.View.GONE
            poolView.visibility = android.view.View.VISIBLE
            debugScroll.visibility = android.view.View.GONE
        }

        tabPool.performClick()
        requestBlePermissions()
        initAudioTrack()

        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = bluetoothManager.adapter
        lastConnectedDeviceAddress = loadLastConnectedDeviceAddress()

        val seekBarVolume = findViewById<SeekBar>(R.id.seekBarVolume)
        val tvVolumeVal = findViewById<TextView>(R.id.tvVolumeVal)
        seekBarVolume.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                var scaled = progress / 10.0f
                if (scaled < 0.1f) scaled = 0.1f
                hardwareVolumeMultiplier = scaled
                tvVolumeVal.text = String.format("%.1fx", hardwareVolumeMultiplier)
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })

        Handler(Looper.getMainLooper()).postDelayed({ attemptAutoConnectOrScan("应用启动") }, 1000)

        btnScan.setOnClickListener {
            if (!isScanning) {
                disableSimulatedHardwareMode("手动扫描真实硬件")
                startScan()
            } else {
                stopScan()
            }
        }

        tbPlayAudio.setOnCheckedChangeListener { _, isChecked ->
            isPlayingAudio = isChecked
            if (isChecked) {
                playbackBuffer.reset()
                if (audioTrack?.playState != AudioTrack.PLAYSTATE_PLAYING) {
                    audioTrack?.play()
                }
            } else {
                audioTrack?.pause()
                audioTrack?.flush()
            }
        }

        val etStatusInput = findViewById<EditText>(R.id.et_status_input)
        val btnSend = findViewById<Button>(R.id.btn_send_to_cloud)

        btnSend?.setOnClickListener {
            val statusText = etStatusInput?.text?.toString() ?: ""
            if (statusText.isEmpty()) {
                Toast.makeText(this@MainActivity, "先写点状态再发嘛！", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val jsonObj = JSONObject()
            jsonObj.put("status", statusText)
            jsonObj.put("device_id", "Gulu_Android_001")
            jsonObj.put("heart_rate", 75)

            val body = okhttp3.RequestBody.create(
                "application/json; charset=utf-8".toMediaTypeOrNull(),
                jsonObj.toString()
            )
            val request = Request.Builder().url(cloudMediaUrl).post(body).build()

            okHttpClient.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    Log.e("Gulu_Network", "发送失败: ${e.message}")
                    runOnUiThread {
                        Toast.makeText(this@MainActivity, "发送失败，看Logcat！", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onResponse(call: Call, response: Response) {
                    runOnUiThread {
                        Toast.makeText(this@MainActivity, "✅ 发送成功！快看小程序", Toast.LENGTH_SHORT).show()
                        etStatusInput?.text?.clear()
                    }
                }
            })
        }
        startCommandPolling()
    }

    private fun initAudioTrack() {
        val sampleRate = 16000
        val channelConfig = AudioFormat.CHANNEL_OUT_MONO
        val audioFormat = AudioFormat.ENCODING_PCM_16BIT
        val bufferSize = AudioTrack.getMinBufferSize(sampleRate, channelConfig, audioFormat)

        audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(audioFormat)
                    .setSampleRate(sampleRate)
                    .setChannelMask(channelConfig)
                    .build()
            )
            .setBufferSizeInBytes(bufferSize)
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
    }

    override fun onDestroy() {
        super.onDestroy()
        cancelReconnectLoop()
        cancelScanTimeout()
        stopScan()
        audioTrack?.release()
        audioTrack = null
        @SuppressLint("MissingPermission")
        bluetoothGatt?.close()
    }

    private fun requestBlePermissions() {
        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.RECORD_AUDIO
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions.add(Manifest.permission.BLUETOOTH_SCAN)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            permissions.add(Manifest.permission.BLUETOOTH)
            permissions.add(Manifest.permission.BLUETOOTH_ADMIN)
        }

        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isNotEmpty()) {
            requestPermissionLauncher.launch(missingPermissions.toTypedArray())
        }
    }

    private fun resetConversationContext() {
        historyLog.clear()
        lastKnownTask = "未知"
        lastKnownState = "未知"
        lastKnownStepsText = "暂无步骤"
        lastKnownStepsList.clear()
        lockedSupervisorPlan = null
        lockedSupervisorState = "未知"
        lastSupervisorProgress = null

        runOnUiThread {
            tvUserTask.text = "🎯 目标任务：未知"
            tvUserState.text = "💡 当前状态：未知"
            tvActionSteps.text = "🪜 拆解步骤：\n暂无步骤"
            renderSupervisorPreview(buildLocalSupervisorPreview(lastKnownTask, lastKnownState, emptyList()))
            tvUserVoice.text = ""
            tvAiReply.text = ""
        }
    }

    private fun buildLocalSupervisorPreview(mainGoal: String, userState: String, steps: List<String>): SupervisorPreview {
        val normalizedGoal = mainGoal.trim().ifEmpty { "未知" }
        val normalizedState = userState.trim().ifEmpty { "未知" }
        val previewSteps = buildSupervisorFallbackSeries(normalizedGoal, normalizedState, steps)
        val interventionNeed = when {
            normalizedGoal == "未知" || normalizedState == "未知" -> "低"
            steps.size >= 4 -> "中"
            steps.size >= 2 -> "低"
            else -> "极低"
        }
        return SupervisorPreview(
            mainGoal = normalizedGoal,
            userState = normalizedState,
            interventionNeed = interventionNeed,
            steps = previewSteps,
            sourceHint = "本地占位",
            currentStepLabel = if (previewSteps.isEmpty()) null else "当前推进：待锁定监督计划"
        )
    }

    private fun shouldLockSupervisorPlan(mainGoal: String, userState: String): Boolean {
        return mainGoal.isNotBlank() && mainGoal != "未知" && userState.isNotBlank() && userState != "未知"
    }

    private fun buildSupervisorFallbackSeries(mainGoal: String, userState: String, steps: List<String>): List<SupervisorStepPreview> {
        val normalizedGoal = mainGoal.trim().ifEmpty { "未知" }
        val normalizedState = userState.trim().ifEmpty { "未知" }
        val fallbackSteps = mutableListOf<SupervisorStepPreview>()

        fun appendStep(title: String, prompter: String) {
            if (fallbackSteps.none { it.title == title }) {
                fallbackSteps.add(SupervisorStepPreview(title = title, prompter = prompter))
            }
        }

        if (normalizedGoal == "未知") {
            appendStep("大步骤 1：先确认用户想做什么", "先帮助用户把当前要推进的事说清楚，再决定如何陪跑。")
            appendStep("大步骤 2：确认用户现在人在哪里、手边有什么", "优先问环境和准备度，别急着推进任务内容。")
            appendStep("大步骤 3：给出一个能立刻开始的最小动作", "让真人只提醒一个动作，降低启动门槛。")
            return fallbackSteps
        }

        appendStep("大步骤 1：进入任务环境", "先确认用户有没有到位，比如坐起、下床、走到桌前、坐下。")
        appendStep("大步骤 2：打开任务入口", "确认设备、页面、材料有没有打开，缺哪个就补哪个。")

        steps.forEachIndexed { index, step ->
            val cleanStep = step.trim()
            if (cleanStep.isNotEmpty()) {
                appendStep(
                    title = "大步骤 ${fallbackSteps.size + 1}：$cleanStep",
                    prompter = when {
                        index == 0 -> "把这一段当成当前主推步骤，提醒要短，确认用户已经开始。"
                        else -> "这一段排在后面，等前一步完成后再推进，不要一次说太多。"
                    }
                )
            }
        }

        appendStep("大步骤 ${fallbackSteps.size + 1}：进入实际处理", "当环境和入口都就绪后，再推进真正的任务动作。")
        appendStep("大步骤 ${fallbackSteps.size + 1}：收尾确认", "最后确认用户是否完成当前轮目标，要不要继续下一轮。")

        return fallbackSteps.take(5).mapIndexed { index, step ->
            val normalizedTitle = step.title.replace(Regex("""^大步骤\s*\d+："""), "").trim()
            SupervisorStepPreview(
                title = "大步骤 ${index + 1}：$normalizedTitle",
                prompter = step.prompter
            )
        }
    }

    private fun buildSupervisorPreviewFromBreakdown(
        breakdown: SupervisorTaskBreakdown,
        fallbackGoal: String,
        fallbackState: String,
        fallbackSteps: List<String>
    ): SupervisorPreview {
        val mainGoal = breakdown.goal?.trim().orEmpty().ifEmpty { fallbackGoal.trim().ifEmpty { "未知" } }
        val userState = fallbackState.trim().ifEmpty { "未知" }
        val parsedSteps = breakdown.steps
            .sortedBy { it.order }
            .mapIndexed { index, step ->
            val normalizedTitle = step.title.replace(Regex("""^大步骤\s*\d+："""), "").trim().ifEmpty { "未命名步骤" }
            SupervisorStepPreview(
                title = "大步骤 ${index + 1}：$normalizedTitle",
                prompter = step.detail.ifBlank { "无提词" }
            )
        }
        val fallbackSeries = buildSupervisorFallbackSeries(mainGoal, userState, fallbackSteps)
        val mergedSteps = (parsedSteps + fallbackSeries)
            .fold(mutableListOf<SupervisorStepPreview>()) { acc, item ->
                val normalizedTitle = item.title.replace(Regex("""^大步骤\s*\d+："""), "").trim()
                if (normalizedTitle.isNotEmpty() && acc.none { it.title.contains(normalizedTitle) }) {
                    acc.add(item)
                }
                acc
            }
            .take(if (parsedSteps.size >= 3) parsedSteps.size else 4)
            .mapIndexed { index, step ->
                val normalizedTitle = step.title.replace(Regex("""^大步骤\s*\d+："""), "").trim()
                SupervisorStepPreview(
                    title = "大步骤 ${index + 1}：$normalizedTitle",
                    prompter = step.prompter
                )
            }

        return SupervisorPreview(
            mainGoal = mainGoal,
            userState = userState,
            interventionNeed = estimateSupervisorIntervention(mainGoal, userState, parsedSteps.size, breakdown.mode),
            steps = mergedSteps,
            sourceHint = if (breakdown.mode.isNullOrBlank()) "监督链路" else "监督链路/${breakdown.mode}",
            currentStepLabel = parsedSteps.firstOrNull()?.title?.let { "当前推进：$it" }
        )
    }

    private fun buildSupervisorPreviewFromLockedPlan(
        plan: SupervisorTaskBreakdown,
        fallbackState: String,
        progress: SupervisorProgressReview?
    ): SupervisorPreview {
        val planSteps = plan.steps.sortedBy { it.order }
        val currentStepOrder = progress?.currentStepOrder ?: planSteps.firstOrNull()?.order
        val currentStepTitle = progress?.currentStepTitle?.trim().orEmpty().ifEmpty {
            planSteps.firstOrNull { it.order == currentStepOrder }?.title.orEmpty()
        }
        val advice = progress?.advice?.trim().orEmpty()
        val previewSteps = planSteps.map { item ->
            val cleanTitle = item.title.replace(Regex("""^大步骤\s*\d+："""), "").trim()
            val label = when {
                currentStepOrder != null && item.order < currentStepOrder -> "已过大步骤 ${item.order}：$cleanTitle"
                currentStepOrder != null && item.order == currentStepOrder -> "当前大步骤 ${item.order}：$cleanTitle"
                else -> "后续大步骤 ${item.order}：$cleanTitle"
            }
            val detail = if (currentStepOrder != null && item.order == currentStepOrder && advice.isNotEmpty()) {
                item.detail + "\n监督建议：" + advice
            } else {
                item.detail
            }
            SupervisorStepPreview(label, detail)
        }

        return SupervisorPreview(
            mainGoal = plan.goal?.trim().orEmpty().ifEmpty { "未知" },
            userState = progress?.userState?.trim().orEmpty().ifEmpty { fallbackState.trim().ifEmpty { "未知" } },
            interventionNeed = progress?.interventionNeed?.trim().orEmpty().ifEmpty {
                estimateSupervisorIntervention(plan.goal.orEmpty(), fallbackState, planSteps.size, plan.mode)
            },
            steps = previewSteps,
            sourceHint = if (plan.mode.isNullOrBlank()) "监督链路/锁定计划" else "监督链路/${plan.mode}/锁定计划",
            currentStepLabel = if (currentStepOrder != null) {
                "当前推进：第${currentStepOrder}步 ${currentStepTitle.ifEmpty { "待确认" }}"
            } else {
                "当前推进：待判断"
            },
            supervisorAdvice = advice.takeIf { it.isNotEmpty() }
        )
    }

    private fun estimateSupervisorIntervention(mainGoal: String, userState: String, stepCount: Int, mode: String?): String {
        val normalizedGoal = mainGoal.trim()
        val normalizedState = userState.trim()
        val normalizedMode = mode?.trim().orEmpty()
        return when {
            normalizedMode == "urgent_mode" -> "高"
            normalizedGoal == "未知" -> "中"
            normalizedState.contains("未进入任务环境") -> "低"
            stepCount >= 6 -> "中"
            stepCount >= 4 -> "低"
            else -> "极低"
        }
    }

    private fun renderSupervisorPreview(preview: SupervisorPreview) {
        tvSupervisorMainGoal.text = "主目标：${preview.mainGoal}"
        tvSupervisorUserState.text = "用户状态：${preview.userState}"
        tvSupervisorIntervention.text = "真人介入必要性：${preview.interventionNeed}（${preview.sourceHint}）"
        tvSupervisorPlan.text = buildString {
            preview.currentStepLabel?.takeIf { it.isNotBlank() }?.let {
                append(it).append("\n")
            }
            preview.supervisorAdvice?.takeIf { it.isNotBlank() }?.let {
                append("监督建议：").append(it).append("\n\n")
            }
            append(preview.steps.joinToString("\n\n") { step ->
                "${step.title}\n提词器：${step.prompter}"
            })
        }
    }

    private fun callSupervisorPlanBootstrap(
        userText: String,
        assistantReply: String,
        userTask: String,
        userState: String,
        extractedSteps: List<String>
    ) {
        val turnIdSnapshot = currentTurnId
        val currentLlmProvider = if (KIMI_KEY.isNotBlank()) "Kimi" else "Zhipu"
        val currentLlmModel = if (KIMI_KEY.isNotBlank()) KIMI_MODEL else "glm-4-flash"

                val sysContent = """你是行动启动教练，任务是把用户“想做却做不动”的事，拆成极小、低阻力、按顺序推进的动作，让用户先做出第一个可见动作。

原则：
1. 先解决启动，不直接规划完整任务。
2. 先处理身体和环境阻力，再处理任务本身。
3. 优先给物理动作，不依赖意志力，不说教，不施压。
4. 每步必须单一、具体、可观察、可判断完成，通常 5 秒到 3 分钟内能开始。
5. 用户极度卡住时先给 3 步；否则给 4 到 6 步。
6. 任务要按顺序推进；必要时先从更小、更容易的接触动作开始。

判断顺序：
1. 身体启动阻力：还躺着、没起身、没喝水、没吃东西、太困、身体不适、手机在手里、电脑没开、工位没切换。
2. 任务定义阻力：任务太大、太乱、太模糊，需要先缩成今天唯一最小切片。
3. 情绪阻力：焦虑、完美主义、羞耻、逃避时，把“做好/完成”降级成“先碰一下/先接触”。

场景规则：
1. 床上或沙发上时，优先身体启动类任务。
2. 已在桌前但没开始时，优先关掉手机、打开唯一文件、接触任务、允许粗糙开始。
3. 任务太大时，只给最低启动路径，不给整天计划。
4. 不知道先做什么时，替用户做默认决策。

文案规则：
1. 只输出合法 JSON，不输出解释、markdown 或额外文字。
2. 输出格式固定为：{"mode":"bed_start | desk_start | task_breakdown | urgent_mode","goal":"本轮目标，10到16个汉字","tasks":[{"order":1,"title":"8到12个汉字","detail":"12到18个汉字","done":false}]}
3. tasks 按 order 升序。
4. title 和 detail 都要简短整齐；同组 title 长度接近，最长最短差不超过 4 个汉字。
5. title 用动词开头，只写一个具体动作，不要抽象词，不要句号、引号、括号、emoji，不要把多个动作合并。
6. detail 说明该步要做到什么，长度控制在 12 到 18 个汉字。
7. 默认生成 4 到 6 个任务；极度卡住时生成 3 个；不要超过 6 个。

输出前自检：任务是否够小、够具体、句式统一、长度接近、没有说教、没有一条里塞多个动作；不满足就先重写再输出。""".trimIndent()

        val contextJson = JSONObject().apply {
            put("user_text", userText)
            put("assistant_reply", assistantReply)
            put("user_task", userTask)
            put("user_state", userState)
            put("steps", org.json.JSONArray(extractedSteps))
        }

        val messagesArray = com.google.gson.JsonArray()
        messagesArray.add(JsonObject().apply {
            addProperty("role", "system")
            addProperty("content", sysContent)
        })
        messagesArray.add(JsonObject().apply {
            addProperty("role", "user")
            addProperty("content", contextJson.toString())
        })

        val reqBodyJson = JsonObject().apply {
            addProperty("model", currentLlmModel)
            add("messages", messagesArray)
            addProperty("temperature", 0.3)
        }

        val request = Request.Builder()
            .url(if (KIMI_KEY.isNotBlank()) "https://api.moonshot.cn/v1/chat/completions" else "https://open.bigmodel.cn/api/paas/v4/chat/completions")
            .addHeader("Authorization", "Bearer " + if (KIMI_KEY.isNotBlank()) KIMI_KEY else ZHIPU_KEY)
            .post(okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString()))
            .build()

        Log.i("SUPERVISOR_LLM", "bootstrap dispatch provider=$currentLlmProvider model=$currentLlmModel task=$userTask state=$userState steps=${extractedSteps.size}")

        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.w("SUPERVISOR_LLM", "bootstrap request failed: ${e.message}")
            }

            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    Log.w("SUPERVISOR_LLM", "bootstrap request unsuccessful code=${response.code} body=$respStr")
                    return
                }

                try {
                    val jsonObj = JSONObject(respStr)
                    val choices = jsonObj.getJSONArray("choices")
                    val rawContent = choices.getJSONObject(0).getJSONObject("message").getString("content")
                    val parsed = parseSupervisorBreakdown(rawContent)
                    lockedSupervisorPlan = parsed
                    lockedSupervisorState = userState
                    lastSupervisorProgress = null
                    val preview = buildSupervisorPreviewFromBreakdown(parsed, userTask, userState, extractedSteps)
                    Log.i(
                        "SUPERVISOR_LLM",
                        "bootstrap parsed mode=${parsed.mode ?: "未知"}, goal=${parsed.goal ?: "未知"}, steps=${parsed.steps.joinToString(" | ") { it.order.toString() + ":" + it.title + " => " + it.detail }}"
                    )
                    runOnUiThread {
                        if (turnIdSnapshot != currentTurnId) {
                            Log.i("SUPERVISOR_LLM", "bootstrap stale response ignored for turn=$turnIdSnapshot current=$currentTurnId")
                            return@runOnUiThread
                        }
                        renderSupervisorPreview(preview)
                        syncSupervisorSnapshotToCloud("🧭 监督计划已锁定")
                    }
                    callSupervisorProgressReview(turnIdSnapshot, userText, assistantReply, userState)
                } catch (e: Exception) {
                    Log.w("SUPERVISOR_LLM", "bootstrap parse failed: ${e.message}; raw=$respStr")
                }
            }
        })
    }

    private fun callSupervisorProgressReview(
        turnIdSnapshot: Long,
        userText: String,
        assistantReply: String,
        fallbackState: String
    ) {
        val lockedPlan = lockedSupervisorPlan ?: return
        val currentLlmProvider = if (KIMI_KEY.isNotBlank()) "Kimi" else "Zhipu"
        val currentLlmModel = if (KIMI_KEY.isNotBlank()) KIMI_MODEL else "glm-4-flash"

        val sysContent = """你是给真人监督者看的进度判断助手。下面这组任务已经锁定，不能修改主目标，不能修改任务顺序，也不能重写任务内容。

你的任务只是根据最近的对话记录，判断用户现在推进到哪一步，并给真人一句监督建议。

严格输出合法 JSON：
{
  "current_step_order": 1,
  "current_step_title": "当前最可能所在的步骤 title",
  "user_state": "一句简短状态判断",
  "advice": "给监督者的一句建议，12到24个汉字",
  "intervention_need": "极低 | 低 | 中 | 高 | 急需"
}

规则：
1. 不要改写已有 goal 和 tasks。
2. 如果用户只是口头回应、抱怨、犹豫，没有明确完成动作，就保持当前步不变。
3. 如果用户明确说做到了、拍照反馈完成、或对话强烈表明某步完成了，才推进到下一步。
4. 如果无法判断，就选择最保守的当前步。
5. advice 只给监督者，不是给用户的话术。
6. 只输出 JSON，不输出解释。""".trimIndent()

        val historyArray = org.json.JSONArray()
        historyLog.takeLast(6).forEach { round ->
            historyArray.put(JSONObject().apply {
                put("user", round.first)
                put("assistant", round.second)
            })
        }

        val contextJson = JSONObject().apply {
            put("locked_plan", JSONObject().apply {
                put("mode", lockedPlan.mode)
                put("goal", lockedPlan.goal)
                put("tasks", org.json.JSONArray().apply {
                    lockedPlan.steps.sortedBy { it.order }.forEach { task ->
                        put(JSONObject().apply {
                            put("order", task.order)
                            put("title", task.title)
                            put("detail", task.detail)
                            put("done", task.done)
                        })
                    }
                })
            })
            put("locked_user_state", lockedSupervisorState)
            put("recent_dialogue", historyArray)
            put("current_user_text", userText)
            put("current_assistant_reply", assistantReply)
            put("latest_user_state", fallbackState)
            put("last_progress", JSONObject().apply {
                put("current_step_order", lastSupervisorProgress?.currentStepOrder)
                put("current_step_title", lastSupervisorProgress?.currentStepTitle)
                put("user_state", lastSupervisorProgress?.userState)
                put("advice", lastSupervisorProgress?.advice)
                put("intervention_need", lastSupervisorProgress?.interventionNeed)
            })
        }

        val messagesArray = com.google.gson.JsonArray()
        messagesArray.add(JsonObject().apply {
            addProperty("role", "system")
            addProperty("content", sysContent)
        })
        messagesArray.add(JsonObject().apply {
            addProperty("role", "user")
            addProperty("content", contextJson.toString())
        })

        val reqBodyJson = JsonObject().apply {
            addProperty("model", currentLlmModel)
            add("messages", messagesArray)
            addProperty("temperature", 0.2)
        }

        val request = Request.Builder()
            .url(if (KIMI_KEY.isNotBlank()) "https://api.moonshot.cn/v1/chat/completions" else "https://open.bigmodel.cn/api/paas/v4/chat/completions")
            .addHeader("Authorization", "Bearer " + if (KIMI_KEY.isNotBlank()) KIMI_KEY else ZHIPU_KEY)
            .post(okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString()))
            .build()

        Log.i("SUPERVISOR_LLM", "progress dispatch provider=$currentLlmProvider model=$currentLlmModel goal=${lockedPlan.goal} turn=$turnIdSnapshot")

        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.w("SUPERVISOR_LLM", "progress request failed: ${e.message}")
            }

            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    Log.w("SUPERVISOR_LLM", "progress request unsuccessful code=${response.code} body=$respStr")
                    return
                }

                try {
                    val jsonObj = JSONObject(respStr)
                    val choices = jsonObj.getJSONArray("choices")
                    val rawContent = choices.getJSONObject(0).getJSONObject("message").getString("content")
                    val parsed = parseSupervisorProgressReview(rawContent)
                    lastSupervisorProgress = parsed
                    Log.i(
                        "SUPERVISOR_LLM",
                        "progress parsed step=${parsed.currentStepOrder ?: -1}, title=${parsed.currentStepTitle ?: "未知"}, state=${parsed.userState ?: "未知"}, advice=${parsed.advice ?: "无"}, intervention=${parsed.interventionNeed ?: "未知"}"
                    )
                    runOnUiThread {
                        if (turnIdSnapshot != currentTurnId) {
                            Log.i("SUPERVISOR_LLM", "progress stale response ignored for turn=$turnIdSnapshot current=$currentTurnId")
                            return@runOnUiThread
                        }
                        val preview = buildSupervisorPreviewFromLockedPlan(lockedPlan, fallbackState, parsed)
                        renderSupervisorPreview(preview)
                        syncSupervisorSnapshotToCloud("🧭 监督进度已更新")
                    }
                } catch (e: Exception) {
                    Log.w("SUPERVISOR_LLM", "progress parse failed: ${e.message}; raw=$respStr")
                }
            }
        })
    }

    private fun parseSupervisorBreakdown(rawReply: String): SupervisorTaskBreakdown {
        val sanitized = sanitizeReplyContent(rawReply)
        val contentObj = JSONObject(sanitized)
        val tasks = mutableListOf<SupervisorTaskItem>()
        val taskArray = contentObj.optJSONArray("tasks")
        if (taskArray != null) {
            for (i in 0 until taskArray.length()) {
                val item = taskArray.optJSONObject(i) ?: continue
                val order = item.optInt("order", i + 1)
                val title = item.optString("title").trim()
                val detail = item.optString("detail").trim()
                val done = item.optBoolean("done", false)
                if (title.isNotEmpty() || detail.isNotEmpty()) {
                    tasks.add(
                        SupervisorTaskItem(
                            order = order,
                            title = title.ifEmpty { "步骤 ${i + 1}" },
                            detail = detail.ifEmpty { "无说明" },
                            done = done
                        )
                    )
                }
            }
        }

        return SupervisorTaskBreakdown(
            mode = contentObj.optString("mode").takeIf { it.isNotBlank() },
            goal = contentObj.optString("goal").takeIf { it.isNotBlank() },
            steps = tasks
        )
    }

    private fun parseSupervisorProgressReview(rawReply: String): SupervisorProgressReview {
        val sanitized = sanitizeReplyContent(rawReply)
        val contentObj = JSONObject(sanitized)
        val stepOrder = contentObj.optInt("current_step_order", -1).takeIf { it > 0 }
        return SupervisorProgressReview(
            currentStepOrder = stepOrder,
            currentStepTitle = contentObj.optString("current_step_title").takeIf { it.isNotBlank() },
            userState = contentObj.optString("user_state").takeIf { it.isNotBlank() },
            advice = contentObj.optString("advice").takeIf { it.isNotBlank() },
            interventionNeed = contentObj.optString("intervention_need").takeIf { it.isNotBlank() }
        )
    }

    private fun appendSupervisorSnapshotToCloud(jsonObj: JSONObject) {
        val lockedPlan = lockedSupervisorPlan ?: return
        jsonObj.put("supervisor_mode", lockedPlan.mode ?: "")
        jsonObj.put("supervisor_goal", lockedPlan.goal ?: "")
        jsonObj.put("supervisor_user_state", lastSupervisorProgress?.userState ?: lockedSupervisorState)
        jsonObj.put("supervisor_intervention_need", lastSupervisorProgress?.interventionNeed ?: "")
        jsonObj.put("supervisor_current_step_order", lastSupervisorProgress?.currentStepOrder ?: JSONObject.NULL)
        jsonObj.put("supervisor_current_step_title", lastSupervisorProgress?.currentStepTitle ?: "")
        jsonObj.put("supervisor_advice", lastSupervisorProgress?.advice ?: "")

        val tasksArray = org.json.JSONArray()
        lockedPlan.steps.sortedBy { it.order }.forEach { task ->
            tasksArray.put(JSONObject().apply {
                put("order", task.order)
                put("title", task.title)
                put("detail", task.detail)
                put("done", task.done)
                put("is_current", lastSupervisorProgress?.currentStepOrder == task.order)
            })
        }
        jsonObj.put("supervisor_tasks", tasksArray)

        Log.i(
            "Gulu_Cloud",
            "附加监督快照: goal=${lockedPlan.goal ?: ""}, state=${lastSupervisorProgress?.userState ?: lockedSupervisorState}, currentStep=${lastSupervisorProgress?.currentStepOrder ?: -1}, tasks=${lockedPlan.steps.size}"
        )
    }

    private fun handlePhotoProgressUpdate() {
        ++currentTurnId
        isInterrupted = true
        isRecordingLocal = false
        isHardwarePtt = false
        isAIThinking = true
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
        audioBufferQueue.clear()
        playbackBuffer.reset()

        try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
        try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}
        try { aliyunWebSocket?.cancel() } catch (e: Exception) {}

        runOnUiThread {
            tvAiStatus.text = "📷 已收到进度照片，默认你已完成当前步，正在继续下一步..."
        }

        if (isHumanIntervened) {
            runOnUiThread {
                tvAiStatus.text = "📷 已收到进度照片，真人接管中，陪聊链保持静默..."
            }
            if (lockedSupervisorPlan == null) {
                if (shouldLockSupervisorPlan(lastKnownTask, lastKnownState)) {
                    callSupervisorPlanBootstrap(
                        "我刚通过拍照反馈了当前进度，这表示我已经完成了你刚才让我做的这一步。",
                        "👩‍⚕️ (真人接管中，拍照反馈，陪聊链静默)",
                        lastKnownTask,
                        lastKnownState,
                        lastKnownStepsList.toList()
                    )
                }
            } else {
                callSupervisorProgressReview(
                    currentTurnId,
                    "我刚通过拍照反馈了当前进度，这表示我已经完成了你刚才让我做的这一步。",
                    "👩‍⚕️ (真人接管中，拍照反馈，陪聊链静默)",
                    lastKnownState
                )
            }
            return
        }

        callLLMForReply("我刚通过拍照反馈了当前进度，这表示我已经完成了你刚才让我做的这一步，请直接告诉我下一步。")
    }

    private fun handleTaskCompletedByHardware() {
        ++currentTurnId
        isInterrupted = true
        isRecordingLocal = false
        isHardwarePtt = false
        isAIThinking = true
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
        audioBufferQueue.clear()
        playbackBuffer.reset()

        try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
        try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}
        try { aliyunWebSocket?.cancel() } catch (e: Exception) {}

        resetConversationContext()

        runOnUiThread {
            tvAiStatus.text = "✅ 检测到任务已完成，正在和你告别..."
        }
        callTTSForAudio("好的，今天这件事就先到这里。辛苦了，再见。")
    }

    @SuppressLint("MissingPermission")
    private fun startScan(targetAddress: String? = null) {
        if (bluetoothAdapter == null || !bluetoothAdapter!!.isEnabled) {
            tvStatus.text = "请先打开手机蓝牙"
            return
        }
        if (isScanning) {
            return
        }
        foundDevices.clear()
        llDeviceList.removeAllViews()
        lastUiUpdateTime = System.currentTimeMillis()
        totalAudioBytes = 0
        tvAudioData.text = "Audio 收包统计: 0 bytes"
        val scanner = bluetoothAdapter?.bluetoothLeScanner ?: run {
            tvStatus.text = "蓝牙扫描器不可用"
            return
        }
        if (!targetAddress.isNullOrBlank()) {
            val filters = listOf(ScanFilter.Builder().setDeviceAddress(targetAddress).build())
            val settings = ScanSettings.Builder()
                .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
                .build()
            scanner.startScan(filters, settings, scanCallback)
        } else {
            scanner.startScan(scanCallback)
        }
        isScanning = true
        btnScan.text = "停止扫描"
        tvStatus.text = if (targetAddress.isNullOrBlank()) "正在扫描..." else "正在后台搜索已配对设备..."
        scheduleScanTimeout()
    }

    @SuppressLint("MissingPermission")
    private fun stopScan() {
        cancelScanTimeout()
        bluetoothAdapter?.bluetoothLeScanner?.stopScan(scanCallback)
        isScanning = false
        btnScan.text = "扫描蓝牙设备"
    }

    private val scanCallback = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device
            val name = device.name ?: "Unknown"

            if (name.contains("MBF") && !foundDevices.any { it.address == device.address }) {
                runOnUiThread { tvStatus.text = "发现，自动连接中..." }
                stopScan()
                connectToDevice(device)

                foundDevices.add(device)
                val deviceLayout = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.VERTICAL; setPadding(0, 16, 0, 16) }
                val tvInfo = TextView(this@MainActivity).apply { text = "发现: $name\nMAC: ${device.address}"; textSize = 18f }
                val btnConnect = Button(this@MainActivity).apply {
                    text = "连接设备"
                    setOnClickListener { stopScan(); connectToDevice(device) }
                }
                deviceLayout.addView(tvInfo)
                deviceLayout.addView(btnConnect)
                llDeviceList.addView(deviceLayout)
            }
        }
    }

    @SuppressLint("MissingPermission")
    private fun connectToDevice(device: BluetoothDevice, autoConnect: Boolean = false) {
        disableSimulatedHardwareMode("连接真实硬件")
        cancelReconnectLoop()
        stopScan()
        lastConnectedDeviceAddress = device.address
        saveLastConnectedDeviceAddress(device.address)
        try {
            bluetoothGatt?.close()
        } catch (_: Exception) {
        }
        tvStatus.text = if (autoConnect) {
            "正在后台重连 ${device.name ?: device.address}..."
        } else {
            "正在连接 ${device.name ?: device.address}..."
        }
        bluetoothGatt = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            device.connectGatt(applicationContext, autoConnect, gattCallback, BluetoothDevice.TRANSPORT_LE)
        } else {
            device.connectGatt(applicationContext, autoConnect, gattCallback)
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                cancelReconnectLoop()
                stopScan()
                bluetoothGatt = gatt
                lastConnectedDeviceAddress = gatt.device.address
                saveLastConnectedDeviceAddress(gatt.device.address)
                hasGreeted = false
                isHumanIntervened = false
                resetConversationContext()
                runOnUiThread { tvStatus.text = "已连接！正在请求 MTU..." }
                gatt.requestMtu(512)
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                if (bluetoothGatt == gatt) {
                    bluetoothGatt = null
                }
                try {
                    gatt.close()
                } catch (_: Exception) {
                }
                Log.w("BLE_DEBUG", "GATT disconnected, status=$status, device=${gatt.device.address}")
                runOnUiThread { tvStatus.text = "连接断开，正在后台重连..." }
                scheduleReconnectLoop("蓝牙断开")
            }
        }

        @SuppressLint("MissingPermission", "NewApi")
        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            super.onMtuChanged(gatt, mtu, status)
            gatt.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH)
            Thread.sleep(100)
            runOnUiThread { tvStatus.text = "MTU 协商成功！发现服务..." }
            gatt.discoverServices()
        }

        @SuppressLint("MissingPermission")
        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                runOnUiThread { tvStatus.text = "服务发现成功，准备订阅流..." }
                val service = gatt.getService(SERVICE_UUID)
                if (service != null) {
                    val imuChar = service.getCharacteristic(IMU_CHAR_UUID)
                    if (imuChar != null) {
                        gatt.setCharacteristicNotification(imuChar, true)
                        val descriptor = imuChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(descriptor, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(descriptor)
                        }
                    }
                }
            }
        }

        @SuppressLint("MissingPermission", "NewApi")
        override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                if (descriptor.characteristic.uuid == IMU_CHAR_UUID) {
                    val audioChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(MIC_AUDIO_CHAR_UUID)
                    if (audioChar != null) {
                        gatt.setCharacteristicNotification(audioChar, true)
                        val audioDec = audioChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(audioDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            audioDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(audioDec)
                        }
                        runOnUiThread { tvStatus.text = "已成功订阅雷达与音频数据流！" }
                    }
                } else if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) {
                    val camChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CAM_IMAGE_CHAR_UUID)
                    if (camChar != null) {
                        gatt.setCharacteristicNotification(camChar, true)
                        val camDec = camChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(camDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            camDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(camDec)
                        }
                        runOnUiThread { tvStatus.text = "Camera Data" }
                    }
                } else if (descriptor.characteristic.uuid == CAM_IMAGE_CHAR_UUID) {
                    val cmdChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(CMD_CHAR_UUID)
                    if (cmdChar != null) {
                        gatt.setCharacteristicNotification(cmdChar, true)
                        val cmdDec = cmdChar.getDescriptor(CCCD_UUID)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            gatt.writeDescriptor(cmdDec, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                        } else {
                            cmdDec.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                            gatt.writeDescriptor(cmdDec)
                        }
                    }
                    runOnUiThread { tvStatus.text = "设备就绪！AI 准备中..." }
                    isAIThinking = true
                    callLLMForReply("系统指令：请用一句非常简短、随和的口语向用户打招呼，比如直接问现在要做什么？或接下来我们干点啥？。绝对不要出现拆解任务、系统指令、好的等书面或AI感的话。")
                }
            }
        }

        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, value: ByteArray) {
            handleCharacteristicChange(characteristic.uuid, value)
        }

        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
            if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.TIRAMISU) {
                handleCharacteristicChange(characteristic.uuid, characteristic.value)
            }
        }

        private var lastCamData: ByteArray = ByteArray(0)
        private var lastAudioData: ByteArray = ByteArray(0)

        private fun handleCharacteristicChange(uuid: UUID, data: ByteArray) {
            if (uuid == IMU_CHAR_UUID) {
                // 原代码 IMU 逻辑...
            } else if (uuid == CAM_IMAGE_CHAR_UUID) {
                if (data.contentEquals(lastCamData)) return
                lastCamData = data.clone()

                if (data.size >= 2 && (data[0].toInt() and 0xFF) == 0xFF && (data[1].toInt() and 0xFF) == 0xD8) {
                    imageBuffer.reset()
                    runOnUiThread { tvStatus.text = "正在接入镜头..." }
                }

                if (imageBuffer.size() > 0 || (data.size >= 2 && (data[0].toInt() and 0xFF) == 0xFF && (data[1].toInt() and 0xFF) == 0xD8)) {
                    imageBuffer.write(data)
                } else {
                    return
                }

                val bufferData = imageBuffer.toByteArray()
                if (bufferData.size % 1000 < 250) {
                    runOnUiThread { tvStatus.text = "图像接收中: " + bufferData.size + " B" }
                }

                if (bufferData.size >= 2 && (bufferData[bufferData.size - 2].toInt() and 0xFF) == 0xFF && (bufferData[bufferData.size - 1].toInt() and 0xFF) == 0xD9) {

                    val finalJpgBytes = bufferData.clone()
                    uploadMediaToCloud("image", finalJpgBytes)

                    runOnUiThread {
                        val bitmap = android.graphics.BitmapFactory.decodeByteArray(bufferData, 0, bufferData.size)
                        if (bitmap != null) {
                            ivCamera.setImageBitmap(bitmap)
                        }
                    }
                    imageBuffer.reset()
                    if (lastKnownStepsList.isNotEmpty()) {
                        handlePhotoProgressUpdate()
                    }
                }
            } else if (uuid == CMD_CHAR_UUID) {
                // ✅ 你的原始硬件物理按键打断逻辑（原封不动）
                if (data.isNotEmpty()) {
                    if (data[0].toInt() == 0x02) {
                        isHardwarePtt = true
                        ++currentTurnId
                        isInterrupted = true
                        isAIThinking = false
                        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                        try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
                        try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}
                        try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
                        runOnUiThread { tvAiStatus.text = "🔇 已打断AI ，等待你讲话..." }
                        isRecordingLocal = true
                        audioBufferQueue.clear()
                    } else if (data[0].toInt() == 0x03) {
                        isHardwarePtt = false
                        if (isRecordingLocal) {
                            isRecordingLocal = false
                            isAIThinking = true
                            playbackBuffer.reset()
                            runOnUiThread { tvAiStatus.text = "打包上传音频推给 STT..." }
                            processAndUploadAudio()
                        }
                    } else if (data[0].toInt() == 0x04) {
                        ++currentTurnId
                        isInterrupted = true
                        try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
                        try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}
                        try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
                        playbackBuffer.reset()
                    } else if (data[0].toInt() == 0x05) {
                        handleTaskCompletedByHardware()
                    }
                }
            } else if (uuid == MIC_AUDIO_CHAR_UUID) {
                if (data.contentEquals(lastAudioData)) return
                lastAudioData = data.clone()
                totalAudioBytes += data.size

                if (isPlayingAudio && !isAIThinking) {
                    try {
                        playbackBuffer.write(data)
                        if (playbackBuffer.size() >= MIN_BUFFER_SIZE_THRESHOLD) {
                            val playbackArray = playbackBuffer.toByteArray()
                            playbackBuffer.reset()
                            if (audioExecutor.queue.size > 2) { audioExecutor.queue.clear(); try { audioTrack?.pause(); audioTrack?.flush(); audioTrack?.play(); } catch(e: Exception){} }
                            audioExecutor.execute {
                                try {
                                    if (audioTrack?.playState != android.media.AudioTrack.PLAYSTATE_PLAYING) {
                                        audioTrack?.play()
                                    }
                                    audioTrack?.write(playbackArray, 0, playbackArray.size)
                                } catch (e: Exception) {
                                    e.printStackTrace()
                                }
                            }
                        }
                    } catch (e: Exception) {}
                }

                                // 2. 16-bit VAD AI Logic

                if (isHardwarePtt) {

                    if (isRecordingLocal) {

                        audioBufferQueue.add(data)

                    }

                } else if (isRecordingPtt) {

                    // Do nothing with BLE audio if app UI PTT is recording

                } else if (!isAIThinking && mediaPlayer?.isPlaying != true) {

                    var maxEnergy = 0

                    val shortBuffer = java.nio.ByteBuffer.wrap(data).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()

                    while (shortBuffer.hasRemaining()) {

                        val energy = Math.abs(shortBuffer.get().toInt())

                        if (energy > maxEnergy) maxEnergy = energy

                    }



                    if (maxEnergy > 2000) {

                        if (!isRecordingLocal) {

                            android.util.Log.i("AI_DEBUG", "VAD trigger start")

                            isRecordingLocal = true

                            runOnUiThread { tvAiStatus.text = "🎙️正在录音... (安静1.5秒发送)" }

                        }

                        audioBufferQueue.add(data)



                        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }

                        silenceRunnable = Runnable {

                            android.util.Log.i("AI_DEBUG", "VAD trigger silence end")

                            isRecordingLocal = false

                            isAIThinking = true

                            playbackBuffer.reset()

                            audioTrack?.pause()

                            audioTrack?.flush()

                            if (isPlayingAudio) audioTrack?.play()

                            runOnUiThread { tvAiStatus.text = "🚀打包上传音频推给STT..." }

                            processAndUploadAudio()

                        }

                        silenceHandler.postDelayed(silenceRunnable!!, 1500)

                    } else {

                        if (isRecordingLocal) {

                            audioBufferQueue.add(data)

                        }

                    }

                }
                val now = System.currentTimeMillis()
                if (now - lastUiUpdateTime > 50) {
                    val hexPreview = data.take(3).joinToString(" ") { String.format("%02X", it) } + "..."
                    val textToSet = "Audio 收包统计: " + totalAudioBytes + " Bytes\n最新包: [" + hexPreview + "]"
                    runOnUiThread { tvAudioData.text = textToSet }
                }
            }
        }
    }

    private fun streamPcmToEsp32(audioBytes: ByteArray) {
        Thread {
            val gatt = bluetoothGatt
            val service = gatt?.getService(SERVICE_UUID)
            val spkChar = service?.getCharacteristic(SPK_AUDIO_CHAR_UUID)

            if (gatt != null && spkChar != null && audioBytes.isNotEmpty()) {
                val chunkSize = 480
                var offset = 0
                var bytesSent = 0
                val startTimeMs = System.currentTimeMillis()
                val targetBytesPerMs = 32.0
                val leadTimeMs = 650L

                isInterrupted = false
                while (offset < audioBytes.size) {
                    // ✅ 完美响应打断标志
                    if (isInterrupted) {
                        android.util.Log.i("AI_DEBUG", "BLE Streaming Interrupted!")
                        break
                    }
                    var length = Math.min(chunkSize, audioBytes.size - offset)
                    if (length % 2 != 0) length -= 1
                    if (length <= 0) break

                    val chunk = ByteArray(length)
                    System.arraycopy(audioBytes, offset, chunk, 0, length)

                    if (hardwareVolumeMultiplier != 1.0f) {
                        try {
                            val shortBuffer = java.nio.ByteBuffer.wrap(chunk).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                            val shortArray = ShortArray(shortBuffer.capacity())
                            shortBuffer.get(shortArray)
                            for (i in shortArray.indices) {
                                var v = (shortArray[i] * hardwareVolumeMultiplier).toInt()
                                if (v > 32767) v = 32767
                                if (v < -32768) v = -32768
                                shortArray[i] = v.toShort()
                            }
                            java.nio.ByteBuffer.wrap(chunk).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(shortArray)
                            val modifiedBytes = ByteArray(shortArray.size * 2)
                            java.nio.ByteBuffer.wrap(modifiedBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(shortArray)
                            System.arraycopy(modifiedBytes, 0, chunk, 0, length)
                        } catch(e: Exception) {}
                    }

                    spkChar.value = chunk
                    spkChar.writeType = android.bluetooth.BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE

                    val writeAccepted = try {
                        @Suppress("MISSING_PERMISSION")
                        gatt.writeCharacteristic(spkChar)
                    } catch (e: Exception) {
                        android.util.Log.e("BLE_DEBUG", "Error writing chunk: " + e.message)
                        false
                    }

                    if (!writeAccepted) {
                        try { Thread.sleep(6) } catch (_: Exception) {}
                        continue
                    }

                    offset += length
                    bytesSent += length

                    val expectedElapsedMs = (bytesSent / targetBytesPerMs).toLong()
                    val actualElapsedMs = System.currentTimeMillis() - startTimeMs
                    val sleepTime = expectedElapsedMs - leadTimeMs - actualElapsedMs

                    if (sleepTime > 0) {
                        try { Thread.sleep(sleepTime) } catch(e: Exception) {}
                    } else {
                        try { Thread.sleep(1) } catch(e: Exception) {}
                    }
                }

                // WRITE_NO_RESPONSE 只表示本地栈接受了写入，请额外留一点时间让最后几包真正发完。
                try { Thread.sleep(180) } catch (_: Exception) {}
                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32.")
            }
        }.start()
    }

    @SuppressLint("MissingPermission")
    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }

        // 🌟 【完美恢复】插入打断逻辑 2：App UI 按键的长按真实打断
        android.util.Log.i("AI_DEBUG", "User Pressed PTT! Interrupting AI.")
        ++currentTurnId
        isInterrupted = true
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
        try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}
        try { audioTrack?.pause(); audioTrack?.flush() } catch(e:Exception){}
        try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
        isPlayingAudio = false
        isAIThinking = false
        runOnUiThread { tvAiStatus.text = "🚫用户按键，直接倾听..." }
        audioBufferQueue.clear()

        val minBufSize = android.media.AudioRecord.getMinBufferSize(16000, android.media.AudioFormat.CHANNEL_IN_MONO, android.media.AudioFormat.ENCODING_PCM_16BIT)
        pttAudioRecord = android.media.AudioRecord(android.media.MediaRecorder.AudioSource.MIC, 16000, android.media.AudioFormat.CHANNEL_IN_MONO, android.media.AudioFormat.ENCODING_PCM_16BIT, minBufSize * 2)
        pttAudioBuffer.reset()
        isRecordingPtt = true
        pttAudioRecord?.startRecording()
        Thread {
            val buffer = ByteArray(minBufSize)
            while (isRecordingPtt) {
                val read = pttAudioRecord?.read(buffer, 0, buffer.size) ?: 0
                if (read > 0) {
                    pttAudioBuffer.write(buffer, 0, read)
                }
            }
        }.start()
    }

    private fun stopPttRecordingAndSend() {
        isRecordingPtt = false
        pttAudioRecord?.stop()
        pttAudioRecord?.release()
        pttAudioRecord = null
        val recordedBytes = pttAudioBuffer.toByteArray()
        if (recordedBytes.isNotEmpty()) {
            streamPcmToEsp32(recordedBytes)
        }
    }

    private fun stopSimulatedHardwarePttRecordingAndSendToAi() {
        isRecordingPtt = false
        pttAudioRecord?.stop()
        pttAudioRecord?.release()
        pttAudioRecord = null

        val recordedBytes = pttAudioBuffer.toByteArray()
        if (recordedBytes.isEmpty()) {
            resetAI()
            return
        }

        isAIThinking = true
        playbackBuffer.reset()
        runOnUiThread {
            tvAiStatus.text = "🚀 模拟硬件录音完成，正在送给 AI..."
        }
        processRecordedPcmForAi(recordedBytes)
    }

    private fun processRecordedPcmForAi(recordedBytes: ByteArray) {
        val rem = recordedBytes.size % 4
        val dataLength16k = recordedBytes.size - rem
        if (dataLength16k <= 0) {
            resetAI()
            return
        }

        val header16k = java.nio.ByteBuffer.allocate(44 + dataLength16k).order(java.nio.ByteOrder.LITTLE_ENDIAN)
        header16k.put("RIFF".toByteArray()); header16k.putInt(36 + dataLength16k); header16k.put("WAVE".toByteArray())
        header16k.put("fmt ".toByteArray()); header16k.putInt(16); header16k.putShort(1); header16k.putShort(1)
        header16k.putInt(16000); header16k.putInt(16000 * 2); header16k.putShort(2); header16k.putShort(16)
        header16k.put("data".toByteArray()); header16k.putInt(dataLength16k)
        header16k.put(recordedBytes, 0, dataLength16k)

        val pcm8kBytes = ByteArray(dataLength16k / 2)
        val inShorts = java.nio.ByteBuffer.wrap(header16k.array(), 44, dataLength16k).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
        val outShorts = ShortArray(pcm8kBytes.size / 2)
        for (i in outShorts.indices) {
            outShorts[i] = inShorts.get(i * 2)
        }
        java.nio.ByteBuffer.wrap(pcm8kBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(outShorts)

        val header8k = java.nio.ByteBuffer.allocate(44 + pcm8kBytes.size).order(java.nio.ByteOrder.LITTLE_ENDIAN)
        header8k.put("RIFF".toByteArray()); header8k.putInt(36 + pcm8kBytes.size); header8k.put("WAVE".toByteArray())
        header8k.put("fmt ".toByteArray()); header8k.putInt(16); header8k.putShort(1); header8k.putShort(1)
        header8k.putInt(8000); header8k.putInt(8000 * 2); header8k.putShort(2); header8k.putShort(16)
        header8k.put("data".toByteArray()); header8k.putInt(pcm8kBytes.size)
        header8k.put(pcm8kBytes)

        uploadAudioToCloudStorage(header8k.array())
        uploadToRealAI(header16k.array())
    }

    private fun processAndUploadAudio() {
        if (audioBufferQueue.isEmpty()) {
            resetAI()
            return
        }

        var originalLength = 0
        for (chunk in audioBufferQueue) {
            originalLength += chunk.size
        }

        // 🌟 核心修复：强制规整字节数为 4 的倍数，绝对防崩溃
        val rem = originalLength % 4
        val dataLength16k = originalLength - rem

        // ==========================================
        // 1. 生成喂给 AI 的 16kHz 高清无损版 (保证识别率)
        // ==========================================
        val header16k = java.nio.ByteBuffer.allocate(44 + dataLength16k).order(java.nio.ByteOrder.LITTLE_ENDIAN)

        header16k.put("RIFF".toByteArray()); header16k.putInt(36 + dataLength16k); header16k.put("WAVE".toByteArray())
        header16k.put("fmt ".toByteArray()); header16k.putInt(16); header16k.putShort(1); header16k.putShort(1)
        header16k.putInt(16000); header16k.putInt(16000 * 1 * 2); header16k.putShort(2); header16k.putShort(16)
        header16k.put("data".toByteArray()); header16k.putInt(dataLength16k)

        var bytesWritten = 0
        for (chunk in audioBufferQueue) {
            val writeLen = Math.min(chunk.size, dataLength16k - bytesWritten)
            if (writeLen > 0) {
                header16k.put(chunk, 0, writeLen)
                bytesWritten += writeLen
            }
        }

        audioBufferQueue.clear()
        val wavBytes16k = header16k.array()

        // ==========================================
        // 2. 生成发给微信小程序的 8kHz 压缩版 (防超时、缩减 50% 体积)
        // ==========================================
        val pcm8kBytes = ByteArray(dataLength16k / 2)
        val inShorts = java.nio.ByteBuffer.wrap(wavBytes16k, 44, dataLength16k).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
        val outShorts = ShortArray(pcm8kBytes.size / 2)

        // 核心降频算法：每两个采样点丢弃一个，体积强行缩小 50%，完美保留语义
        for (i in outShorts.indices) {
            outShorts[i] = inShorts.get(i * 2)
        }
        java.nio.ByteBuffer.wrap(pcm8kBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(outShorts)

        val header8k = java.nio.ByteBuffer.allocate(44 + pcm8kBytes.size).order(java.nio.ByteOrder.LITTLE_ENDIAN)
        header8k.put("RIFF".toByteArray()); header8k.putInt(36 + pcm8kBytes.size); header8k.put("WAVE".toByteArray())
        header8k.put("fmt ".toByteArray()); header8k.putInt(16); header8k.putShort(1); header8k.putShort(1)
        header8k.putInt(8000); header8k.putInt(8000 * 1 * 2); header8k.putShort(2); header8k.putShort(16)
        header8k.put("data".toByteArray()); header8k.putInt(pcm8kBytes.size)
        header8k.put(pcm8kBytes)

        val wavBytes8k = header8k.array()

        android.util.Log.i("Gulu_Cloud", "音频准备上传: originalLength=" + originalLength +
            ", dataLength16k=" + dataLength16k +
            ", wav16kBytes=" + wavBytes16k.size +
            ", wav8kBytes=" + wavBytes8k.size)

        // ==========================================
        // 3. 双轨发车
        // ==========================================
        // 上传给小程序：改为先申请直传凭证，再直接 PUT 到云存储
        uploadAudioToCloudStorage(wavBytes8k)

        // 喂给阿里云 STT：依然用 16kHz 高清原版（保证 AI 听得清每一个字）
        uploadToRealAI(wavBytes16k)
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
                        Thread.sleep(200)
                        webSocket.send("{\"header\":{\"action\":\"finish-task\",\"task_id\":\"" + taskId + "\",\"streaming\":\"duplex\"},\"payload\":{\"input\":{}}}")
                    } else if (event == "result-generated" || event == "task-finished") {
                        val outObj = jsonObj.optJSONObject("payload")?.optJSONObject("output")?.optJSONObject("sentence")
                        if (outObj != null && outObj.has("text")) {
                            val latestSentence = outObj.getString("text").trim()
                            if (latestSentence.isNotEmpty()) {
                                // DashScope can repeat the same final sentence on both result-generated and task-finished.
                                // Treat sentence.text as the latest full transcript snapshot instead of a delta chunk.
                                finalStr = latestSentence
                            }
                        }

                        if (event == "task-finished") {
                            webSocket.close(1000, "Done")
                            if (finalStr.trim().isEmpty()) {
                                runOnUiThread { tvAiStatus.text = "⚠️ 没听清你说啥..." }
                                resetAI(500)
                                return
                            }
                            Log.i("AI_DEBUG", "STT Success: " + finalStr)

                            // 🌟 新增 4：真人接管拦截逻辑
                            if (isHumanIntervened) {
                                // 【真人接管模式】
                                // 把之前保存好的目标和步骤打包，保留给小程序端
                                val stepsForCloud = mutableListOf<String>()
                                stepsForCloud.add("🎯 目标：" + lastKnownTask)
                                stepsForCloud.add("💡 状态：" + lastKnownState)
                                stepsForCloud.addAll(lastKnownStepsList)

                                // 同步给云端，告诉小程序 AI 已经静默
                                syncDialogueToCloud(finalStr, "👩‍⚕️ (真人接管中，AI已静默)", stepsForCloud)

                                runOnUiThread {
                                    tvUserVoice.text = "👂 " + finalStr
                                    tvAiStatus.text = "👩‍⚕️ 真人接管中，等待小程序端回话..."
                                }
                                if (lockedSupervisorPlan == null) {
                                    if (shouldLockSupervisorPlan(lastKnownTask, lastKnownState)) {
                                        callSupervisorPlanBootstrap(finalStr, "👩‍⚕️ (真人接管中，陪聊链静默)", lastKnownTask, lastKnownState, lastKnownStepsList.toList())
                                    }
                                } else {
                                    callSupervisorProgressReview(currentTurnId, finalStr, "👩‍⚕️ (真人接管中，陪聊链静默)", lastKnownState)
                                }
                                // 不叫大模型，直接重置去听用户的下一句话！
                                resetAI(500)
                            } else {
                                // 【AI 自动驾驶模式】(你原本的代码)
                                syncDialogueToCloud(finalStr, null, null)
                                runOnUiThread {
                                    tvUserVoice.text = "👂 " + finalStr
                                    tvAiStatus.text = "🚀 STT成功，呼叫大模型..."
                                }
                                callLLMForReply(finalStr)
                            }
                        }
                    } else if (event == "task-failed") {
                        runOnUiThread { tvAiStatus.text = "❌ STT 识别失败" }  
                        resetAI(1500)
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                resetAI(1500)
            }
        })
    }

    private fun callLLMForReply(userText: String) {
        val currentLlmProvider = if (KIMI_KEY.isNotBlank()) "Kimi" else "Zhipu"
        val currentLlmModel = if (KIMI_KEY.isNotBlank()) KIMI_MODEL else "glm-4-flash"

        val sysContent = """你是一个实时行动教练。用户按下按钮后，会说出自己想做但卡住的事。你的任务不是直接给出任务本身的步骤，而是先判断用户现在离这件事还有多远，再带他一步一步靠近，直到真的开始做。

    你的核心目标是：让用户每一轮都知道现在只做哪一步，并且这一步小到可以立刻开始。

    工作规则：
    1. 每轮只给一个下一步，不一次说完整计划。
    2. 默认不要假设用户已经坐在电脑前、已经打开页面、已经准备开始。
    3. 先判断用户现在处在哪一层：
    - 人还没进入任务环境：还在床上、沙发上、路上、没到桌前。
    - 人到了任务环境，但设备没开、页面没开、材料没找到。
    - 人已经进入任务界面，但不知道先做什么。
    4. 如果用户还没进入任务环境，优先给身体和环境步骤，比如：坐起来、下床、走到电脑前、坐下、打开电脑。
    5. 只有当用户已经进入任务环境后，再给任务步骤，比如：打开邮箱、找到邮件、点开邮件、写第一句回复。
    6. 如果信息不够，不要直接跳到任务内容，可以先问一个最关键的问题，比如：你现在在电脑前吗？
    7. 如果用户完成了当前步骤，就直接给下一步，不长篇总结。
    8. 如果用户说不对、不是这个情况、我做不到，就立刻调整，把下一步拆得更小，不争辩。
    9. 如果用户通过拍照反馈进度，默认视为用户已经完成当前这一步；在此基础上继续给下一步，不要让他倒退。
    10. 记住用户原始目标、当前阶段和已完成步骤，不要每轮重新规划。

    拆解原则：
    1. 动作必须小、具体、立刻能做。
    2. 优先用明确动作词：坐起、下床、走到、坐下、打开、点开、找到、写下、发送。
    3. 每一步只做一件事。
    4. 优先从最靠近现实的位置开始，不要跳步。
    5. 你的目标不是直接推进任务内容，而是先缩短用户和任务之间的距离。

    表达风格：
    1. 像真人在旁边带着做事，短句、自然、稳定。
    2. 多说正向动作，少说不要、别、不用、先别、只做。
    3. 不讲大道理，不做情绪分析，不说教。
    4. 只解释为什么现在做这一步，不解释为什么别的先不做。

    每轮回复尽量用这个结构：
    - 简短承接。
    - 当前动作，或一个关键判断问题。
    - 一句很短的原因。
    - 做完后的续接。

    例如用户说我想回复海外用户邮件，你不要默认他已经能打开邮箱。你应先确认他是否已经到电脑前；如果没有，就先带他到电脑前，再打开电脑，再打开邮箱，再找到那封邮件，再进入回复。

    你的标准很简单：用户听完后，应该觉得这一步离自己很近，而不是更远。

    你必须只返回一个合法的 JSON 对象，绝对不要输出任何其他前后缀废话。
    必须包含以下字段：
    "reply": "你要对用户说的口语化回复（保持温柔自然，暗中引导，千万不要说你在记录数据）",
    "user_task": "提取出的任务，如果未知请输出『未知』",
    "user_state": "提取出的状态，如果未知请输出『未知』",
    "steps": ["当前这一轮唯一要做的下一步；如果这一轮更适合先确认关键状态，就把这个问题写在这里"]""".trimIndent()

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
            addProperty("model", currentLlmModel)
            add("messages", messagesArray)
        }

        val body = okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())
        val request = Request.Builder()
            .url(if (KIMI_KEY.isNotBlank()) "https://api.moonshot.cn/v1/chat/completions" else "https://open.bigmodel.cn/api/paas/v4/chat/completions")
            .addHeader("Authorization", "Bearer " + if (KIMI_KEY.isNotBlank()) KIMI_KEY else ZHIPU_KEY)
            .post(body)
            .build()

        Log.i("LLM_DEBUG", "provider=$currentLlmProvider, model=$currentLlmModel, url=${request.url}")
        runOnUiThread {
            tvAiStatus.text = "🧠 正在思考... 当前模型：$currentLlmProvider / $currentLlmModel"
        }

        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                resetAI(1500)
            }

            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body?.string() ?: ""
                try {
                    val jsonObj = JSONObject(respStr)
                    val choices = jsonObj.getJSONArray("choices")
                    val replyText = choices.getJSONObject(0).getJSONObject("message").getString("content")

                    historyLog.add(Pair(userText, replyText))
                    while (historyLog.size > maxHistoryRounds) {
                        historyLog.removeAt(0)
                    }

                    var userTask = lastKnownTask
                    var userState = lastKnownState
                    var stepsText = lastKnownStepsText
                    var finalReplyText = replyText
                    val extractedSteps = mutableListOf<String>()
                    extractedSteps.addAll(lastKnownStepsList)

                    try {
                        val parsed = parseAssistantReply(replyText)

                        val parsedReply = parsed.reply?.trim().orEmpty()
                        if (parsedReply.isNotEmpty()) {
                            finalReplyText = parsedReply
                        }

                        val parsedTask = parsed.userTask?.trim().orEmpty()
                        if (parsedTask.isNotEmpty() && parsedTask != "未知") {
                            userTask = parsedTask
                            lastKnownTask = parsedTask
                        }

                        val parsedState = parsed.userState?.trim().orEmpty()
                        if (parsedState.isNotEmpty() && parsedState != "未知") {
                            userState = parsedState
                            lastKnownState = parsedState
                        }

                        if (parsed.steps.isNotEmpty()) {
                            val sb = StringBuilder()
                            extractedSteps.clear()
                            lastKnownStepsList.clear()
                            parsed.steps.forEachIndexed { index, step ->
                                extractedSteps.add(step)
                                lastKnownStepsList.add(step)
                                sb.append(index + 1).append(". ").append(step).append("\n")
                            }
                            stepsText = sb.toString().trim()
                            lastKnownStepsText = stepsText
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }

                    val stepsForCloud = mutableListOf<String>()
                    stepsForCloud.add("🎯 目标：" + userTask)
                    stepsForCloud.add("💡 状态：" + userState)
                    stepsForCloud.addAll(extractedSteps)
                    
                    syncDialogueToCloud(userText, finalReplyText, stepsForCloud)

                    runOnUiThread {
                        tvAiReply.text = "AI: " + finalReplyText
                        tvAiStatus.text = "🔊 正在全自动生成逼真语音(TTS)..."
                        tvUserTask.text = "🎯 目标任务：" + userTask
                        tvUserState.text = "💡 当前状态：" + userState
                        tvActionSteps.text = "🪜 拆解步骤：\n" + stepsText
                        val lockedPlan = lockedSupervisorPlan
                        if (lockedPlan != null) {
                            renderSupervisorPreview(buildSupervisorPreviewFromLockedPlan(lockedPlan, userState, lastSupervisorProgress))
                        } else {
                            renderSupervisorPreview(buildLocalSupervisorPreview(userTask, userState, extractedSteps))
                        }

                        val actionText = "想要" + userTask + "，状态是" + userState
                        val existingAnny = poolItems.find { it.userName == "Anny" }
                        if (existingAnny != null) {
                            existingAnny.userAction = actionText
                            existingAnny.timestamp = System.currentTimeMillis()
                            existingAnny.steps = extractedSteps
                        } else {
                            poolItems.add(0, HelpRequest("Anny", actionText, System.currentTimeMillis(), extractedSteps))
                            if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                        }
                        renderPool()
                    }
                    callTTSForAudio(finalReplyText)
                    if (lockedSupervisorPlan == null) {
                        if (shouldLockSupervisorPlan(userTask, userState)) {
                            callSupervisorPlanBootstrap(userText, finalReplyText, userTask, userState, extractedSteps)
                        }
                    } else {
                        callSupervisorProgressReview(currentTurnId, userText, finalReplyText, userState)
                    }

                } catch (e: Exception) {
                    resetAI(1500)
                }
            }
        })
    }

    private fun parseAssistantReply(rawReply: String): ParsedAssistantReply {
        val sanitized = sanitizeReplyContent(rawReply)

        try {
            val contentObj = org.json.JSONObject(sanitized)
            val steps = mutableListOf<String>()
            val stepsArray = contentObj.optJSONArray("steps")
            if (stepsArray != null) {
                for (i in 0 until stepsArray.length()) {
                    val step = stepsArray.optString(i).trim()
                    if (step.isNotEmpty()) {
                        steps.add(step)
                    }
                }
            }

            return ParsedAssistantReply(
                reply = contentObj.optString("reply").takeIf { it.isNotBlank() },
                userTask = contentObj.optString("user_task").takeIf { it.isNotBlank() },
                userState = contentObj.optString("user_state").takeIf { it.isNotBlank() },
                steps = steps
            )
        } catch (_: Exception) {
        }

        return parseTaggedAssistantReply(sanitized)
    }

    private fun sanitizeReplyContent(rawReply: String): String {
        var content = rawReply.trim()
        if (content.startsWith("```json")) {
            content = content.removePrefix("```json")
        } else if (content.startsWith("```")) {
            content = content.removePrefix("```")
        }
        if (content.endsWith("```")) {
            content = content.removeSuffix("```")
        }
        return content.trim()
    }

    private fun parseTaggedAssistantReply(content: String): ParsedAssistantReply {
        val lines = content.lines().map { it.trim() }.filter { it.isNotEmpty() }
        val replyLines = mutableListOf<String>()
        val steps = mutableListOf<String>()
        var userTask: String? = null
        var userState: String? = null
        var explicitReply: String? = null
        var inStepsSection = false

        fun addStepCandidate(raw: String) {
            val cleaned = raw
                .replace(Regex("^(?:[-*•]|\\d+[.)、])\\s*"), "")
                .trim()
            if (cleaned.isNotEmpty()) {
                steps.add(cleaned)
            }
        }

        for (line in lines) {
            when {
                Regex("^(reply|回复|ai回复|assistant reply)\\s*[:：]\\s*(.+)$", RegexOption.IGNORE_CASE).containsMatchIn(line) -> {
                    explicitReply = Regex("^(reply|回复|ai回复|assistant reply)\\s*[:：]\\s*(.+)$", RegexOption.IGNORE_CASE)
                        .find(line)?.groupValues?.get(2)?.trim()
                    inStepsSection = false
                }
                Regex("^(user_task|task|目标任务|目标)\\s*[:：]\\s*(.+)$", RegexOption.IGNORE_CASE).containsMatchIn(line) -> {
                    userTask = Regex("^(user_task|task|目标任务|目标)\\s*[:：]\\s*(.+)$", RegexOption.IGNORE_CASE)
                        .find(line)?.groupValues?.get(2)?.trim()
                    inStepsSection = false
                }
                Regex("^(user_state|state|当前状态|状态)\\s*[:：]\\s*(.+)$", RegexOption.IGNORE_CASE).containsMatchIn(line) -> {
                    userState = Regex("^(user_state|state|当前状态|状态)\\s*[:：]\\s*(.+)$", RegexOption.IGNORE_CASE)
                        .find(line)?.groupValues?.get(2)?.trim()
                    inStepsSection = false
                }
                Regex("^(steps|step|拆解步骤|步骤)\\s*[:：]\\s*(.*)$", RegexOption.IGNORE_CASE).containsMatchIn(line) -> {
                    val rest = Regex("^(steps|step|拆解步骤|步骤)\\s*[:：]\\s*(.*)$", RegexOption.IGNORE_CASE)
                        .find(line)?.groupValues?.get(2)?.trim().orEmpty()
                    inStepsSection = true
                    if (rest.isNotEmpty()) {
                        if (rest.contains("|")) {
                            rest.split("|").map { it.trim() }.filter { it.isNotEmpty() }.forEach { addStepCandidate(it) }
                        } else if (rest.contains("；") || rest.contains(";")) {
                            rest.split(Regex("[；;]"))
                                .map { it.trim() }
                                .filter { it.isNotEmpty() }
                                .forEach { addStepCandidate(it) }
                        } else {
                            addStepCandidate(rest)
                        }
                    }
                }
                inStepsSection && Regex("^(?:[-*•]|\\d+[.)、])\\s*(.+)$").containsMatchIn(line) -> {
                    addStepCandidate(line)
                }
                else -> {
                    inStepsSection = false
                    replyLines.add(line)
                }
            }
        }

        val reply = explicitReply?.takeIf { it.isNotBlank() }
            ?: replyLines.joinToString("\n").trim().takeIf { it.isNotEmpty() }

        return ParsedAssistantReply(
            reply = reply,
            userTask = userTask,
            userState = userState,
            steps = steps
        )
    }

    private fun callTTSForAudio(textToRead: String) {
        if (VOLCENGINE_TTS_APP_ID.isNotBlank() && VOLCENGINE_TTS_ACCESS_TOKEN.isNotBlank()) {
            callVolcengineTTSForAudio(textToRead)
            return
        }
        callLegacyTTSForAudio(textToRead)
    }

    private fun callVolcengineTTSForAudio(textToRead: String) {
        val reqBodyJson = JSONObject().apply {
            put("user", JSONObject().apply {
                put("uid", "android_adhd_user")
            })
            put("req_params", JSONObject().apply {
                put("text", textToRead)
                put("speaker", VOLCENGINE_TTS_SPEAKER)
                put("audio_params", JSONObject().apply {
                    put("format", "pcm")
                    put("sample_rate", 16000)
                })
            })
        }

        val body = okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())
        val request = Request.Builder()
            .url("https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse")
            .addHeader("X-Api-App-Id", VOLCENGINE_TTS_APP_ID)
            .addHeader("X-Api-Access-Key", VOLCENGINE_TTS_ACCESS_TOKEN)
            .addHeader("X-Api-Resource-Id", VOLCENGINE_TTS_RESOURCE_ID)
            .addHeader("Accept", "text/event-stream")
            .post(body)
            .build()

        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread { tvAiStatus.text = "❌ 火山 TTS 请求失败，回退原 TTS" }
                callLegacyTTSForAudio(textToRead)
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    if (!response.isSuccessful) {
                        runOnUiThread { tvAiStatus.text = "❌ 火山 TTS 响应失败，回退原 TTS" }
                        callLegacyTTSForAudio(textToRead)
                        return
                    }

                    try {
                        val responseBody = response.body ?: throw IOException("empty volcengine body")
                        val source = responseBody.source()
                        val pcmOutput = ByteArrayOutputStream()
                        var currentEvent: String? = null
                        val currentData = StringBuilder()
                        var sessionFinished = false

                        fun handleSseEvent(eventName: String?, payloadText: String) {
                            if (payloadText.isBlank()) {
                                return
                            }

                            val json = JSONObject(payloadText)
                            when (eventName) {
                                "352" -> {
                                    val audioBase64 = json.optString("data")
                                    if (audioBase64.isNotEmpty()) {
                                        pcmOutput.write(android.util.Base64.decode(audioBase64, android.util.Base64.DEFAULT))
                                    }
                                }
                                "152" -> {
                                    if (json.optInt("code") == 20000000) {
                                        sessionFinished = true
                                    } else {
                                        throw IOException(json.optString("message", "volcengine session failed"))
                                    }
                                }
                                "153" -> {
                                    throw IOException(json.optString("message", "volcengine tts failed"))
                                }
                            }
                        }

                        while (true) {
                            val line = source.readUtf8Line() ?: break
                            if (line.isBlank()) {
                                handleSseEvent(currentEvent, currentData.toString())
                                currentData.setLength(0)
                                currentEvent = null
                                continue
                            }

                            if (line.startsWith("event:")) {
                                currentEvent = line.removePrefix("event:").trim()
                                continue
                            }

                            if (!line.startsWith("data:")) {
                                continue
                            }

                            val payload = line.removePrefix("data:").trim()
                            if (payload.isEmpty()) {
                                continue
                            }

                            if (currentData.isNotEmpty()) {
                                currentData.append('\n')
                            }
                            currentData.append(payload)
                        }

                        if (currentData.isNotEmpty()) {
                            handleSseEvent(currentEvent, currentData.toString())
                        }

                        val pcmBytes = pcmOutput.toByteArray()
                        if (!sessionFinished || pcmBytes.isEmpty()) {
                            throw IOException("volcengine tts returned no audio")
                        }

                        runOnUiThread { tvAiStatus.text = "🎵 正在外放 AI 语音..." }
                        playPcmAudio(pcmBytes, 16000)
                    } catch (e: Exception) {
                        Log.e("VOLC_TTS", "Volcengine TTS parse failed", e)
                        runOnUiThread { tvAiStatus.text = "❌ 火山 TTS 解析失败，回退原 TTS" }
                        callLegacyTTSForAudio(textToRead)
                    }
                }
            }
        })
    }

    private fun callLegacyTTSForAudio(textToRead: String) {
        val ttsPrompt = "请用坚定、温柔且鼓励的知心大姐姐声音，全自动朗读下面这句话，不需要加任何自己的话，直接读：\n\n" + textToRead

        val messagesArray = com.google.gson.JsonArray()
        val contentArray = com.google.gson.JsonArray()
        contentArray.add(JsonObject().apply {
            addProperty("type", "text")
            addProperty("text", ttsPrompt)
        })
        val uMsg = JsonObject().apply {
            addProperty("role", "user")
            add("content", contentArray)
        }
        messagesArray.add(uMsg)

        val reqBodyJson = JsonObject().apply {
            addProperty("model", "glm-4-voice")
            add("messages", messagesArray)
        }

        val body = okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())
        val request = Request.Builder()
            .url("https://open.bigmodel.cn/api/paas/v4/chat/completions")
            .addHeader("Authorization", "Bearer " + ZHIPU_KEY)
            .post(body)
            .build()

        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                resetAI(1500)
            }

            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body?.string() ?: ""
                try {
                    val jsonObj = JSONObject(respStr)
                    val msgObj = jsonObj.getJSONArray("choices").getJSONObject(0).getJSONObject("message")
                    val audioData = msgObj.getJSONObject("audio").getString("data")
                    runOnUiThread { tvAiStatus.text = "🎵 正在外放 AI 语音..." }
                    playBase64Audio(audioData)
                } catch (e: Exception) {
                    resetAI(1500)
                }
            }
        })
    }

    private fun playPcmAudio(pcmBytes: ByteArray, sampleRate: Int) {
        try {
            val paddedPcmBytes = appendTrailingSilence(pcmBytes, sampleRate, 220)
            val hardwarePaddedPcmBytes = appendTrailingSilence(pcmBytes, sampleRate, 520)
            val wavBytes = wrapPcmAsWav(paddedPcmBytes, sampleRate)
            val tempFile = File(cacheDir, "ai_reply_volc.wav")
            FileOutputStream(tempFile).use { it.write(wavBytes) }

            val shouldPlayLocally = shouldPlayPhoneSpeaker()

            if (shouldPlayLocally) {
                Handler(Looper.getMainLooper()).post {
                    try {
                        mediaPlayer?.release()
                        mediaPlayer = MediaPlayer().apply {
                            setAudioAttributes(
                                android.media.AudioAttributes.Builder()
                                    .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SPEECH)
                                    .setUsage(android.media.AudioAttributes.USAGE_MEDIA)
                                    .build()
                            )
                            setVolume(1.0f, 1.0f)
                            setDataSource(tempFile.absolutePath)
                            prepare()
                            start()
                            setOnCompletionListener {
                                resetAI(1000)
                            }
                        }
                    } catch (e: Exception) {
                        resetAI(1000)
                    }
                }
            } else {
                resetAI(calculatePcmDurationMs(paddedPcmBytes, sampleRate) + 300L)
            }

            streamPcmToEsp32(hardwarePaddedPcmBytes)
        } catch (e: Exception) {
            resetAI(1000)
        }
    }

    private fun appendTrailingSilence(pcmBytes: ByteArray, sampleRate: Int, durationMs: Int): ByteArray {
        val silenceBytes = ((sampleRate * durationMs / 1000) * 2).coerceAtLeast(0)
        if (silenceBytes == 0) {
            return pcmBytes
        }

        val output = ByteArray(pcmBytes.size + silenceBytes)
        System.arraycopy(pcmBytes, 0, output, 0, pcmBytes.size)
        return output
    }

    private fun wrapPcmAsWav(pcmBytes: ByteArray, sampleRate: Int): ByteArray {
        val byteRate = sampleRate * 2
        val buffer = ByteBuffer.allocate(44 + pcmBytes.size).order(ByteOrder.LITTLE_ENDIAN)
        buffer.put("RIFF".toByteArray())
        buffer.putInt(36 + pcmBytes.size)
        buffer.put("WAVE".toByteArray())
        buffer.put("fmt ".toByteArray())
        buffer.putInt(16)
        buffer.putShort(1)
        buffer.putShort(1)
        buffer.putInt(sampleRate)
        buffer.putInt(byteRate)
        buffer.putShort(2)
        buffer.putShort(16)
        buffer.put("data".toByteArray())
        buffer.putInt(pcmBytes.size)
        buffer.put(pcmBytes)
        return buffer.array()
    }

    private fun playIncomingCommandOnPhone(pcmBytes: ByteArray, sampleRate: Int) {
        if (!shouldPlayPhoneSpeaker()) {
            return
        }

        try {
            val paddedPcmBytes = appendTrailingSilence(pcmBytes, sampleRate, 220)
            val wavBytes = wrapPcmAsWav(paddedPcmBytes, sampleRate)
            val tempFile = File(cacheDir, "incoming_command.wav")
            FileOutputStream(tempFile).use { it.write(wavBytes) }

            Handler(Looper.getMainLooper()).post {
                try {
                    mediaPlayer?.release()
                    mediaPlayer = MediaPlayer().apply {
                        setAudioAttributes(
                            android.media.AudioAttributes.Builder()
                                .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SPEECH)
                                .setUsage(android.media.AudioAttributes.USAGE_MEDIA)
                                .build()
                        )
                        setVolume(1.0f, 1.0f)
                        setDataSource(tempFile.absolutePath)
                        prepare()
                        start()
                    }
                } catch (e: Exception) {
                    Log.e("AI_DEBUG", "真人语音手机外放失败", e)
                }
            }
        } catch (e: Exception) {
            Log.e("AI_DEBUG", "真人语音写入本地播放文件失败", e)
        }
    }

    private fun playBase64Audio(base64Str: String) {
        try {
            val audioBytes = android.util.Base64.decode(base64Str, android.util.Base64.DEFAULT)
            val tempFile = File(cacheDir, "ai_reply.wav")
            FileOutputStream(tempFile).use { it.write(audioBytes) }

            val shouldPlayLocally = shouldPlayPhoneSpeaker()

            if (shouldPlayLocally) {
                Handler(Looper.getMainLooper()).post {
                    mediaPlayer?.release()
                    mediaPlayer = MediaPlayer().apply {
                        setAudioAttributes(
                            android.media.AudioAttributes.Builder()
                                .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SPEECH)
                                .setUsage(android.media.AudioAttributes.USAGE_MEDIA)
                                .build()
                        )
                        setVolume(1.0f, 1.0f)
                        setDataSource(tempFile.absolutePath)
                        prepare()
                        start()
                        setOnCompletionListener {
                            resetAI(1000)
                        }
                    }
                }
            }

            if (audioBytes.size > 44) {
                val inRate = (audioBytes[24].toInt() and 0xFF) or
                        ((audioBytes[25].toInt() and 0xFF) shl 8) or
                        ((audioBytes[26].toInt() and 0xFF) shl 16) or
                        ((audioBytes[27].toInt() and 0xFF) shl 24)

                val pcmBytes = ByteArray(audioBytes.size - 44)
                System.arraycopy(audioBytes, 44, pcmBytes, 0, pcmBytes.size)

                val targetRate = 16000
                val finalPcm = if (inRate != targetRate && inRate > 0) {
                    val inShorts = ShortArray(pcmBytes.size / 2)
                    java.nio.ByteBuffer.wrap(pcmBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(inShorts)

                    val ratio = inRate.toDouble() / targetRate.toDouble()
                    val outLen = (inShorts.size / ratio).toInt()
                    val outShorts = ShortArray(outLen)
                    for (i in 0 until outLen) {
                        val inIndex = (i * ratio).toInt()
                        if (inIndex < inShorts.size) {
                            outShorts[i] = inShorts[inIndex]
                        }
                    }
                    val outBytes = ByteArray(outShorts.size * 2)
                    java.nio.ByteBuffer.wrap(outBytes).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(outShorts)
                    outBytes
                } else {
                    pcmBytes
                }

                if (!shouldPlayLocally) {
                    resetAI(calculatePcmDurationMs(finalPcm, targetRate) + 300L)
                }

                streamPcmToEsp32(finalPcm)
            }
        } catch (e: Exception) {
            resetAI(1000)
        }
    }

    override fun onStart() {
        super.onStart()
        isAppInForeground = true
        startAppKeepAliveService()
        if (!isSimulatedHardwareMode && bluetoothGatt == null && !isScanning) {
            attemptAutoConnectOrScan("应用回到前台")
        }
    }

    override fun onStop() {
        super.onStop()
        isAppInForeground = false
        if (!isSimulatedHardwareMode && bluetoothGatt == null && !isScanning) {
            scheduleReconnectLoop("应用进入后台")
        }
    }

    private fun enableSimulatedHardwareModeIfNeeded() {
        if (bluetoothGatt != null) {
            return
        }
        isSimulatedHardwareMode = true
        cancelReconnectLoop()
        if (isScanning) {
            stopScan()
        }
        runOnUiThread {
            tvStatus.text = "模拟硬件模式：当前不自动连接真实硬件"
        }
    }

    private fun disableSimulatedHardwareMode(reason: String) {
        if (!isSimulatedHardwareMode) {
            return
        }
        isSimulatedHardwareMode = false
        Log.i("SIM_HW", "Simulated hardware mode disabled: $reason")
    }

    private fun startAppKeepAliveService() {
        try {
            val serviceIntent = Intent(this, BackgroundKeepAliveService::class.java)
            startForegroundService(this, serviceIntent)
        } catch (e: Exception) {
            Log.e("KEEP_ALIVE", "Failed to start keep alive service", e)
        }
    }

    private fun shouldPlayPhoneSpeaker(): Boolean {
        return !mutePhoneSpeakerWhenAppBackgrounded || isAppInForeground
    }

    private fun attemptAutoConnectOrScan(reason: String) {
        if (isSimulatedHardwareMode && bluetoothGatt == null) {
            runOnUiThread { tvStatus.text = "模拟硬件模式中，跳过真实硬件重连" }
            return
        }

        if (bluetoothGatt != null || isScanning) {
            return
        }

        val adapter = bluetoothAdapter
        if (adapter == null || !adapter.isEnabled) {
            runOnUiThread { tvStatus.text = "蓝牙未开启，暂时无法自动重连" }
            scheduleReconnectLoop(reason)
            return
        }

        val targetAddress = lastConnectedDeviceAddress ?: loadLastConnectedDeviceAddress()
        if (!targetAddress.isNullOrBlank()) {
            try {
                connectToDevice(adapter.getRemoteDevice(targetAddress), true)
                return
            } catch (e: IllegalArgumentException) {
                Log.e("BLE_DEBUG", "Invalid remembered device address: $targetAddress", e)
                clearLastConnectedDeviceAddress()
                lastConnectedDeviceAddress = null
            } catch (e: Exception) {
                Log.e("BLE_DEBUG", "Auto reconnect failed: ${e.message}", e)
            }
        }

        startScan(targetAddress)
    }

    private fun scheduleReconnectLoop(reason: String) {
        if (isSimulatedHardwareMode && bluetoothGatt == null) {
            return
        }
        cancelReconnectLoop()
        reconnectRunnable = Runnable {
            attemptAutoConnectOrScan(reason)
        }
        reconnectHandler.postDelayed(reconnectRunnable!!, reconnectDelayMs)
    }

    private fun cancelReconnectLoop() {
        reconnectRunnable?.let { reconnectHandler.removeCallbacks(it) }
        reconnectRunnable = null
    }

    private fun scheduleScanTimeout() {
        cancelScanTimeout()
        scanTimeoutRunnable = Runnable {
            if (isScanning && bluetoothGatt == null) {
                stopScan()
                scheduleReconnectLoop("扫描超时")
            }
        }
        scanTimeoutHandler.postDelayed(scanTimeoutRunnable!!, scanTimeoutMs)
    }

    private fun cancelScanTimeout() {
        scanTimeoutRunnable?.let { scanTimeoutHandler.removeCallbacks(it) }
        scanTimeoutRunnable = null
    }

    private fun loadLastConnectedDeviceAddress(): String? {
        return getSharedPreferences(BLE_PREFS, Context.MODE_PRIVATE)
            .getString(LAST_DEVICE_ADDRESS_KEY, null)
            ?.takeIf { it.isNotBlank() }
    }

    private fun saveLastConnectedDeviceAddress(address: String) {
        getSharedPreferences(BLE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(LAST_DEVICE_ADDRESS_KEY, address)
            .apply()
    }

    private fun clearLastConnectedDeviceAddress() {
        getSharedPreferences(BLE_PREFS, Context.MODE_PRIVATE)
            .edit()
            .remove(LAST_DEVICE_ADDRESS_KEY)
            .apply()
    }

    private fun calculatePcmDurationMs(pcmBytes: ByteArray, sampleRate: Int): Long {
        if (sampleRate <= 0) {
            return 1000L
        }
        val samples = pcmBytes.size / 2.0
        return ((samples / sampleRate.toDouble()) * 1000.0).toLong().coerceAtLeast(300L)
    }

    private fun resetAI(delayMs: Long = 0) {
        resetAIRunnable?.let { resetAIHandler.removeCallbacks(it) }
        resetAIRunnable = Runnable {
            isAIThinking = false
            isRecordingLocal = false
            isHardwarePtt = false
            audioBufferQueue.clear()
            playbackBuffer.reset()
            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
            audioTrack?.pause()
            audioTrack?.flush()
            if (isPlayingAudio) audioTrack?.play()
            tvAiStatus.text = "💤 AI 闲置就绪，等待听你讲话..."
        }
        resetAIHandler.postDelayed(resetAIRunnable!!, delayMs)
    }

    private fun renderPool() {
        poolListLayout.removeAllViews()
        for (item in poolItems) {
            val view = layoutInflater.inflate(R.layout.pool_item, poolListLayout, false)
            val tvName = view.findViewById<TextView>(R.id.tv_pool_name)
            val tvAction = view.findViewById<TextView>(R.id.tv_pool_action)
            val tvTime = view.findViewById<TextView>(R.id.tv_pool_time)

            tvName.text = item.userName
            tvAction.text = item.userAction
            val minutesAgo = (System.currentTimeMillis() - item.timestamp) / 60000
            tvTime.text = "${minutesAgo}分钟前"

            view.setOnClickListener {
                showHelpDetail(item)
            }
            poolListLayout.addView(view)
        }
    }

    private fun showHelpDetail(item: HelpRequest) {
        poolView.visibility = android.view.View.GONE
        helpDetailView.visibility = android.view.View.VISIBLE

        tvDetailTask.text = "🎯 " + item.userAction

        taskListContainer.removeAllViews()
        for (i in item.steps.indices) {
            val stepView = layoutInflater.inflate(R.layout.task_item, taskListContainer, false)
            val cb = stepView.findViewById<android.widget.CheckBox>(R.id.cb_task)
            val title = stepView.findViewById<TextView>(R.id.tv_task_title)
            title.text = item.steps[i]

            cb.setOnCheckedChangeListener { _, isChecked ->
                title.paintFlags = if (isChecked) title.paintFlags or android.graphics.Paint.STRIKE_THRU_TEXT_FLAG else title.paintFlags and android.graphics.Paint.STRIKE_THRU_TEXT_FLAG.inv()
            }
            taskListContainer.addView(stepView)
        }
    }

    private fun uploadAudioToCloudStorage(fileBytes: ByteArray) {
        val jsonObj = org.json.JSONObject()
        jsonObj.put("action", "getUploadMetadata")
        jsonObj.put("fileType", "audio")
        jsonObj.put("extension", "wav")

        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "申请音频直传凭证失败: " + e.message)
            }

            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                val respBody = response.body?.string() ?: ""
                android.util.Log.i("Gulu_Cloud", "直传凭证响应: code=" + response.code + ", success=" + response.isSuccessful + ", body=" + respBody)

                if (!response.isSuccessful) return

                try {
                    val respJson = org.json.JSONObject(respBody)
                    if (respJson.optInt("code") != 200) {
                        android.util.Log.e("Gulu_Cloud", "直传凭证业务失败: " + respBody)
                        return
                    }

                    val uploadUrl = respJson.optString("url")
                    val authorization = respJson.optString("authorization")
                    val token = respJson.optString("token")
                    val fileID = respJson.optString("fileID")
                    val cosFileId = respJson.optString("cosFileId")
                    val cloudPath = respJson.optString("cloudPath")

                    if (uploadUrl.isEmpty() || authorization.isEmpty() || token.isEmpty() || fileID.isEmpty() || cosFileId.isEmpty() || cloudPath.isEmpty()) {
                        android.util.Log.e("Gulu_Cloud", "直传凭证字段不完整: " + respBody)
                        return
                    }

                    val encodedCloudPath = java.net.URLEncoder.encode(cloudPath, "UTF-8").replace("+", "%20")
                    val uploadBody = okhttp3.RequestBody.create("audio/wav".toMediaTypeOrNull(), fileBytes)
                    val uploadRequest = okhttp3.Request.Builder()
                        .url(uploadUrl)
                        .put(uploadBody)
                        .addHeader("Signature", authorization)
                        .addHeader("x-cos-security-token", token)
                        .addHeader("x-cos-meta-fileid", cosFileId)
                        .addHeader("authorization", authorization)
                        .addHeader("key", encodedCloudPath)
                        .build()

                    okHttpClient.newCall(uploadRequest).enqueue(object : okhttp3.Callback {
                        override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                            android.util.Log.e("Gulu_Cloud", "音频直传云存储失败: " + e.message)
                        }

                        override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                            val uploadRespBody = response.body?.string() ?: ""
                            android.util.Log.i("Gulu_Cloud", "音频直传响应: code=" + response.code + ", success=" + response.isSuccessful + ", body=" + uploadRespBody)

                            if (response.isSuccessful) {
                                registerUploadedMedia(fileID, "audio")
                            }
                        }
                    })
                } catch (e: Exception) {
                    android.util.Log.e("Gulu_Cloud", "解析直传凭证失败: " + e.message)
                }
            }
        })
    }

    private fun registerUploadedMedia(fileID: String, fileType: String) {
        val jsonObj = org.json.JSONObject()
        jsonObj.put("action", "saveUploadedFile")
        jsonObj.put("fileType", fileType)
        jsonObj.put("fileID", fileID)

        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "登记已上传媒体失败: " + e.message)
            }

            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                val respBody = response.body?.string() ?: ""
                android.util.Log.i("Gulu_Cloud", "登记已上传媒体响应: code=" + response.code + ", success=" + response.isSuccessful + ", body=" + respBody)
            }
        })
    }

    private fun uploadMediaToCloud(fileType: String, fileBytes: ByteArray) {
        val base64Str = android.util.Base64.encodeToString(fileBytes, android.util.Base64.NO_WRAP)
        val jsonObj = org.json.JSONObject()
        jsonObj.put("fileType", fileType)
        jsonObj.put("fileBase64", base64Str)

        android.util.Log.i("Gulu_Cloud", "开始上传媒体: type=" + fileType +
            ", rawBytes=" + fileBytes.size +
            ", base64Chars=" + base64Str.length +
            ", jsonChars=" + jsonObj.toString().length)

        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "媒体上传失败: " + e.message)
            }
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                val respBody = response.body?.string() ?: ""
                android.util.Log.i("Gulu_Cloud", "媒体上传响应: code=" + response.code +
                    ", success=" + response.isSuccessful +
                    ", body=" + respBody)
            }
        })
    }

    private fun syncDialogueToCloud(userText: String?, aiText: String?, steps: List<String>?) {
        val jsonObj = org.json.JSONObject()
        jsonObj.put("user_voice_text", userText ?: "")
        jsonObj.put("ai_reply_text", aiText ?: "")
        if (steps != null) {
            val jsonArray = org.json.JSONArray()
            steps.forEach { jsonArray.put(it) }
            jsonObj.put("ai_steps", jsonArray)
        }
        appendSupervisorSnapshotToCloud(jsonObj)
        jsonObj.put("status", if (aiText != null) "🤖 Gulu已回复" else "🎤 Gulu正在思考...")

        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "文本同步失败: " + e.message)
            }
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                android.util.Log.i("Gulu_Cloud", "文本同步成功: " + response.body?.string())
            }
        })
    }

    private fun syncSupervisorSnapshotToCloud(statusText: String) {
        val lockedPlan = lockedSupervisorPlan ?: return
        val jsonObj = org.json.JSONObject()
        jsonObj.put("status", statusText)
        jsonObj.put("user_voice_text", "")
        jsonObj.put("ai_reply_text", "")
        jsonObj.put("ai_steps", org.json.JSONArray())
        appendSupervisorSnapshotToCloud(jsonObj)

        Log.i(
            "Gulu_Cloud",
            "开始同步监督快照: status=$statusText, goal=${lockedPlan.goal ?: ""}, currentStep=${lastSupervisorProgress?.currentStepOrder ?: -1}, advice=${lastSupervisorProgress?.advice ?: ""}"
        )

        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())
        val request = okhttp3.Request.Builder().url(cloudMediaUrl).post(body).build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("Gulu_Cloud", "监督快照同步失败: " + e.message)
            }

            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                android.util.Log.i("Gulu_Cloud", "监督快照同步成功: " + response.body?.string())
            }
        })
    }
    // ==========================================
    // 🌟 新增 5：远程指令轮询与播放引擎
    // ==========================================
    private fun startCommandPolling() {
        commandPollRunnable = object : Runnable {
            override fun run() {
                // 只有在没录音、AI没思考、且没在播放的时候才去拉取，防止声音打架！
                if (!isRecordingLocal && !isRecordingPtt && !isAIThinking && mediaPlayer?.isPlaying != true) {
                    fetchAndPlayCommand()
                }
                commandPollHandler.postDelayed(this, 3000)
            }
        }
        commandPollHandler.postDelayed(commandPollRunnable!!, 3000)
    }

    private fun fetchAndPlayCommand() {
        val cmdUrl = "https://cloud1-2g65h7na8576f841-1418292974.ap-shanghai.app.tcloudbase.com/pull_command"
        val request = okhttp3.Request.Builder().url(cmdUrl).get().build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {}
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                val respStr = response.body?.string() ?: return
                try {
                    val jsonObj = org.json.JSONObject(respStr)
                    if (jsonObj.optInt("code") == 200) {
                        val downloadUrl = jsonObj.optString("audio_url")
                        if (downloadUrl.isNotEmpty()) {
                            downloadAndStreamPcm(downloadUrl)
                        }
                    }
                } catch (e: Exception) {}
            }
        })
    }

    private fun downloadAndStreamPcm(url: String) {
        val request = okhttp3.Request.Builder().url(url).get().build()
        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {}
            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                val pcmBytes = response.body?.bytes()
                if (pcmBytes != null && pcmBytes.isNotEmpty()) {
                    val hardwarePaddedPcmBytes = appendTrailingSilence(pcmBytes, 16000, 720)

                    // 🌟 致命一击：收到小程序发来的声音，瞬间打开接管开关！
                    isHumanIntervened = true

                    runOnUiThread { tvAiStatus.text = "👩‍⚕️ 真人已接管对话，正在外放..." }
                    playIncomingCommandOnPhone(pcmBytes, 16000)
                    streamPcmToEsp32(hardwarePaddedPcmBytes)
                }
            }
        })
    }
}