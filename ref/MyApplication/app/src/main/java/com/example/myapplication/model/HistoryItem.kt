package com.example.myapplication.model

data class HistoryItem(
    val id: Long,
    val role: CallRole,
    val targetName: String,
    val task: String,
    val steps: List<StepItem>,
    var isPublic: Boolean = true
)

