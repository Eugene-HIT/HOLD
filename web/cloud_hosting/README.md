# Pulse-PPG 微信云托管部署

## 目录结构

```
cloud_hosting/
├── app.py                  # Flask HTTP 后端服务
├── Dockerfile              # 容器化配置
├── requirements.txt        # Python 依赖
├── miniprogram_hosting.js  # 小程序端调用示例
├── README.md               # 本文档
└── models/
    ├── pulseppg_encoder.onnx   # ONNX 编码器模型（108.85 MB）
    └── head_params.npz         # 分类头参数（11.30 KB）
```

## API 接口

### POST /api/ppg_predict

PPG 信号情感检测接口，接收设备时间戳和信号数据，返回三分类结果（基线/压力/愉悦）。

#### 请求参数

`data` 字段包含两个数组：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `t_ms` | `number[]` | 是 | 设备时间戳数组，单位毫秒，从传感器 `device_uptime_ms` 读取 |
| `sig` | `number[]` | 是 | PPG 信号数组，对应 `detrended_ir` 列的值 |

#### 约束条件

- 两个数组长度必须一致
- 数据时长需 ≥ 60 秒，否则无法切出完整片段（返回 code=400）
- 采样率不要求固定，预处理会按时间戳对齐并重采样到 50Hz
- 每满 60 秒切一个片段，支持多段连续预测（如 120 秒数据 → 2 个片段）

#### 请求示例

```javascript
const res = await wx.cloud.callContainer({
  env: 'prod-xxxxxxxxxxxxxx',   // 替换为你的云开发环境ID
  path: '/api/ppg_predict',
  method: 'POST',
  header: { 'content-type': 'application/json' },
  data: {
    // 设备开机后的时间戳（毫秒），逐采样点递增
    t_ms: [374787, 374827, 374867, 374907, ...],

    // 经过去趋势处理的 IR 信号值（可正可负）
    sig: [12.5, -8.3, 45.1, -23.7, ...]
  }
});
```

#### 数据来源

对应 CSV 文件中以下两列：

| device_uptime_ms | detrended_ir |
|------------------|--------------|
| 374787 | -2519.6 |
| 374827 | 123.4 |
| 374867 | -87.2 |
| ... | ... |

小程序端从 MAX30102 传感器实时采集时，只需将每次读取到的 `device_uptime_ms` 和 `detrended_ir` 追加到数组中，攒够 60 秒后一次性发送即可。

#### 返回格式

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "segments_count": 1,
    "predictions": [
      {
        "index": 0,
        "label_id": 1,
        "label": "压力",
        "probabilities": {
          "基线": 0.0000,
          "压力": 1.0000,
          "愉悦": 0.0000
        }
      }
    ]
  }
}
```

#### 错误码

| code | 原因 |
|------|------|
| 400 | `t_ms` 或 `sig` 缺失 |
| 400 | 两数组长度不一致 |
| 400 | 数据为空 |
| 400 | 数据时长不足 60 秒 |
| 500 | 服务器内部错误 |

### GET /health

健康检查接口。

```json
{ "status": "ok" }
```

## 部署步骤

### 1. 上传至微信云托管

1. 打开微信开发者工具 → 云开发 → 云托管 → 新建服务
2. 服务名：`ppg-predict`（可自定义）
3. 上传方式：选择**本地文件夹**，指向 `cloud_hosting/` 目录
4. 等待 Docker 构建完成，服务状态变为"运行中"

### 2. 小程序端初始化

在 `App.js` 的 `onLaunch` 中初始化云能力：

```javascript
App({
  onLaunch() {
    wx.cloud.init({
      env: 'prod-xxxxxxxxxxxxxx'  // 替换为你的云开发环境ID
    });
  }
});
```

### 3. 小程序端调用

```javascript
const res = await wx.cloud.callContainer({
  env: 'prod-xxxxxxxxxxxxxx',
  path: '/api/ppg_predict',
  method: 'POST',
  header: { 'content-type': 'application/json' },
  data: {
    t_ms: t_ms_array,
    sig: sig_array
  }
});

if (res.statusCode === 200 && res.data.code === 0) {
  const predictions = res.data.data.predictions;
  console.log('检测结果:', predictions);
}
```

## 注意事项

- 微信小程序基础库版本需 >= 2.23.0
- 需已开通云开发和云托管服务
- 出现错误码 `-601034` 表示未开通云开发/云托管权限，需在控制台开通
- `callContainer` 调用应放在 `wx.cloud.init` 完成之后
- 如需更换分类头权重，只需替换 `models/head_params.npz` 文件并重新部署
- 如需更换编码器模型，替换 `models/pulseppg_encoder.onnx` 文件并重新部署
