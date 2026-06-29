package com.example.myapplication.model

data class HelpRequest(
    val id: Int,
    val name: String,
    val task: String,
    val difficulty: String,
    val steps: MutableList<StepItem>,
    var waitSeconds: Int
)

