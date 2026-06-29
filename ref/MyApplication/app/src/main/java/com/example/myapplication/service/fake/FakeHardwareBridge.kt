package com.example.myapplication.service.fake

import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.service.HardwareBridge

class FakeHardwareBridge(private val activity: AppCompatActivity) : HardwareBridge {
    private var callback: (() -> Unit)? = null

    override fun setLight(color: String) {
        Toast.makeText(activity, "硬件灯光 -> $color", Toast.LENGTH_SHORT).show()
    }

    override fun playVoice(text: String) {
        Toast.makeText(activity, "硬件语音: $text", Toast.LENGTH_SHORT).show()
    }

    override fun connectBluetoothVoice(): Boolean {
        Toast.makeText(activity, "蓝牙语音连接成功(演示)", Toast.LENGTH_SHORT).show()
        return true
    }

    override fun onHardwareButtonConfirmed(onConfirmed: () -> Unit) {
        callback = onConfirmed
    }

    fun simulateButtonPress() {
        callback?.invoke()
    }
}

