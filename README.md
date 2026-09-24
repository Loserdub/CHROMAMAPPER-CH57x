# ChromaMapper - WebHID Configurator for CH57x Macropads

ChromaMapper is a premium, web-based configurator utility for CH57x hardware macropads. It allows you to program standard keys, Digital Audio Workstation (DAW) presets, multimedia keys, and system LED backlight animations directly via WebHID in your browser—without needing to install clunky desktop software.

Created and Developed by [Justin Ray](https://jray.me).

## Features

- **Direct WebHID Flashing:** Securely flash your macropad's onboard memory directly from Google Chrome or Microsoft Edge. No local software installation required.
- **DAW & Web/AI Presets:** Includes curated, pre-mapped shortcut presets for Ableton Live, Logic Pro, FL Studio, standard Web Browsers, and AI Assistants.
- **Advanced LED Studio:** Configure hardware-native LED effects like Always On Backlight, Reactive Ripple (Shock), and Instant Trigger, along with custom color presets.
- **Persistent Memory:** Key bindings and LED settings are permanently saved to the CH57x flash memory, meaning your keypad works flawlessly across any computer.
- **Custom Matrix Mapping:** Specifically optimized for 12-Key / 3-Knob layouts with automatic shifted-matrix translation under the hood.

## Getting Started

1. Connect your CH57x macropad to your computer via USB.
2. Open `chromamapper.html` in a WebHID-compatible browser (Google Chrome, Microsoft Edge, Opera).
3. Click the **Connect Device** button in the top right.
4. Select your hardware from the browser popup.
5. Click any physical representation on the virtual layout (keys or knobs) and use the right-side inspector to configure its behavior.
6. Click **Apply & Program Key** or **Write Layer LED Effect** to flash the configuration.

## Requirements

- A Chromium-based browser that supports the WebHID API (e.g., Google Chrome, Microsoft Edge). Safari and Firefox currently do not support WebHID.
- A CH57x-based hardware macropad (VID `0x1189`, PID `0x8842` / `0x8840` / `0x8890`).

## Acknowledgments

- **Author:** Justin Ray
- **Website:** [https://jray.me](https://jray.me)
- **Copyright:** © 2026 ChromaMapper. All rights reserved.
