package com.example.myapplication.service.fake

import com.example.myapplication.service.PhotoCaptureBridge

class FakePhotoCaptureBridge : PhotoCaptureBridge {
    override fun captureStepPhoto(): String = "demo_photo_${System.currentTimeMillis()}"
}

