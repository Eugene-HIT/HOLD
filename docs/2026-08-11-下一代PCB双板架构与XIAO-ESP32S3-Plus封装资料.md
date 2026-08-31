# 2026-08-11 下一代 PCB 双板架构与 XIAO ESP32S3 Plus 封装资料

## 文档标题
下一代 HOLD PCB 双板架构规划与 XIAO ESP32S3 Plus 封装资料整理

## 创建时间
2026-08-11

## 最后更新时间
2026-08-11

## 文档目的
为下一代 HOLD 硬件提供一份可直接用于原理图和 PCB 规划的结构草案，重点回答以下问题：

1. 是否将 MCU、LED、PPG 一并集成到下一代 PCB。
2. 是否采用一大一小两块板的分板结构。
3. 小板除 PPG 之外是否还适合承载其他器件。
4. XIAO ESP32S3 Plus 是否适合作为直接焊接到主板上的 SoM，以及其官方封装资料从哪里获取。

## 需求背景
当前工程和网表已经证明，现阶段板级实现更接近“外围功能板”，尚未把主控、RGB/状态灯和 PPG 传感头完整收进一版终板。

已知现状：

1. 当前主线固件口径已经稳定在 XIAO ESP32S3 / Plus 体系。
2. 当前代码实际依赖 IMU、PPG、压力、LRA、热反馈、BLE 和状态灯。
3. 历史板级日志已确认 PPG 对机械扰动、供电扰动和布线口径较敏感。
4. 你当前目标已从“飞线 bring-up”切到“下一代可长期演进的 PCB 架构”。

## 已确认信息

### 1. XIAO ESP32S3 Plus 适合直接作为板载 SoM 使用
基于 Seeed 官方资料，XIAO ESP32S3 Plus 不是只能插针使用的开发板，它本身就是面向 PCBA 集成的 SMD/castellation 形态。

已确认点：

1. 外形尺寸为 21 x 17.8mm。
2. Plus 版保留 XIAO 外形，但新增背面焊盘与更多可引出 IO。
3. Seeed 官方产品页明确将其描述为适合 PCBA 集成的 SoM。
4. Seeed 官方资源页提供了 Plus 版原理图、KiCad 工程、KiCad 封装库、Top/Bottom DXF、3D 模型入口。

这意味着下一代主板可以不再预留一块“插开发板”的大面积区域，而是直接把 XIAO ESP32S3 Plus 当成模块焊在主板上。

### 2. PPG 独立小板是合理方向
基于现有项目经验和 Analog Devices 的 MAX30102 公开资料，可以确认：

1. MAX30102 是集成 LED、PD、光学结构和 cover glass 的反射式光学模组。
2. 它适合可穿戴/贴肤场景，但是否测得稳，强依赖贴肤压力、遮光、机械稳定性和振动隔离。
3. ADI 的参考设计普遍把 MAX30102 放在小尺寸、相对独立的传感板上，而不是和高扰动执行器、电源开关、大电流路径混在一块大板中心。

因此，从“可测性”和“后续机械调姿自由度”来看，PPG 单独做成小板是合理的，不只是为了节省面积。

## 目标定义
下一代 PCB 建议目标定义如下：

1. 主板负责运算、供电、无线、执行器和大部分通用接口。
2. 小板负责贴肤光学采集，并优先保证测量质量，而不是堆功能。
3. 结构上支持一大一小双板，通过 FPC、BTB 或短排线连接。
4. 软件口径尽量沿用当前稳定主线，避免为了新板重写大量底层。

## 范围说明

### 本文覆盖
1. 主板/小板职责划分建议。
2. XIAO ESP32S3 Plus 集成方式建议。
3. 小板还能放什么、不建议放什么。
4. 当前最值得先下载的官方封装/尺寸资料。

### 本文不覆盖
1. 最终连接器型号定型。
2. 最终外壳结构件尺寸。
3. 具体原理图器件值和走线宽度。
4. PPG 算法与固件改动细节。

## 方案建议

### 方案 A：一大一小双板，主板集成 XIAO Plus，PPG 独立小板
这是当前最推荐的方案。

#### 主板建议承载
1. XIAO ESP32S3 Plus 模组本体。
2. 电池接口、充电与电源路径。
3. 3V3 电源、负载开关、必要保护电路。
4. IMU。
5. DRV2605L 与 LRA 接口。
6. 热反馈驱动。
7. RGB / 状态 LED。
8. 压力传感前端或压力接口。
9. 调试下载、Boot、Reset、测试点。
10. PPG 小板连接器。

#### PPG 小板建议承载
1. MAX30102。
2. PPG 贴肤窗口与遮光结构配合区。
3. 必要的去耦与上拉。
4. 如机械上需要，可带一颗贴近 PPG 的温度传感器或 NTC。

#### 这个方案的优点
1. 主板面积虽然增加，但功能区更清晰。
2. PPG 小板可以独立调位置、角度、贴肤压力和开窗方式。
3. 后续若更换 PPG 方案，只动小板即可。
4. 可把振动、电源和无线天线区与光学采集区拉开。

#### 这个方案的代价
1. 会多一个连接器与线缆/FPC 成本。
2. 结构件设计复杂度上升。
3. 需要更认真处理板间地、ESD 与连接可靠性。

### 方案 B：单板全集成，仅将 PPG 放在板边或探出区
这个方案只有在整机外形非常受限、且你能很好控制贴肤几何关系时才值得考虑。

主要风险：

1. PPG 与马达、热片、电源门控、电池走线过近时，噪声和结构耦合更难处理。
2. 如果后续发现贴肤位置不对，返工成本高。
3. 天线、传感窗口、充电口、马达和电池会明显争面积。

结论：

除非你已经非常确定整机外形与贴肤位置，否则不建议下一代第一版就走单板全集成。

## 小板除了 PPG 还要不要放别的

### 建议放的器件
1. 紧贴 PPG 的去耦电容和 I2C 上拉。
2. 一颗贴近皮肤侧的温度器件，前提是你未来确实要做皮温辅助特征。
3. 必要的 ID 电阻或保留焊盘，便于区分不同版本的小板。

### 谨慎放的器件
1. 小尺寸状态灯。
2. 轻量接近检测电极或佩戴检测焊盘。

前提是这些器件不会破坏遮光、不会抬高贴肤面、不会明显增加硬板面积。

### 不建议放的器件
1. 马达驱动或任何大电流执行器。
2. 热反馈器件。
3. 主充电、电源切换器件。
4. 高频无线相关器件。
5. 体积明显的按键或 USB。

结论：

小板应优先服务于“稳定贴肤测量”，不要为了利用空间把它做成第二块杂项板。

## 推荐的板间接口定义方向
建议主板与 PPG 小板至少预留以下信号：

1. 3V3
2. GND
3. I2C SDA
4. I2C SCL
5. PPG INT
6. 可选的 1 路 GPIO 或 ID

如果你计划后续加皮温器件，可再多预留 1 路 ADC 或继续走 I2C。

## MAX30102 可直接参考的公开设计文件

### 1. MAXREFDES1043
这是当前最接近“独立 MAX30102 小板”的公开参考设计。

已确认点：

1. 核心器件就是 MAX30102。
2. ADI 官方说明该设计采用单独 1.8V 逻辑电源和 3.3V LED 电源。
3. 官方页面明确提供 Design Files，包含 Schematic、PCB Layout、BOM。
4. Ultra Librarian 页面可下载多种 CAD 格式。

适用判断：

1. 如果你要画的是正式 PPG 小板，优先参考这一份。
2. 它比常见淘宝/立创商品小模块更可靠，因为电气边界和官方器件口径一致。

链接：

1. 参考设计页面：
   https://www.analog.com/en/resources/reference-designs/maxrefdes1043.html
2. 官方设计文件 ZIP：
   https://www.analog.com/media/en/reference-design-documentation/design-integration-files/maxrefdes1043-designsupport.zip
3. Ultra Librarian CAD 下载页：
   https://vendor.ultralibrarian.com/Maxim/refdes?refDsn=MAXREFDES1043

### 2. MAXREFDES117
这是一块更成熟、外围更完整的心率/血氧小板，也公开提供整套设计文件。

已确认点：

1. 核心同样使用 MAX30102。
2. 官方页面明确提供 Schematic、PCB Layout、PCB CAD、BOM、Firmware Files。
3. 板上还带电源相关外围，适合参考“完整小模组”怎么做。

适用判断：

1. 如果你不仅想看 MAX30102 本体接法，还想看一个可独立工作的完整小模块，优先下载这一份。
2. 它的板子比 MAXREFDES1043 更像“带辅助外围的功能模块”。

链接：

1. 参考设计页面：
   https://www.analog.com/en/resources/reference-designs/maxrefdes117.html
2. 官方设计文件 ZIP：
   https://www.analog.com/media/en/reference-design-documentation/design-integration-files/rd117v01_00.zip
3. Ultra Librarian CAD 下载页：
   https://vendor.ultralibrarian.com/adi/reference-design?refDsn=MAXREFDES117

### 3. 结论
1. 如果你要找“能直接用来画自定义 PPG 小板”的原理图，首推 MAXREFDES1043。
2. 如果你要找“更像成品小模块”的完整公开原理图，MAXREFDES117 更值得一起下载。
3. 目前未确认到高质量、长期可追溯、且比这两份官方设计更值得直接复用的第三方开源 MAX30102 商品小模块原理图，因此不建议优先依赖来源不明的商品页截图反推电路。

## 对当前固件口径的影响
为了最大限度复用现有工程，建议下一代板继续维持以下高优先级口径：

1. 主 I2C 继续以 GPIO5 / GPIO6 为核心。
2. RGB 继续优先保留 GPIO7 / GPIO8 / GPIO9。
3. 热反馈控制继续优先保留 GPIO2，除非硬件上有强约束必须迁移。
4. 压力采样继续优先保留 GPIO1。
5. PPG 继续挂主 I2C，若分到小板，仅改变物理位置，不改变逻辑总线归属。

## XIAO ESP32S3 Plus 封装与资料入口

### 高优先级官方资料
1. XIAO ESP32-S3 系列官方资源页：
   https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/#for-seeed-studio-xiao-esp32s3-plus
2. XIAO ESP32-S3 Plus 原理图：
   https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_V1.1_SCH_260115.pdf
3. XIAO ESP32-S3 Plus KiCad 工程：
   https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_V1.1_KiCad_260115.zip
4. XIAO Plus Base，带底部引脚引出参考板：
   https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_Plus_Base_with_botton_pad_lead_out_V1.0.zip
5. XIAO Plus Base，不带底部引脚引出参考板：
   https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_Plus_Base_without_botton_pad_lead_out_V1.0.zip
6. XIAO 系列 KiCad Footprints：
   https://files.seeedstudio.com/wiki/XIAO-KiCad-Library/New_XIAO_Series_Footprints.zip
7. XIAO 系列 KiCad Symbols：
   https://files.seeedstudio.com/wiki/XIAO-KiCad-Library/XIAO_Series_SCH_Symbols.zip
8. XIAO ESP32-S3 Plus Top DXF：
   https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/TOP.dxf
9. XIAO ESP32-S3 Plus Bottom DXF：
   https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/BOTTOM.dxf

### 这些资料怎么用
1. 如果你要直接复用官方板外形和焊盘，先打开 Plus KiCad 工程。
2. 如果你要做“母板承接 XIAO 模组”的焊盘，先重点看 Plus Base 两个参考工程。
3. 如果你要对齐板边、螺丝区、天线留空和结构边界，配合 Top/Bottom DXF 一起看。
4. 如果你要在自己工程中直接放置封装，优先用官方 KiCad Footprints，不建议自己手搓第一版封装。

## 设计约束

### 主板约束
1. XIAO 天线区域必须避免大面积铜皮、金属壳体压近和高干扰器件贴近。
2. 充电、电池、马达、热片路径应与 PPG 总线和模拟敏感区分层处理。
3. 需要保留 Boot、Reset、下载和关键测试点。

### 小板约束
1. 贴肤面要优先保证平整、遮光和稳定接触。
2. 小板周边不要堆高器件影响佩戴。
3. 连接器位置要先服务于机械装配，不要只图电气最短。

## 验收标准
1. 原理图阶段能明确区分主板和小板职责。
2. 主板上 XIAO Plus 焊接基座来源于官方资源，而不是手工猜封装。
3. PPG 小板接口定义在第一版即冻结，不随意漂移。
4. 不再出现主 I2C / 副 I2C、热控脚等口径在文档和固件之间长期并行漂移。

## 风险与待确认事项
1. 小板与主板之间采用 FPC、BTB 还是导线焊接，当前仍待定。
2. PPG 小板是否顺带集成皮温器件，取决于你是否要把皮温纳入下一阶段特征。
3. 若未来计划加 ECG，是否与 PPG 小板共板，需要单独评估，当前不建议默认合并。
4. XIAO Plus 的底部新增 IO 虽然可用，但第一版不建议为了“把 IO 用满”而拉高设计复杂度。

## 建议的下一步动作
1. 先下载并解压 XIAO ESP32S3 Plus KiCad 工程和两个 Plus Base 参考板，确认你要采用“带底部引脚引出”还是“只用标准边缘 castellation”的焊接方式。
2. 先画一页系统框图，把主板和 PPG 小板之间的接口冻结下来。
3. 先定连接器形式，再开始正式摆放 PPG 小板与主板的相对位置。
4. 若你愿意，我下一步可以直接继续帮你出一版“主板/小板原理图页级清单 + 网络命名建议”。

## 参考资料来源
1. Seeed 官方 XIAO ESP32-S3 系列资源页。
2. Seeed 官方 XIAO ESP32-S3 Plus 产品页。
3. Seeed 官方 XIAO Series OSHW 仓库说明。
4. Analog Devices MAX30102 产品页。
5. Analog Devices MAXREFDES1043 参考设计。
6. Analog Devices MAXREFDES117 参考设计。
7. 当前工程已有板级约束日志与接线文档。