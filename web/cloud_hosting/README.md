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
    ├── pulseppg_encoder.onnx   # ONNX 编码器模型（108.95 MB, 30s 训练, 支持动态序列长度）
    └── head_params.npz         # 分类头参数（11.30 KB, 30s 训练）
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
- 数据时长需 ≥ 30 秒，否则无法切出完整片段（返回 code=400）
  - 由于重采样取整，**建议发送 30.5 秒以上**的数据以留出余量
- 采样率不要求固定，预处理会按时间戳对齐并重采样到 50Hz
- 默认每 30 秒切一个片段、步长 15 秒（50% 重叠），支持多段连续预测
  - 例如发送 60 秒数据 → 切出 3 个片段（起止点 0~30s、15~45s、30~60s）
- 窗口/步长可通过环境变量 `PPG_WINDOW_SEC` / `PPG_STRIDE_SEC` 调整（详见下文"环境变量"）

#### 请求示例

```javascript
// 需确保小程序与目标云开发环境已完成关联(见: https://docs.cloudbase.net/quick-start/create-env)

wx.cloud.init({
    env: 'hold-dev-env-d2gukfp01ac296189',
    traceUser: true,
})

// 调用云托管服务
const result = await wx.cloud.callContainer({
    config: {
        env: 'hold-dev-env-d2gukfp01ac296189',
    },
    path: '/api/ppg_predict',
    method: 'POST',
    header: {
        'X-WX-SERVICE': 'ppg-predict',  // 填入服务名称
        'content-type': 'application/json'
    },
    data: {
        // 设备开机后的时间戳（毫秒），逐采样点递增
        t_ms: [374787, 374827, 374867, 374907, ...],

        // 经过去趋势处理的 IR 信号值（可正可负）
        sig: [12.5, -8.3, 45.1, -23.7, ...]
    }
})
```

#### 数据来源

对应 CSV 文件中以下两列：

| device_uptime_ms | detrended_ir |
|------------------|--------------|
| 374787 | -2519.6 |
| 374827 | 123.4 |
| 374867 | -87.2 |
| ... | ... |

小程序端从 MAX30102 传感器实时采集时，只需将每次读取到的 `device_uptime_ms` 和 `detrended_ir` 追加到数组中，攒够 30 秒后一次性发送即可。

> **实时检测建议**：为缩短首响延迟并持续刷新结果，可采取"滑动窗口"策略——保持发送最近 30 秒的数据，每隔 15 秒发一次。例如采集到第 45 秒时发送 15~45 秒的数据，第 60 秒时发送 30~60 秒的数据，依此类推。

#### 返回格式

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "window_sec": 30,
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

| 字段 | 说明 |
|------|------|
| `window_sec` | 当前服务的窗口长度（秒），由环境变量 `PPG_WINDOW_SEC` 决定 |
| `segments_count` | 实际切出的片段数量 |
| `predictions[].label_id` | 类别 id（0=基线, 1=压力, 2=愉悦） |
| `predictions[].probabilities` | 三分类概率，和为 1 |

#### 错误码

| code | 原因 |
|------|------|
| 400 | `t_ms` 或 `sig` 缺失 |
| 400 | 两数组长度不一致 |
| 400 | 数据为空 |
| 400 | 数据时长不足 30 秒 |
| 500 | 服务器内部错误 |

### GET /health

健康检查接口，返回当前窗口长度便于排查。

```json
{ "status": "ok", "window_sec": 30 }
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
// 需确保小程序与目标云开发环境已完成关联(见: https://docs.cloudbase.net/quick-start/create-env)

App({
  onLaunch() {
    wx.cloud.init({
        env: 'hold-dev-env-d2gukfp01ac296189',
        traceUser: true,
    })
  }
});
```

### 3. 小程序端调用

```javascript
const result = await wx.cloud.callContainer({
    config: {
        env: 'hold-dev-env-d2gukfp01ac296189',
    },
    path: '/api/ppg_predict',
    method: 'POST',
    header: {
        'X-WX-SERVICE': 'ppg-predict',  // 填入服务名称
        'content-type': 'application/json'
    },
    data: {
        t_ms: t_ms_array,
        sig: sig_array
    }
});

if (result.statusCode === 200 && result.data.code === 0) {
  const predictions = result.data.data.predictions;
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
  - 当前 ONNX 已导出**动态序列长度**轴，一份模型可同时支持 15s / 30s / 60s 等任意时长输入，不必按窗口分别维护
- **预处理链路与项目根 `preprocess.py` 完全一致**：时间戳插值重采样到 50Hz → 0.5–10Hz 带通滤波（Butterworth order=2）→ 滑窗切分 → 百分位 z-score 归一化（percentile=90）。本地与线上推理结果数值差异 ≤ 1e-5

## 环境变量

可在微信云托管控制台为服务配置以下环境变量，无需改代码即可切换窗口配置：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | `80` | Flask 监听端口，云托管会自动注入 |
| `PPG_WINDOW_SEC` | `30` | 切窗长度（秒）。如需回滚到 60s 模型，把此值改为 `60` 并替换 `models/` 下的两个文件 |
| `PPG_STRIDE_SEC` | `15`（`PPG_WINDOW_SEC/2`） | 滑窗步长（秒），决定多段预测的密集程度 |

> 切换窗口长度时务必确认 `models/` 下的 ONNX 与 npz 是用同一窗口训练出来的，否则预测会失准。
