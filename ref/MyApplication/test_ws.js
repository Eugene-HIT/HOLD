const WebSocket = require('ws');
const ws = new WebSocket('wss://dashscope.aliyuncs.com/api-ws/v1/inference/', {
  headers: {
    'Authorization': 'Bearer sk-2dde2d428b5f4871bb90ad450ae4a515'
  }
});
ws.on('open', () => {
  ws.send(JSON.stringify({
    header: { action: "run-task", task_id: "test", streaming: "duplex" },
    payload: { task_group: "audio", task: "asr", function: "recognition", model: "paraformer-realtime-v1", parameters: { format: "wav", sample_rate: 16000 }, input: {} }
  }));
});
ws.on('message', data => console.log('Message:', data.toString()));
