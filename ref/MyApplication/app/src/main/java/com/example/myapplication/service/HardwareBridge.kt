package com.example.myapplication.service

interface HardwareBridge {
    fun setLight(color: String)
    fun playVoice(text: String)
    fun connectBluetoothVoice(): Boolean
    fun onHardwareButtonConfirmed(onConfirmed: () -> Unit)
}

