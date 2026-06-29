package com.example.myapplication.service

import com.example.myapplication.model.StepItem

interface AiApiService {
    fun askInitialQuestion(): String
    fun askPostureQuestion(): String
    fun buildTaskBreakdown(task: String, posture: String): Pair<String, MutableList<StepItem>>
}
