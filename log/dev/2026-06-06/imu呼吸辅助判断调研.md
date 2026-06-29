# 胸口 IMU 呼吸辅助判断调研

## 创建时间
2026-06-06

## 最后更新时间
2026-06-06

## 文档目的
评估在当前 HOLD MVP 中，是否适合引入 MPU6050 或其他 IMU 作为胸口贴身场景下的呼吸辅助判断与运动干扰抑制传感器。

## 已确认结论
- 胸口 IMU 用于呼吸频率估计不是冷门方案，公开论文和原型较多，常见关键词包括 chest-worn IMU、accelerometer respiratory rate、seismocardiography。
- 文献检索结果显示，胸口加速度计和 IMU 常用于呼吸频率估计、呼吸周期估计、姿态识别、活动识别，以及心肺振动监测。
- 动态场景下的方案通常会加入活动识别、人类活动分类或多传感器结构；单 IMU 在运动干扰存在时精度更容易下降。
- 开源仓库存在，但多数为研究或课程项目，成熟度有限，缺少可直接用于 Arduino 产品化的稳定库。

## 外部依据摘要

### PubMed 检索结果
- PubMed 检索 `respiration imu chest wearable` 返回多项结果，包括：
  - `Assessment of Breathing Parameters Using an IMU-Based System`：明确提出基于胸壁运动的 breath-by-breath 提取与姿态无关处理。
  - `An IMU-Based Wearable System for Respiratory Rate Estimation in Static and Dynamic Conditions`：明确提到使用三颗 IMU，同时处理呼吸频率估计与人体活动识别。
  - `Comparison between Chest-Worn Accelerometer and Gyroscope Performance for Heart Rate and Respiratory Rate Monitoring`：直接比较胸前 accelerometer 与 gyroscope 的 HR/RR 监测表现。
  - `A Wearable System with Embedded Conductive Textiles and an IMU for Unobtrusive Cardio-Respiratory Monitoring`：说明胸前 IMU 已用于心肺联合监测。
- PubMed 检索 `respiratory rate accelerometer chest wearable` 还显示：
  - accelerometer chest patch
  - sleep position + respiration estimation
  - hospital respiratory monitoring patch
  说明胸前加速度式呼吸监测在研究和原型层面较常见。

### GitHub 可复用项目线索
- `hanifadrv/RespiratoryRate`
  - 明确写明使用 `MPU-6050 accelerometer sensor` 做实时呼吸频率监测。
  - 依赖 `PeakDetection` 与 `libFilter`。
  - 从源码可见其核心骨架是：
    - 读取 MPU6050 加速度
    - 将姿态角作为主信号
    - 低通滤波
    - 峰值检测
    - 按时间窗统计呼吸次数
  - 结论：适合作为轻量级原型参考，不适合作为现成产品算法直接照搬。
- `UBCBEST/Respiratory-Rate-Monitor`
  - 项目已归档。
  - README 明确写到旧版使用单加速度计贴胸，后续改为胸前+背后双加速度计，以抵消跑动、旋转等附加运动干扰。
  - 结论：运动干扰问题是真实存在的，且公开项目已经用双传感器结构专门处理。
- `seanwaye/accelerometer-resp-rate`
  - 更偏早期课程/学生项目。
  - 可作为思路参考，但工程成熟度较低。

## 对当前项目的判断

### 合理性判断
- 合理。
- 如果当前毫米波在贴身场景下因距离过近导致呼吸估计变差，引入胸口 IMU 作为辅助判断是有工程依据的。
- IMU 的价值主要体现在两类：
  - 胸口微小起伏带来的低频周期信号，可用于估计呼吸节律。
  - 较大幅度身体运动、姿态变化、走动、转身等可被识别，用作运动干扰门控。

### 更适合当前阶段的定位
- 当前阶段更适合把 IMU 定位为“辅助传感器”，不是“新的主呼吸真值链”。
- 优先价值排序建议：
  1. 运动/姿态干扰判断
  2. 贴胸时的呼吸趋势辅助
  3. 与毫米波输出做可信度互补
  4. 未来再考虑更复杂的融合估计

### 不建议当前阶段做的事情
- 不建议现在直接做复杂多模态融合模型。
- 不建议现在追求单颗 MPU6050 在自由活动场景下给出高置信绝对呼吸频率。
- 不建议现在把“IMU 呼吸估计”替代毫米波验证主线。

## 当前阶段推荐落地方向

### 推荐做
- 用 MPU6050 做胸口运动质量评估：
  - 静止
  - 轻微运动
  - 剧烈运动
- 在静止或轻微运动时，提取呼吸辅助信号：
  - 选一个主轴或姿态角
  - 做低频滤波
  - 做峰值检测或零交叉检测
  - 输出呼吸间隔与呼吸频率
- 将 IMU 输出作为毫米波结果的 `quality gate`：
  - 若 IMU 判断剧烈运动，则降低毫米波呼吸值可信度
  - 若 IMU 判断贴胸静止，则提高毫米波或 IMU 呼吸估计的可信度

### 可接受的第一版算法骨架
- 采样频率：50Hz 到 100Hz
- 原始量：acc x/y/z，必要时 gyro x/y/z
- 处理链：
  - 姿态或重力方向估计
  - 选取胸廓起伏更敏感的轴向量
  - 0.1Hz 到 0.7Hz 左右呼吸带通或低通
  - 10 秒到 30 秒滑窗
  - 峰值间隔或自相关估计呼吸周期
  - 输出质量分数

## 是否适合现在去做
- 适合，但只适合做“小步快跑版”。
- 更准确地说：
  - 适合现在新增一个 MPU6050 实验分支，用来做贴胸场景下的运动门控和呼吸趋势辅助。
  - 不适合现在把主线从毫米波验证切换成“IMU 呼吸完整方案开发”。

## 建议下一步
1. 先做 MPU6050 原始采样与静止/走动/转身分类日志。
2. 在胸口贴附静止场景下验证单轴滤波后是否能看到明显呼吸波。
3. 若能看到，再补峰值检测并输出 `breath_interval_s`、`breath_rate_bpm`、`motion_level`。
4. 最后再和 MR60BHA2 串口输出做并排对比，决定是否进入融合阶段。

## 风险与待确认项
- 单颗 MPU6050 的贴附位置、固定方式、松紧程度会显著影响结果。
- 胸口贴身场景下，体动、说话、抬手、转体都可能污染呼吸波形。
- 公开资料能确认“方向正确”，但无法仅凭这些资料保证你当前结构件与佩戴方式一定有足够信噪比。
- 当前未检索到高成熟度、可直接复用到 Arduino 产品原型的胸口 IMU 呼吸完整开源库。

## 参考来源
- PubMed 搜索：`respiration imu chest wearable`
- PubMed 搜索：`respiratory rate accelerometer chest wearable`
- GitHub：`hanifadrv/RespiratoryRate`
- GitHub：`UBCBEST/Respiratory-Rate-Monitor`
- GitHub：`seanwaye/accelerometer-resp-rate`