# Waveshare ESP32-S3 Mini / Zero (ESP32-S3FH4R2) Wiring Guide

This wiring schematic is tailored specifically for the **Waveshare ESP32-S3 Mini Development Board** (powered by the **ESP32-S3FH4R2** dual-core processor with on-chip 4MB Flash and 2MB Quad-PSRAM).

---

## 🛠️ Required Components
1. **Waveshare ESP32-S3 Mini / Zero** (ESP32-S3FH4R2)
2. **0.96" or 1.3" I2C OLED Display** (SSD1306 / SH1106, 128x64)
3. **INMP441 I2S Omnidirectional Digital Microphone Module**
4. **TS1215CJ 12x12mm Tactile Push Button** (4-pin Plugin)
5. **220Ω Current-Limiting Resistor** (1/4W, for external Status LED)
6. **3mm / 5mm Blue or Red Status LED** (optional if using onboard RGB on GPIO 21)
7. **Jumper Wires & Breadboard** (or custom PCB)

---

## 🔌 Circuit Schematic & Wiring Diagram

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

---

## 📋 Complete Pin Assignment Table

| Module / Component | Pin / Terminal | Connects To (Waveshare ESP32-S3 Mini) | Logic / Electrical Level | Description & Wiring Details |
| :--- | :--- | :--- | :--- | :--- |
| **SSD1306 OLED (128x64)** | **VCC** | **3V3** | 3.3V DC | Power supply for display |
| | **GND** | **GND** | 0V | Common ground |
| | **SDA** | **GPIO 8** | 3.3V I2C Data | Hardware I2C Serial Data |
| | **SCL** | **GPIO 9** | 3.3V I2C Clock | Hardware I2C Serial Clock |
| **INMP441 I2S Digital Mic** | **VDD** | **3V3** | 3.3V DC | Digital microphone power |
| | **GND** | **GND** | 0V | Common ground |
| | **L/R** | **GND** | 0V (GND) | Pull to GND for Left Channel audio |
| | **SD** | **GPIO 1** | 3.3V I2S Data | I2S Serial Data Out (to ESP32) |
| | **WS** | **GPIO 2** | 3.3V I2S Clock | Word Select / Frame LRCLK |
| | **SCK** | **GPIO 3** | 3.3V I2S Clock | Continuous Serial Bit Clock |
| **TS1215CJ Push Button** | **Pin 1 (or 2)** | **GPIO 6** | Active LOW | Push-to-Talk input (firmware uses `INPUT_PULLUP`) |
| | **Pin 4 (or 3)** | **GND** | 0V | Ground connection (press closes circuit to GND) |
| **220Ω Resistor** | **Lead 1** | **GPIO 10** | 3.3V Output | In-series current-limiting resistor for LED |
| | **Lead 2** | **Status LED Anode (+)** | Forward Voltage | Connects directly to LED positive leg |
| **Status LED (External)** | **Anode (+)** | **220Ω Resistor Lead 2** | Current limited | Longer leg of LED |
| | **Cathode (-)**| **GND** | 0V | Shorter leg of LED connects to Ground |
| **WS2812 RGB LED (Onboard)** | **Data In** | **GPIO 21 (Internal)** | 3.3V Logic | Built-in RGB on Waveshare board (no external resistor needed) |

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
