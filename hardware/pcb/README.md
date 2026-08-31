# HOLD PCB 工程

本目录集中保存 HOLD 主板的可编辑工程、Gerber 生产资料和阶段性网表。

## 目录说明

- `easyeda/Hold.eprj2`：嘉立创 EDA 专业版工程，后续原理图和 PCB 修改以此文件为入口。
- `gerber/current/Gerber_PCB2_2026-08-28.zip`：当前 Gerber 导出包。
- `gerber/archive/DO_NOT_FABRICATE_Hold_PCB2_20260816_010438.zip`：历史实际下单包，包含额外过孔并曾导致 `SW_OUT` 与 `GND` 短路，仅供故障追溯，禁止生产。
- `netlist/Netlist_Schematic1_2026-07-16.net`：阶段性原理图网表。

## 使用约束

1. 修改 PCB 前备份 `Hold.eprj2`，并确认使用嘉立创 EDA 专业版打开。
2. 每次下单都应从当前源工程重新导出 Gerber，不复用 `archive/` 中的文件。
3. 导出后检查顶层、底层、钻孔和飞针网络，重点确认 `SW_OUT`、`GND`、`3V3`、`BAT`、`SDA` 与 `SCL` 未发生意外连接。
4. 当前 Gerber 仅代表阶段性导出结果；生产前仍须完成原理图 ERC、PCB DRC 和在线 Gerber 预览。

## 已知历史问题

历史下单包相对后续设计额外包含多颗镀铜孔，其中 MPU6050 附近的异常铜连接曾将 `SW_OUT` 接入 `GND`。归档文件名已加入 `DO_NOT_FABRICATE`，避免误用。