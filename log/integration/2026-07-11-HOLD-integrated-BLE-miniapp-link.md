# 2026-07-11 HOLD integrated BLE miniapp link

## Goal

- Fix miniapp connected-but-no-data.
- Fix breath feedback command having no hardware response.
- Fix calibration having no visible state change.
- Keep homepage as the user-facing control surface and debug page as diagnosis only.

## First principles diagnosis

The working chain must have all four links:

1. Hardware advertises a stable BLE service.
2. Miniapp discovers the service and subscribes to a notify characteristic with CCCD.
3. Hardware emits parseable packets on notify.
4. Miniapp writes commands to a writable command characteristic, and firmware turns those commands into DRV2605 state.

The screenshot symptom "收到无法解析的通知" showed link 2 was partly alive, but link 3 and link 4 were not an agreed protocol. Previous iterations also emphasized BLE2902/CCCD and direct miniapp-to-hardware BLE first, before cloud.

## Changes

- `src/xiao_esp32s3_full_smoke_test/main.cpp`
  - Added BLE service `19b10010-e8f2-537e-4f6c-d104768a1214`.
  - Added notify characteristic `19b10011-e8f2-537e-4f6c-d104768a1214` with `BLE2902`.
  - Added command characteristic `19b10013-e8f2-537e-4f6c-d104768a1214` with write and write-no-response.
  - Emits compact JSON telemetry every 500 ms: type, device id, heart, beat, motion, phase, IMU model, haptic, breath, calibration.
  - Handles `breath_start`, `breath_stop`, `calibrate_start`.
  - Breath mode drives DRV2605 RTP with a rising/falling envelope.
  - Calibration mode pulses DRV2605 and reports `calibration_started` / `calibration_done`.
  - Fixed calibration race: start time is written before `calibrationRunning=true`.

- `web/utils/ble-protocol.js`
  - Centralized BLE UUIDs.
  - Parses JSON, key-value text, and binary fallback packets.
  - Normalizes short firmware fields (`br/hr/bt/mo/ph/hp/bg/cg`) to miniapp fields.
  - Adds Chinese labels for motion and guidance phase.

- `web/pages/home/*`
  - Homepage now performs real BLE scan/connect/subscribe/write.
  - Homepage shows connection, calibration, breath guidance, live metrics, raw packet summary.
  - Main controls: scan/connect, disconnect, clear cache, breath guide, base calibration.

- `web/pages/index/*`
  - Debug page now shares the same BLE protocol and command path.
  - Keeps raw/hex diagnostics for protocol inspection.

## Verification

- Backed up workspace to `D:\Desktop\HOLD-main\backup-20260711-114424`.
- Built firmware:
  - `python -m platformio run -e xiao_esp32s3_full_smoke_test`
  - Result: success.
- Uploaded firmware to USB serial `COM13`.
  - Board: ESP32-S3, MAC `e0:72:a1:fa:0f:5c`.
  - Result: success.
- Serial boot check:
  - IMU `MPU6500` OK.
  - MAX30102 OK.
  - Pressure sensor OK.
  - DRV2605 OK.
  - BLE advertising `HOLD-INTEGRATED`.
- PC BLE scan:
  - Found `HOLD-INTEGRATED`.
  - Service UUID present.
- PC BLE connect/notify/write:
  - Received telemetry JSON.
  - `calibrate_start` produced `calibration_started`, `cg=1`, `ph=calibrating`.
  - `breath_start` produced `breath_started`, `bg=1`, `ph=inhale`.
  - `breath_stop` produced `breath_stopped`, `bg=0`, `ph=idle`.
- Miniapp JS checks:
  - `node --check web/utils/ble-protocol.js`
  - `node --check web/pages/home/index.js`
  - `node --check web/pages/index/index.js`
  - Result: success.

## Remaining risk

- Respiration BPM is currently `0` in the integrated smoke firmware because the production respiration estimator is not yet merged into this entrypoint.
- Physical vibration amplitude was verified by command/state path and DRV2605 RTP writes, but tactile strength still needs human confirmation on the worn prototype.
- WeChat DevTools is open for phone-side testing; PC BLE already validated the underlying BLE protocol.
