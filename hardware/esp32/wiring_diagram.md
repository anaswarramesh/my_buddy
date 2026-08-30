# Waveshare ESP32-S3 Mini / Zero (ESP32-S3FH4R2) Wiring Guide

This wiring schematic is tailored specifically for the **Waveshare ESP32-S3 Mini Development Board** (powered by the **ESP32-S3FH4R2** dual-core processor with on-chip 4MB Flash and 2MB Quad-PSRAM).

---

## 🛠️ Required Components
1. **Waveshare ESP32-S3 Mini / Zero** (ESP32-S3FH4R2)
2. **0.96" or 1.3" I2C OLED Display** (SSD1306 / SH1106, 128x64)
3. **INMP441 I2S Omnidirectional Digital Microphone Module**
4. **Tactile Push Button** (Push-to-Talk)
5. **Jumper Wires & Breadboard** (or custom PCB)

---

## 🔌 Pinout Connection Table

```
   ┌────────────────────────────────────────────────────────────┐
   │         WAVESHARE ESP32-S3 MINI (ESP32-S3FH4R2)            │
   │                                                            │
   │   [3V3]   ────────────┬─────────────┬────────────────┐     │
   │   [GND]   ─────────┐  │ (3.3V)      │ (3.3V)         │     │
   │                    │  │             │                │     │
   │   [GPIO 8]  ───────┼──┼── SDA       │                │     │
   │   [GPIO 9]  ───────┼──┼── SCL       │                │     │
   │                    │  │  (OLED)     │                │     │
   │                    │  │             │                │     │
   │   [GPIO 3]  ───────┼──┼─────────────┼── SCK (Clock)  │     │
   │   [GPIO 2]  ───────┼──┼─────────────┼── WS (LRCLK)   │     │
   │   [GPIO 1]  ───────┼──┼─────────────┼── SD (Data)    │     │
   │                    │  │             │  (INMP441)     │     │
   │                    │  └─────────────┴── VDD          │     │
   │                    └──┬─────────────┬── GND / L/R    │     │
   │                       │             │                │     │
   │   [GPIO 6]  ──────────┼── Push BTN ─┘                │     │
   │   [GPIO 10] ──[220Ω]──┼── Status LED ────────────────┘     │
   │   [GPIO 21] ──────────┴── Built-in WS2812 RGB LED (Onboard)│
   └────────────────────────────────────────────────────────────┘
```

### Detailed Pin Assignments

| Module | Pin Name | Waveshare ESP32-S3 Pin | Description |
| :--- | :--- | :--- | :--- |
| **SSD1306 OLED (128x64)** | **VCC** | **3V3** | 3.3V Power |
| | **GND** | **GND** | Ground |
| | **SDA** | **GPIO 8** | I2C Serial Data |
| | **SCL** | **GPIO 9** | I2C Serial Clock |
| **INMP441 I2S Digital Mic** | **VDD** | **3V3** | 3.3V Power |
| | **GND** | **GND** | Ground |
| | **L/R** | **GND** | Left Channel Audio Select |
| | **SD** | **GPIO 1** | I2S Serial Data In |
| | **WS** | **GPIO 2** | I2S Word Select / LRCLK |
| | **SCK** | **GPIO 3** | I2S Continuous Serial Clock |
| **Push-to-Talk Button** | **Pin 1** | **GPIO 6** | Configured with internal `INPUT_PULLUP` |
| | **Pin 2** | **GND** | Ground (pressing pulls LOW) |
| **Status LED** | **Anode (+)** | **GPIO 10** (or onboard RGB **GPIO 21**) | Active HIGH during recording |
| | **Cathode (-)**| **GND** | Ground |

---

## ⚙️ Arduino IDE Board Settings for ESP32-S3FH4R2

When compiling and uploading via Arduino IDE or PlatformIO:

- **Board:** `ESP32S3 Dev Module` (or `Waveshare ESP32-S3-Zero / Mini`)
- **USB CDC On Boot:** `Enabled` *(Crucial: ensures Serial Monitor works over native USB-C port)*
- **CPU Frequency:** `240MHz (WiFi)`
- **Flash Size:** `4MB (32Mb)`
- **Flash Mode:** `QIO 80MHz`
- **PSRAM:** `QSPI PSRAM` *(Enables the on-chip 2MB Quad PSRAM R2 chip for 10s audio buffers)*
- **Upload Mode:** `UART0 / Hardware CDC`
