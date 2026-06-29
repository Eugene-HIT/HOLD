package com.example.myapplication.model

data class StepItem(
    val text: String,
    var completed: Boolean = false,
    var photoPath: String? = null
)

