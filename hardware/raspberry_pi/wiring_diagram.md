# Raspberry Pi Hardware Wiring Guide: CoachPilot Standalone Appliance

## Components Required:
1. **Raspberry Pi** (Pi Zero 2 W, Pi 4, or Pi 5)
2. **0.96" or 1.3" I2C OLED Display** (SSD1306, 128x64)
3. **USB Mini Microphone** (or I2S INMP441)
4. **Push-to-Talk Tactile Button**
5. **Status LED + 220Ω Resistor**

---

## GPIO Pinout Table

### 1. I2C SSD1306 OLED Display
| OLED Pin | Raspberry Pi Pin | Physical Pin |
| :--- | :--- | :--- |
| **VCC** | **3.3V Power** | Pin 1 |
| **GND** | **Ground** | Pin 6 |
| **SDA** | **GPIO 2 (SDA)** | Pin 3 |
| **SCL** | **GPIO 3 (SCL)** | Pin 5 |

---

### 2. Push-to-Talk Button & LED
| Component | Raspberry Pi Pin | Physical Pin |
| :--- | :--- | :--- |
| **Button Pin 1** | **GPIO 17** | Pin 11 |
| **Button Pin 2** | **Ground** | Pin 9 |
| **Status LED (+)**| **GPIO 27** (via 220Ω) | Pin 13 |
| **Status LED (-)**| **Ground** | Pin 14 |
