# ESP32 Hardware Wiring Guide: CoachPilot AI Desk Companion

## Components Required:
1. **ESP32 Development Board** (ESP32-WROOM-32 or ESP32-S3)
2. **0.96" or 1.3" I2C OLED Display** (SSD1306 / SH1106, 128x64)
3. **INMP441 I2S Omnidirectional Microphone Module**
4. **Tactile Push Button** (Push-to-Talk)
5. **10kΩ Pull-up Resistor** (optional if using internal pull-up)
6. **RGB or Status LED** (optional)
7. Breadboard & Jumper wires

---

## Pinout Connections Table

### 1. SSD1306 128x64 I2C OLED Display
| OLED Pin | ESP32 Pin | Description |
| :--- | :--- | :--- |
| **VCC** | **3V3** | 3.3V Power |
| **GND** | **GND** | Ground |
| **SCL** | **GPIO 22** | I2C Clock |
| **SDA** | **GPIO 21** | I2C Data |

---

### 2. INMP441 I2S Digital Microphone
| INMP441 Pin | ESP32 Pin | Description |
| :--- | :--- | :--- |
| **VDD** | **3V3** | 3.3V Power |
| **GND** | **GND** | Ground |
| **SD** | **GPIO 32** | I2S Serial Data Out |
| **WS (L/R CLK)** | **GPIO 25** | I2S Word Select Clock |
| **SCK (BCLK)** | **GPIO 33** | I2S Bit Clock |
| **L/R** | **GND** | Left Channel Select |

---

### 3. Push-to-Talk Button & Status LED
| Component | ESP32 Pin | Configuration |
| :--- | :--- | :--- |
| **Push Button Pin 1** | **GPIO 4** | Connected to Pin with `INPUT_PULLUP` |
| **Push Button Pin 2** | **GND** | Ground (pressing pulls LOW) |
| **Status LED (+) (opt)**| **GPIO 2** | In-series with 220Ω resistor to GND |
| **Status LED (-)** | **GND** | Ground |
