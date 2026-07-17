"""
app.py
------
微信云托管 Flask 后端服务。

提供 PPG 信号情感检测 API，接收设备时间戳和信号数据，返回三分类结果（基线/压力/愉悦）。

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


def process_array_to_segments(t_ms: np.ndarray, sig: np.ndarray) -> np.ndarray:
    if len(t_ms) == 0 or len(sig) == 0:
        return np.array([]).reshape(0, 3000)

    start_time = t_ms[0]
    window_sec = 60
    target_hz = 50
    window_len = window_sec * target_hz
    window_ms = window_sec * 1000

    segments = []
    current_start = start_time
    while current_start + window_ms <= t_ms[-1]:
        mask = (t_ms >= current_start) & (t_ms < current_start + window_ms)
        segment_sig = sig[mask]

        if len(segment_sig) >= window_len:
            segment_sig = segment_sig[:window_len]
        else:
            pad_len = window_len - len(segment_sig)
            segment_sig = np.pad(segment_sig, (0, pad_len), mode="edge")

        segments.append(segment_sig)
        current_start += window_ms

    return np.array(segments)


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
                "message": "数据时长不足 60 秒，无法切出完整片段",
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
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port, debug=False)
