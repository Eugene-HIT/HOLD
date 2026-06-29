package com.example.myapplication.service.fake

import com.example.myapplication.model.StepItem
import com.example.myapplication.service.AiApiService

class FakeAiApiService : AiApiService {
    override fun askInitialQuestion(): String = "现在想做什么？"

    override fun askPostureQuestion(): String = "现在坐着还是躺着？"

    override fun buildTaskBreakdown(task: String, posture: String): Pair<String, MutableList<StepItem>> {
        val difficulty = if (posture == "躺着") "极难" else "困难"
        return difficulty to mutableListOf(
            StepItem("坐起来"),
            StepItem("穿上拖鞋"),
            StepItem("走到水槽边"),
            StepItem("打开水龙头并开始洗碗")
        )
    }
}

