Add-Type -AssemblyName System.Net.WebSockets
Add-Type -AssemblyName System.Net.Http

$uri = [System.Uri]::new('wss://dashscope.aliyuncs.com/api-ws/v1/inference/')
$taskId = 'task_' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$key = 'sk-2dde2d428b5f4871bb90ad450ae4a515'

$client = [System.Net.WebSockets.ClientWebSocket]::new()
$client.Options.SetRequestHeader('Authorization', 'Bearer ' + $key)

function Send-Text([System.Net.WebSockets.ClientWebSocket]$ws, [string]$text) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
    $segment = [ArraySegment[byte]]::new($bytes)
    $ws.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
}

function Send-Binary([System.Net.WebSockets.ClientWebSocket]$ws, [byte[]]$data) {
    $segment = [ArraySegment[byte]]::new($data)
    $ws.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Binary, $true, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
}

function Receive-Text([System.Net.WebSockets.ClientWebSocket]$ws, [int]$timeoutMs = 10000) {
    $buffer = New-Object byte[] 8192
    $segment = [ArraySegment[byte]]::new($buffer)
    $cts = [Threading.CancellationTokenSource]::new($timeoutMs)
    $ms = New-Object System.IO.MemoryStream
    try {
        do {
            $result = $ws.ReceiveAsync($segment, $cts.Token).GetAwaiter().GetResult()
            if ($result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) {
                return '[CLOSE FRAME]'
            }
            $ms.Write($buffer, 0, $result.Count)
        } while (-not $result.EndOfMessage)
        return [System.Text.Encoding]::UTF8.GetString($ms.ToArray())
    } finally {
        $ms.Dispose()
        $cts.Dispose()
    }
}

try {
    $client.ConnectAsync($uri, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
    Write-Output ('CONNECTED state=' + $client.State)

    $runTaskCmd = '{"header":{"action":"run-task","task_id":"' + $taskId + '","streaming":"duplex"},"payload":{"task_group":"audio","task":"asr","function":"recognition","model":"paraformer-realtime-v1","parameters":{"format":"wav","sample_rate":16000},"input":{}}}'
    Send-Text $client $runTaskCmd
    $first = Receive-Text $client 10000
    Write-Output 'FIRST_RESPONSE_START'
    Write-Output $first
    Write-Output 'FIRST_RESPONSE_END'

    if ($first -match 'task-started') {
        # 44-byte WAV header + 3200 bytes silence ~= 100ms mono 16kHz 16-bit
        $pcmBytes = New-Object byte[] 3200
        $totalLen = 44 + $pcmBytes.Length
        $wav = New-Object byte[] $totalLen
        $riff = [System.Text.Encoding]::ASCII.GetBytes('RIFF')
        $wave = [System.Text.Encoding]::ASCII.GetBytes('WAVE')
        $fmt  = [System.Text.Encoding]::ASCII.GetBytes('fmt ')
        $data = [System.Text.Encoding]::ASCII.GetBytes('data')
        [Array]::Copy($riff, 0, $wav, 0, 4)
        [BitConverter]::GetBytes([int]($totalLen - 8)).CopyTo($wav, 4)
        [Array]::Copy($wave, 0, $wav, 8, 4)
        [Array]::Copy($fmt, 0, $wav, 12, 4)
        [BitConverter]::GetBytes([int]16).CopyTo($wav, 16)
        [BitConverter]::GetBytes([int16]1).CopyTo($wav, 20)
        [BitConverter]::GetBytes([int16]1).CopyTo($wav, 22)
        [BitConverter]::GetBytes([int]16000).CopyTo($wav, 24)
        [BitConverter]::GetBytes([int]32000).CopyTo($wav, 28)
        [BitConverter]::GetBytes([int16]2).CopyTo($wav, 32)
        [BitConverter]::GetBytes([int16]16).CopyTo($wav, 34)
        [Array]::Copy($data, 0, $wav, 36, 4)
        [BitConverter]::GetBytes([int]$pcmBytes.Length).CopyTo($wav, 40)
        [Array]::Copy($pcmBytes, 0, $wav, 44, $pcmBytes.Length)

        Send-Binary $client $wav
        $finishCmd = '{"header":{"action":"finish-task","task_id":"' + $taskId + '","streaming":"duplex"},"payload":{"input":{}}}'
        Send-Text $client $finishCmd

        for ($i = 0; $i -lt 4; $i++) {
            try {
                $msg = Receive-Text $client 8000
                Write-Output ('FOLLOWUP_' + $i + '_START')
                Write-Output $msg
                Write-Output ('FOLLOWUP_' + $i + '_END')
                if ($msg -match 'task-finished|task-failed') { break }
            } catch {
                Write-Output ('FOLLOWUP_' + $i + '_ERROR ' + $_.Exception.Message)
                break
            }
        }
    }
} catch {
    Write-Output ('ERROR: ' + $_.Exception.Message)
    if ($_.Exception.InnerException) {
        Write-Output ('INNER: ' + $_.Exception.InnerException.Message)
    }
} finally {
    try {
        if ($client.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
            $client.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, 'done', [Threading.CancellationToken]::None).GetAwaiter().GetResult()
        }
    } catch {}
    $client.Dispose()
}
