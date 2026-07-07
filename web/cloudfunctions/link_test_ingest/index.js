const cloud = require('wx-server-sdk');
const https = require('https');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();

function normalizeEnvValue(value) {
  if (typeof value !== 'string') {
    return '';
  }

  return value.trim().replace(/^['\"]|['\"]$/g, '');
}

function callOpenAiCompatibleChat({ apiKey, baseUrl, model, prompt }) {
  return new Promise((resolve, reject) => {
    const requestBody = JSON.stringify({
      model,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 1
    });

    const request = https.request(baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(requestBody),
        Authorization: `Bearer ${apiKey}`
      }
    }, (response) => {
      let responseText = '';

      response.on('data', (chunk) => {
        responseText += chunk.toString();
      });

      response.on('end', () => {
        try {
          const json = JSON.parse(responseText);
          const reply = json.choices && json.choices[0] && json.choices[0].message && json.choices[0].message.content;

          if (!reply) {
            reject(new Error('LLM response missing content'));
            return;
          }

          resolve(reply.trim());
        } catch (error) {
          reject(error);
        }
      });
    });

    request.on('error', reject);
    request.write(requestBody);
    request.end();
  });
}

async function getLlmReply(event) {
  const apiKey = normalizeEnvValue(process.env.LLM_API_KEY || '');
  const baseUrl = normalizeEnvValue(process.env.LLM_BASE_URL || '');
  const model = normalizeEnvValue(process.env.LLM_MODEL || '') || 'gpt-4.1-mini';

  if (!apiKey || !baseUrl) {
    return '已收到按钮事件，云端基础链路已通';
  }

  const prompt = `收到来自 ${event.device_id} 的第 ${event.press_count} 次按钮按下事件，请返回一句 20 字以内的确认文本，说明蓝牙、云端和模型链路已通。`;
  return callOpenAiCompatibleChat({ apiKey, baseUrl, model, prompt });
}

exports.main = async (event) => {
  const now = Date.now();
  const wxContext = cloud.getWXContext();

  const sanitizedEvent = {
    openid: wxContext.OPENID || '',
    device_id: event.device_id || 'unknown-device',
    event_type: event.event_type || 'button_press',
    press_count: Number(event.press_count || 0),
    device_timestamp: Number(event.device_timestamp || 0),
    miniapp_timestamp: Number(event.miniapp_timestamp || now),
    created_at: db.serverDate()
  };

  let llmReply = '';
  let llmStatus = 'success';
  let llmError = '';

  try {
    llmReply = await getLlmReply(sanitizedEvent);
  } catch (error) {
    llmStatus = 'fallback';
    llmReply = '已收到按钮事件，模型代理待补齐配置';
    llmError = error && error.message ? error.message : 'unknown';
  }

  const storagePayload = {
    ...sanitizedEvent,
    llm_status: llmStatus,
    llm_reply: llmReply,
    llm_error: llmError,
    archived_at: now
  };

  const date = new Date(now);
  const dateFolder = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
  const cloudPath = `link-test/${dateFolder}/${sanitizedEvent.device_id}/${now}.json`;

  const uploadResult = await cloud.uploadFile({
    cloudPath,
    fileContent: Buffer.from(JSON.stringify(storagePayload, null, 2), 'utf8')
  });

  const addResult = await db.collection('link_test_events').add({
    data: {
      ...sanitizedEvent,
      llm_status: llmStatus,
      llm_reply: llmReply,
      llm_error: llmError,
      storage_file_id: uploadResult.fileID,
      storage_cloud_path: cloudPath
    }
  });

  return {
    code: 200,
    msg: 'ok',
    record_id: addResult._id,
    storage_file_id: uploadResult.fileID,
    storage_cloud_path: cloudPath,
    llm_status: llmStatus,
    llm_reply: llmReply,
    llm_error: llmError
  };
};