[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$appId = "2278522339"
$accessToken = "Q-wccpgWtPazM9Lq47CA0DMZ2TgK0gLA"
$resourceId = "seed-tts-2.0"
$speaker = "zh_female_xiaohe_uranus_bigtts"
$url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse"

$body = @{
    user = @{ uid = "api_check_user" }
    req_params = @{
        text = "quota check"
        speaker = $speaker
        audio_params = @{
            format = "pcm"
            sample_rate = 16000
        }
    }
} | ConvertTo-Json -Depth 6

$headers = @{
    "X-Api-App-Id" = $appId
    "X-Api-Access-Key" = $accessToken
    "X-Api-Resource-Id" = $resourceId
    "Accept" = "text/event-stream"
}

try {
    $response = Invoke-WebRequest -Uri $url -Method Post -Headers $headers -ContentType "application/json" -Body $body -TimeoutSec 60
    Write-Output ("HTTP_STATUS=" + [int]$response.StatusCode)
    $content = $response.Content
    if ([string]::IsNullOrWhiteSpace($content)) {
        Write-Output "EMPTY_BODY"
        exit 0
    }

    Write-Output "BODY_START"
    Write-Output $content
    Write-Output "BODY_END"

    $events = @()
    $currentEvent = ""
    $currentData = ""
    $lines = $content -split "`r?`n"
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            if ($currentEvent -or $currentData) {
                $events += [PSCustomObject]@{ event = $currentEvent; data = $currentData.Trim() }
                $currentEvent = ""
                $currentData = ""
            }
            continue
        }
        if ($line.StartsWith("event:")) {
            $currentEvent = $line.Substring(6).Trim()
            continue
        }
        if ($line.StartsWith("data:")) {
            $piece = $line.Substring(5).Trim()
            if ($currentData) {
                $currentData += "`n"
            }
            $currentData += $piece
        }
    }
    if ($currentEvent -or $currentData) {
        $events += [PSCustomObject]@{ event = $currentEvent; data = $currentData.Trim() }
    }

    foreach ($evt in $events) {
        Write-Output ("PARSED_EVENT=" + $evt.event)
        try {
            $json = $evt.data | ConvertFrom-Json
            if ($json.code) { Write-Output ("CODE=" + $json.code) }
            if ($json.message) { Write-Output ("MESSAGE=" + $json.message) }
            if ($json.data) { Write-Output ("DATA_LENGTH=" + $json.data.Length) }
        } catch {
            Write-Output ("RAW_DATA=" + $evt.data)
        }
    }
} catch {
    Write-Output ("ERROR=" + $_.Exception.Message)
    if ($_.Exception.Response) {
        try {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Output ("ERROR_STATUS=" + $statusCode)
        } catch {}
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errBody = $reader.ReadToEnd()
            $reader.Dispose()
            if ($errBody) {
                Write-Output "ERROR_BODY_START"
                Write-Output $errBody
                Write-Output "ERROR_BODY_END"
            }
        } catch {}
    }
}
