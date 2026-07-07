#include "led_feedback_manager.h"

#include <math.h>

namespace hold_integration {
namespace {

uint8_t redPinValue = 255;
uint8_t greenPinValue = 255;
uint8_t bluePinValue = 255;
constexpr uint8_t kRedChannel = 3;
constexpr uint8_t kGreenChannel = 4;
constexpr uint8_t kBlueChannel = 5;
constexpr uint8_t kLedOffBrightness = 0;
constexpr uint8_t kLedSolidBrightness = 255;
constexpr uint32_t kLedPwmFrequencyHz = 5000;
constexpr uint8_t kLedPwmResolutionBits = 8;
LedMode activeMode = LedMode::kOff;
GuidePhaseType activePhase = GuidePhaseType::kIdle;
uint32_t activePhaseElapsedMs = 0;
uint32_t activePhaseDurationMs = 0;
uint32_t lastToggleAtMs = 0;
bool blinkOn = false;

uint8_t clampBrightness(float value) {
  if (value < 0.0f) {
    return 0;
  }
  if (value > 255.0f) {
    return 255;
  }
  return static_cast<uint8_t>(value);
}

float smoothPulse(uint32_t nowMs, uint32_t periodMs, float minScale = 0.0f,
                  float maxScale = 1.0f) {
  const float phase = static_cast<float>(nowMs % periodMs) / static_cast<float>(periodMs);
  const float waveform = 0.5f - 0.5f * cosf(phase * 2.0f * PI);
  return minScale + waveform * (maxScale - minScale);
}

void writeRgb(uint8_t red, uint8_t green, uint8_t blue) {
  if (redPinValue != 255) {
    ledcWrite(kRedChannel, red);
  }
  if (greenPinValue != 255) {
    ledcWrite(kGreenChannel, green);
  }
  if (bluePinValue != 255) {
    ledcWrite(kBlueChannel, blue);
  }
}

}  // namespace

void ledFeedbackManagerBegin(uint8_t redPin, uint8_t greenPin, uint8_t bluePin,
                             uint32_t nowMs) {
  redPinValue = redPin;
  greenPinValue = greenPin;
  bluePinValue = bluePin;
  ledcSetup(kRedChannel, kLedPwmFrequencyHz, kLedPwmResolutionBits);
  ledcSetup(kGreenChannel, kLedPwmFrequencyHz, kLedPwmResolutionBits);
  ledcSetup(kBlueChannel, kLedPwmFrequencyHz, kLedPwmResolutionBits);
  ledcAttachPin(redPinValue, kRedChannel);
  ledcAttachPin(greenPinValue, kGreenChannel);
  ledcAttachPin(bluePinValue, kBlueChannel);
  lastToggleAtMs = nowMs;
  writeRgb(kLedOffBrightness, kLedOffBrightness, kLedOffBrightness);
}

void ledFeedbackManagerTick(uint32_t nowMs) {
  const bool shouldToggle = nowMs - lastToggleAtMs >= 400;
  if (shouldToggle) {
    lastToggleAtMs = nowMs;
    blinkOn = !blinkOn;
  }

  const uint8_t pulseSoft = clampBrightness(smoothPulse(nowMs, 1400, 0.0f, 1.0f) * 255.0f);
  const uint8_t pulseMedium = clampBrightness(smoothPulse(nowMs, 900, 0.0f, 1.0f) * 255.0f);
  const uint8_t pulseSlow = clampBrightness(smoothPulse(nowMs, 2200, 0.0f, 1.0f) * 255.0f);
  const float guideRatio = activePhaseDurationMs > 0
    ? static_cast<float>(activePhaseElapsedMs) / static_cast<float>(activePhaseDurationMs)
    : 0.0f;
  const uint8_t purpleGuide = clampBrightness((activePhase == GuidePhaseType::kInhale
    ? guideRatio
    : (1.0f - guideRatio)) * 255.0f);

  switch (activeMode) {
    case LedMode::kRedBlink:
      writeRgb(pulseMedium, kLedOffBrightness, kLedOffBrightness);
      break;
    case LedMode::kYellowSolid:
      writeRgb(kLedSolidBrightness, kLedSolidBrightness, kLedOffBrightness);
      break;
    case LedMode::kYellowBreathing:
      if (activePhase == GuidePhaseType::kInhale || activePhase == GuidePhaseType::kExhale) {
        writeRgb(purpleGuide, kLedOffBrightness, purpleGuide);
      } else if (activePhase == GuidePhaseType::kRest) {
        writeRgb(pulseSlow, pulseSlow, kLedOffBrightness);
      } else {
        writeRgb(pulseSoft, pulseSoft, kLedOffBrightness);
      }
      break;
    case LedMode::kGreenSolid:
      writeRgb(kLedOffBrightness, kLedSolidBrightness, kLedOffBrightness);
      break;
    case LedMode::kYellowBlink:
      writeRgb(pulseMedium, pulseMedium, kLedOffBrightness);
      break;
    case LedMode::kBlueSolid:
      writeRgb(kLedOffBrightness, kLedOffBrightness, kLedSolidBrightness);
      break;
    case LedMode::kErrorFastBlink:
      writeRgb(pulseMedium, kLedOffBrightness, kLedOffBrightness);
      break;
    case LedMode::kOff:
    default:
      writeRgb(kLedOffBrightness, kLedOffBrightness, kLedOffBrightness);
      break;
  }
}

void ledFeedbackManagerSetMode(LedMode mode, GuidePhaseType phase) {
  activeMode = mode;
  activePhase = phase;
}

void ledFeedbackManagerSetGuideProgress(uint32_t phaseElapsedMs, uint32_t phaseDurationMs) {
  activePhaseElapsedMs = phaseElapsedMs;
  activePhaseDurationMs = phaseDurationMs;
}

LedMode ledFeedbackManagerGetMode() { return activeMode; }

}  // namespace hold_integration