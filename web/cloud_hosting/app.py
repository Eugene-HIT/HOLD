"""
app.py
------
微信云托管 Flask 后端服务。

提供 PPG 信号情感检测 API，接收设备时间戳和信号数据，返回三分类结果（基线/压力/愉悦）。

预处理流程与项目根目录 preprocess.py 完全一致:
  原始信号 -> 基于时间戳线性插值重采样到 50Hz
          -> 0.5-10Hz 带通滤波(Butterworth order=2)
          -> 按窗口长度切分(默认 30s, 可通过 PPG_WINDOW_SEC 环境变量配置)
          -> 每段做百分位 z-score 归一化(percentile=90)

部署方式：
1. 将本目录打包为 Docker 镜像上传至微信云托管
2. 小程序端使用 wx.cloud.callContainer 调用
"""

import os
import json
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# 模型文件路径（容器内路径）
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
ONNX_PATH = os.path.join(MODEL_DIR, "pulseppg_encoder.onnx")
NPZ_PATH = os.path.join(MODEL_DIR, "head_params.npz")

# 预处理参数（与项目根 config.py / preprocess.py 保持一致）
TARGET_HZ = 50
BANDPASS_LOW = 0.5
BANDPASS_HIGH = 10.0
BANDPASS_ORDER = 2
ZNORM_PERCENTILE = 90
# 默认 30s 窗口(与 config.WINDOW_SEC 一致); 通过环境变量可改回 60 兼容旧部署
WINDOW_SEC = int(os.environ.get("PPG_WINDOW_SEC", "30"))
STRIDE_SEC = int(os.environ.get("PPG_STRIDE_SEC", str(WINDOW_SEC // 2)))

# 全局缓存
_sess = None
_clf_params = None

LABEL_NAMES = {
    0: "基线",
    1: "压力",
    2: "愉悦",
}


def load_models():
    global _sess, _clf_params
    if _sess is None:
        import onnxruntime as ort
        _sess = ort.InferenceSession(ONNX_PATH, providers=["CPUExecutionProvider"])

    if _clf_params is None:
        _clf_params = np.load(NPZ_PATH)


# ============ 预处理函数（与 preprocess.py 一致）============
def resample_to_fixed_hz(t_ms: np.ndarray, sig: np.ndarray, target_hz: int = TARGET_HZ) -> np.ndarray:
    """基于真实时间戳做线性插值重采样到均匀 target_hz。"""
    t_s = (t_ms - t_ms[0]) / 1000.0
    duration = t_s[-1]
    n_samples = int(duration * target_hz) + 1
    new_t = np.arange(n_samples) / target_hz
    return np.interp(new_t, t_s, sig)


def bandpass_filter(sig: np.ndarray, fs: int = TARGET_HZ,
                    low: float = BANDPASS_LOW, high: float = BANDPASS_HIGH,
                    order: int = BANDPASS_ORDER) -> np.ndarray:
    """0.5-10Hz 带通滤波(Butterworth order=2), 与 preprocess.py 一致。"""
    from scipy.signal import butter, filtfilt
    nyq = fs / 2
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    return filtfilt(b, a, sig)


def znorm_percent(sig: np.ndarray, percent: int = ZNORM_PERCENTILE) -> np.ndarray:
    """百分位 z-score 归一化, 与 preprocess.py znorm_percent 完全一致。"""
    thresh = np.percentile(sig, percent)
    below = sig[sig < thresh]
    mean = below.mean()
    std = below.std()
    return (sig - mean) / (std + 1e-8)


def segment_signal(sig: np.ndarray, fs: int = TARGET_HZ,
                   window_sec: int = WINDOW_SEC, stride_sec: int = STRIDE_SEC) -> np.ndarray:
    """滑窗切分, 返回 (n_segments, window_len), 与 preprocess.py segment_signal 一致。"""
    window_len = int(window_sec * fs)
    stride_len = int(stride_sec * fs)
    if len(sig) < window_len:
        return np.empty((0, window_len), dtype=np.float32)
    segments = []
    start = 0
    while start + window_len <= len(sig):
        segments.append(sig[start:start + window_len])
        start += stride_len
    return np.stack(segments).astype(np.float32)


def process_array_to_segments(t_ms: np.ndarray, sig: np.ndarray) -> np.ndarray:
    """一站式: 时间戳+原始信号 -> (n_segments, window_len) 归一化片段数组。

    与项目根 preprocess.process_csv_to_segments 算法完全一致, 仅输入源不同:
    - preprocess.py 从 CSV 读取, 这里从 HTTP 请求体读取
    """
    if len(t_ms) == 0 or len(sig) == 0:
        return np.empty((0, int(WINDOW_SEC * TARGET_HZ)), dtype=np.float32)

    # 1. 重采样到 50Hz
    resampled = resample_to_fixed_hz(t_ms, sig, TARGET_HZ)
    # 2. 带通滤波
    filtered = bandpass_filter(resampled, fs=TARGET_HZ)
    # 3. 滑窗切分
    segments = segment_signal(filtered, fs=TARGET_HZ,
                              window_sec=WINDOW_SEC, stride_sec=STRIDE_SEC)
    if segments.shape[0] == 0:
        return segments
    # 4. 逐段百分位 z-norm
    normed = np.stack([znorm_percent(seg) for seg in segments])
    return normed


def predict(embeddings: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = _clf_params
    x = (embeddings - p["scaler_mean"]) / p["scaler_scale"]
    logits = x @ p["clf_coef"].T + p["clf_intercept"]
    exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
    preds = np.argmax(probs, axis=1)
    return preds, probs


@app.route("/api/ppg_predict", methods=["POST"])
def ppg_predict():
    try:
        data = request.get_json()
        t_ms = data.get("t_ms")
        sig = data.get("sig")

        if t_ms is None or sig is None:
            return jsonify({
                "code": 400,
                "message": "缺少必要参数: t_ms 和 sig",
                "data": None
            })

        t_ms = np.array(t_ms, dtype=float)
        sig = np.array(sig, dtype=float)

        if len(t_ms) != len(sig):
            return jsonify({
                "code": 400,
                "message": f"t_ms({len(t_ms)}) 与 sig({len(sig)}) 长度不一致",
                "data": None
            })

        if len(t_ms) == 0:
            return jsonify({
                "code": 400,
                "message": "输入数据为空",
                "data": None
            })

        load_models()

        segments = process_array_to_segments(t_ms, sig)
        if segments.shape[0] == 0:
            return jsonify({
                "code": 400,
                "message": f"数据时长不足 {WINDOW_SEC} 秒，无法切出完整片段",
                "data": None
            })

        x = segments[:, np.newaxis, :].astype(np.float32)
        embeddings = _sess.run(None, {"input": x})[0]
        y_pred, y_prob = predict(embeddings)

        predictions = []
        for i in range(len(y_pred)):
            pred_id = int(y_pred[i])
            prob_dict = {
                LABEL_NAMES[j]: round(float(y_prob[i][j]), 4)
                for j in sorted(LABEL_NAMES.keys())
            }
            predictions.append({
                "index": i,
                "label_id": pred_id,
                "label": LABEL_NAMES.get(pred_id, str(pred_id)),
                "probabilities": prob_dict
            })

        return jsonify({
            "code": 0,
            "message": "ok",
            "data": {
                "window_sec": WINDOW_SEC,
                "segments_count": int(segments.shape[0]),
                "predictions": predictions
            }
        })

    except Exception as e:
        import traceback
        return jsonify({
            "code": 500,
            "message": f"服务器内部错误: {str(e)}",
            "data": traceback.format_exc()
        })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "window_sec": WINDOW_SEC})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port, debug=False)
