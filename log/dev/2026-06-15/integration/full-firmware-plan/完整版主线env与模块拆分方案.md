# 完整版主线 env 与模块拆分方案

## 头部信息
- 创建时间：2026-06-15
- 最后更新时间：2026-06-15
- 文档类型：开发前实施文档
- 所属模块：主线集成入口 / PlatformIO env / 状态机模块拆分
- 文档用途：把完整版融合固件从“流程规划”进一步细化到“新 env、目录结构、模块边界、第一阶段实现顺序”

## 1. 文档目的
本文件用于回答一个更具体的问题：

- 下一步代码应该放在哪里
- PlatformIO 应新增什么 env
- 主线入口如何与现有实验入口并行
- 第一版集成代码应拆成哪些模块

目标是让下一阶段开始写代码时，不再重新讨论目录和入口组织方式。

## 2. 新主线入口建议

### 2.1 新增独立主线入口目录
建议新增一个新的主线入口目录，而不是继续扩展当前 [src/main.cpp](src/main.cpp)。

建议目录名：
- `src/full_firmware_xiao_esp32s3/`

建议入口文件：
- `src/full_firmware_xiao_esp32s3/main.cpp`

理由：
- 当前 [src/main.cpp](src/main.cpp) 历史包袱较重，仍保留了 MAX30102、ICS43434、压力、AD8232 的旧主线接入逻辑
- 本次新版主线已经改变了优先级，不再以旧主入口作为最合适基线
- 新主线入口独立出来后，旧主线仍可保留用于回归和对照

### 2.2 新增 PlatformIO env
建议在 [platformio.ini](platformio.ini) 中新增：

- `full_firmware_xiao_esp32s3`

建议策略：
- 继续采用 `build_src_filter`
- 只编译新的主线入口目录
- 复用共享 reader / service 源文件

## 3. 推荐目录结构

### 3.1 第一版即可采用的结构
建议新增以下目录或文件层次：

- `src/full_firmware_xiao_esp32s3/main.cpp`
- `include/full_firmware/firmware_state_machine.h`
- `src/full_firmware_state_machine.cpp`
- `include/full_firmware/imu_respiration_service.h`
- `src/imu_respiration_service.cpp`
- `include/full_firmware/ppg_runtime_service.h`
- `src/ppg_runtime_service.cpp`
- `include/full_firmware/haptic_guidance_service.h`
- `src/haptic_guidance_service.cpp`
- `include/full_firmware/pressure_trigger_service.h`
- `src/pressure_trigger_service.cpp`
- `include/full_firmware/finger_ppg_session.h`
- `src/finger_ppg_session.cpp`
- `include/full_firmware/full_firmware_config.h`

说明：
- 这里不要求一开始就把所有算法完全抽象到极致
- 但至少要把“主状态机”和“各功能服务”分开
- 不建议把所有逻辑继续堆进一个 main.cpp

## 4. 模块职责拆分建议

### 4.1 `firmware_state_machine`
职责：
- 维护顶层状态
- 处理状态迁移
- 控制各服务启停顺序
- 汇总触发条件与超时条件

建议状态枚举：
- `BOOT`
- `CALIBRATION_IMU`
- `MONITOR_PASSIVE`
- `GUIDED_BREATHING`
- `ACTIVE_FINGER_PPG`
- `REPORT_OUTPUT`

### 4.2 `imu_respiration_service`
职责：
- 封装 MPU6050 呼吸校准与运行逻辑
- 对外暴露呼吸率、周期、运动等级、信号质量、校准就绪状态

实现建议：
- 第一版尽量从 [src/mpu6050_xiao_esp32s3_respiration/main.cpp](src/mpu6050_xiao_esp32s3_respiration/main.cpp) 中抽取可复用逻辑
- 不要求一步抽得很漂亮，但要逐步从“实验入口”转成“服务模块”

### 4.3 `ppg_runtime_service`
职责：
- 封装同一颗 MAX30102 在两种模式下的运行：
  - 胸口被动监测模式
  - 指部主动检测模式

必须显式支持：
- `chest_ppg_profile`
- `finger_ppg_profile`

建议对外接口：
- 切换 profile
- 更新采样
- 获取当前 BPM
- 获取当前 beat interval
- 获取 finger present / contact quality
- 获取当前数据质量状态

### 4.4 `haptic_guidance_service`
职责：
- 封装 DRV2605L + LRA 的呼吸引导模式
- 提供“开始提示单震”和“固定引导节律”两类输出

建议对外接口：
- `begin()`
- `playConfirmationPulse()`
- `startBreathingGuidance(pattern)`
- `update()`
- `stop()`

### 4.5 `pressure_trigger_service`
职责：
- 读取压感模块
- 完成去抖
- 识别主动触发事件

第一版建议：
- 只输出一个简单事件：`finger_measure_request`

### 4.6 `finger_ppg_session`
职责：
- 封装“一分钟指部 PPG 测量会话”
- 管理计时、接触质量、数据累积、报告结果

建议对外接口：
- `startSession()`
- `update()`
- `isFinished()`
- `buildReport()`

## 5. 共享配置建议

### 5.1 新增主线专用配置头
建议新增：
- `include/full_firmware/full_firmware_config.h`

放置内容：
- 主状态机超时配置
- 呼吸异常阈值
- 胸口 PPG 运行阈值
- 指部 PPG 会话时长
- 报告阈值
- 是否输出详细日志开关

### 5.2 PPG 双 profile 配置建议
建议使用两个结构体，而不是零散常量：

- `ChestPpgProfile`
- `FingerPpgProfile`

至少应包含：
- LED 电流参数
- 接触质量阈值
- 心率有效范围
- beat interval 有效范围
- HRV 统计窗口长度

## 6. 第一阶段实现顺序

### 阶段 1A：新 env 与空骨架
目标：
- 在 [platformio.ini](platformio.ini) 新增 `full_firmware_xiao_esp32s3`
- 新建 `src/full_firmware_xiao_esp32s3/main.cpp`
- 新建状态机空骨架

验收标准：
- 能单独编译通过
- 上电串口能打印状态切换日志

### 阶段 1B：接入 IMU 校准与被动监测
目标：
- 先只接入 IMU 服务
- 跑通 `BOOT -> CALIBRATION_IMU -> MONITOR_PASSIVE`

验收标准：
- 可复现当前 IMU 校准流程
- 校准完成后可持续输出呼吸和运动状态摘要

### 阶段 1C：接入震动引导闭环
目标：
- 呼吸异常触发 `GUIDED_BREATHING`
- 引导结束后返回 `MONITOR_PASSIVE`

验收标准：
- 呼吸阈值可配置
- 可观察完整状态跳转闭环

### 阶段 1D：接入压感触发事件
目标：
- 接入 pressure trigger service
- 在监测状态下允许进入 `ACTIVE_FINGER_PPG`

验收标准：
- 可稳定触发一次主动测量请求
- 不出现误触连续跳转

### 阶段 1E：接入指部 PPG 一分钟会话
目标：
- 完成最小版本的 finger session
- 先输出最基础报告，不急于追求复杂 HRV

验收标准：
- 一分钟计时完整
- 有结果输出
- 数据不足时能给出“无效/不足”报告

### 阶段 1F：最后再并入胸口 PPG 被动判断
目标：
- 将同一颗 MAX30102 作为被动胸口监测源接入
- 静止条件下启用高心率与简化 HRV 趋势判断

说明：
- 胸口 PPG 放在阶段 1F，而不是更早，并不是不重要
- 而是因为它最依赖参数分化和贴肤质量边界，过早并入会扰乱前面闭环验证

## 7. 当前不建议做的事情
- 不建议第一版同时并入 AD8232
- 不建议第一版就加入复杂多模态评分模型
- 不建议第一版就把胸口 PPG 和指部 PPG 混成一套参数
- 不建议继续把新逻辑叠加进当前 [src/main.cpp](src/main.cpp)

## 8. 第一阶段最小验收闭环
第一阶段真正应追求的最小完整闭环是：

- 上电
- IMU 校准
- 进入被动监测
- 呼吸异常触发震动引导
- 返回监测
- 压感触发主动指部 PPG 测量
- 一分钟后输出最小报告

只要这条链先跑通，后面再把胸口 PPG 被动判断补进去，会更稳。

## 9. 下一步建议
1. 先按本文件创建新的 `full_firmware_xiao_esp32s3` env 与入口目录。
2. 第一轮代码实现只先抽 IMU 和 LRA 两个服务。
3. 第二轮再接入压感和指部 PPG 会话。
4. 最后一轮再并入胸口 PPG 被动监测逻辑。