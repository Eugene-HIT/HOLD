const cloud = require('wx-server-sdk');
const https = require('https');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

function normalizeEnvValue(value) {
  if (typeof value !== 'string') {
    return '';
  }

  return value.trim().replace(/^['\"]|['\"]$/g, '');
}

function stringifyProviderError(errorPayload) {
  if (!errorPayload) {
    return '';
  }

  if (typeof errorPayload === 'string') {
    return errorPayload;
  }

  const messageParts = [];
  if (errorPayload.message) {
    messageParts.push(errorPayload.message);
  }
  if (errorPayload.type) {
    messageParts.push(`type=${errorPayload.type}`);
  }
  if (errorPayload.code) {
    messageParts.push(`code=${errorPayload.code}`);
  }
  if (errorPayload.param) {
    messageParts.push(`param=${errorPayload.param}`);
  }
  return messageParts.join(' / ');
}

function extractReplyText(responseJson) {
  const choice = responseJson && Array.isArray(responseJson.choices) ? responseJson.choices[0] : null;
  const message = choice && choice.message ? choice.message : null;

  if (message && typeof message.content === 'string' && message.content.trim()) {
    return message.content.trim();
  }

  if (message && Array.isArray(message.content)) {
    const text = message.content
      .map((item) => {
        if (!item) {
          return '';
        }
        if (typeof item === 'string') {
          return item;
        }
        if (typeof item.text === 'string') {
          return item.text;
        }
        if (item.type === 'text' && typeof item.content === 'string') {
          return item.content;
        }
        return '';
      })
      .filter(Boolean)
      .join('\n')
      .trim();
    if (text) {
      return text;
    }
  }

  if (typeof choice?.text === 'string' && choice.text.trim()) {
    return choice.text.trim();
  }

  if (typeof responseJson?.output_text === 'string' && responseJson.output_text.trim()) {
    return responseJson.output_text.trim();
  }

  return '';
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
          const statusCode = Number(response.statusCode || 0);
          if (statusCode >= 400) {
            const providerError = stringifyProviderError(json.error);
            reject(new Error(`LLM http ${statusCode}${providerError ? `: ${providerError}` : ''}`));
            return;
          }

          const reply = extractReplyText(json);
          if (!reply) {
            const providerError = stringifyProviderError(json.error);
            const finishReason = json && Array.isArray(json.choices) && json.choices[0]
              ? json.choices[0].finish_reason || ''
              : '';
            const bodyPreview = responseText.replace(/\s+/g, ' ').slice(0, 240);
            reject(new Error(
              `LLM response missing content${providerError ? `: ${providerError}` : ''}${finishReason ? ` / finish_reason=${finishReason}` : ''} / body=${bodyPreview}`
            ));
            return;
          }
          resolve(reply.trim());
        } catch (error) {
          reject(new Error(`LLM response parse failed: ${error.message || 'unknown'}`));
        }
      });
    });

    request.on('error', reject);
    request.write(requestBody);
    request.end();
  });
}

function buildFallbackReply(reportKind = 'overall') {
  if (reportKind === 'active_report') {
    return '当前已提交本次指部 PPG 检测数据，但模型侧没有返回有效分析文本。请结合页面显示的来源与错误原因判断是配置缺失、接口失败，还是模型未返回内容。';
  }

  if (reportKind === 'daily_report') {
    return '当前已提交现有呼吸与胸口 PPG 数据，但模型侧没有返回有效日报分析文本。数据不足时应由模型在正文里说明，而不是前端拦截请求。';
  }

  if (reportKind === 'overall_detailed') {
    return '当前已提交现有整体缓存数据，但模型侧没有返回有效综合报告。请结合页面显示的来源与错误原因继续排查。';
  }

  return JSON.stringify({
    title: '整体分析',
    summary: '当前已收到部分真实监测数据，但云端模型暂未返回结构化摘要。',
    advice: '建议继续积累多次被动与主动记录，再观察趋势变化。',
    sections: [
      { key: 'resp', title: '呼吸报告', body: '请结合近期被动窗口继续观察呼吸稳定度。' },
      { key: 'heart', title: '当天心率报告', body: '请结合当天心率平均值与质量评分一起判断。' },
      { key: 'active', title: '指部 PPG 报告', body: '请优先查看最近一次主动检测的质量与平均心率。' },
      { key: 'overall', title: '总结板块', body: '当前先以趋势参考为主，不建议基于单次结果下结论。' }
    ]
  });
}

exports.main = async (event) => {
  const apiKey = normalizeEnvValue(process.env.LLM_API_KEY || '');
  const baseUrl = normalizeEnvValue(process.env.LLM_BASE_URL || '');
  const model = normalizeEnvValue(process.env.LLM_MODEL || '') || 'gpt-4.1-mini';
  const prompt = event.prompt || '';
  const reportKind = event.report_kind || 'overall';

  if (!prompt) {
    return {
      code: 400,
      reply_text: buildFallbackReply(reportKind),
      source: 'invalid-request',
      error_message: 'prompt empty'
    };
  }

  if (!apiKey || !baseUrl) {
    const missingItems = [];
    if (!apiKey) {
      missingItems.push('LLM_API_KEY');
    }
    if (!baseUrl) {
      missingItems.push('LLM_BASE_URL');
    }
    return {
      code: 200,
      reply_text: buildFallbackReply(reportKind),
      source: 'fallback-config-missing',
      error_message: `missing ${missingItems.join(', ')}`
    };
  }

  try {
    const reply = await callOpenAiCompatibleChat({ apiKey, baseUrl, model, prompt });
    return {
      code: 200,
      reply_text: reply,
      source: 'llm'
    };
  } catch (error) {
    return {
      code: 200,
      reply_text: buildFallbackReply(reportKind),
      source: 'fallback-llm-error',
      error_message: error.message || 'unknown'
    };
  }
};