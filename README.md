# CoachPilot AI — Intelligent Daily Productivity & Coaching Assistant
### *With Standalone Physical Desk Companion Support (ESP32 / Raspberry Pi + OLED Display + Voice)*

CoachPilot is an AI-powered daily assistant and executive coach that syncs calendar commitments, captures raw voice notes, and separates immediate tasks from big ideas. For big ideas, it acts as a proactive coach: evaluating feasibility, breaking ideas into $\le 15$-minute micro-ignition steps, pushing execution, and automatically scheduling those steps into open slots on lighter calendar days.

---

## 🖥️ Standalone Physical Product: ESP32 vs. Raspberry Pi

To create a physical desk companion product that **does not require launching from your laptop every time**, you have two architectural options:

| Feature | Option A: Raspberry Pi (Zero 2 W / 4 / 5) | Option B: ESP32 (ESP32-S3 / WROOM) |
| :--- | :--- | :--- |
| **Independence** | **100% Self-Contained Standalone** (Backend + DB + Display + Mic all run on the device). | **Ultra-Low-Power IoT Client** (Microcontroller connects to a cloud-hosted backend over Wi-Fi). |
| **Laptop Needed?** | ❌ **No laptop ever.** Plugs into wall power, boots on startup via `systemd`. | ❌ **No laptop needed** if backend is deployed to a free cloud host (Render, Railway, Fly.io, or AWS). |
| **Hardware Cost** | \$15 – \$45 (Pi Zero 2W or Pi 4) | \$5 – \$10 (ESP32-S3 board) |
| **Power Draw** | 2W – 5W | < 0.5W (Instant sleep/wake) |
| **Audio Ingestion** | Plug-and-play USB Mini Mic or I2S mic | INMP441 I2S Digital Microphone |
| **Display** | 0.96" / 1.3" I2C OLED (SSD1306) or HDMI/Touchscreen | 0.96" / 1.3" I2C OLED (SSD1306 / SH1106) |
| **Best For** | **Fastest standalone commercial prototype** — zero cloud configuration needed. | **Mass production & commercial IoT hardware** — low BOM cost and battery-friendly. |

---

## 🛠️ Hardware Schematics & Wiring

### 1. I2C SSD1306 OLED (128x64)
- **VCC** $\rightarrow$ 3.3V
- **GND** $\rightarrow$ GND
- **SDA** $\rightarrow$ ESP32 `GPIO 21` / Raspberry Pi `GPIO 2 (Pin 3)`
- **SCL** $\rightarrow$ ESP32 `GPIO 22` / Raspberry Pi `GPIO 3 (Pin 5)`

### 2. Voice Input (Push-to-Talk)
- **Push Button** $\rightarrow$ ESP32 `GPIO 4` / Raspberry Pi `GPIO 17 (Pin 11)` (Internal Pull-Up enabled)
- **I2S Microphone (INMP441 for ESP32)**:
  - `SCK` $\rightarrow$ `GPIO 33`
  - `WS` $\rightarrow$ `GPIO 25`
  - `SD` $\rightarrow$ `GPIO 32`
  - `L/R` $\rightarrow$ GND (Left channel)

---

## 🚀 How to Run: Standalone Hardware Modes

### Mode A: Raspberry Pi Standalone Appliance (All-in-One)
On your Raspberry Pi:
```bash
# 1. Clone repository onto Raspberry Pi
git clone https://github.com/your-repo/coach-pilot.git
cd coach-pilot

# 2. Run backend in background
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 3. Setup hardware drivers and auto-start on boot
cd ../hardware/raspberry_pi
chmod +x setup_pi.sh
./setup_pi.sh
```
*The device will now automatically boot, sync your Google Calendar, show your daily density and tasks on the OLED, and record thoughts whenever you press the physical button!*

---

### Mode B: ESP32 IoT Desk Companion
1. Open `hardware/esp32/CoachPilot_ESP32.ino` in the **Arduino IDE** or **PlatformIO**.
2. Install required libraries via Library Manager:
   - `Adafruit SSD1306`
   - `Adafruit GFX Library`
   - `ArduinoJson` (v7)
3. Set your Wi-Fi credentials and backend server URL in `CoachPilot_ESP32.ino`:
   ```cpp
   const char* WIFI_SSID = "Your_WiFi_Network";
   const char* WIFI_PASS = "Your_WiFi_Password";
   const char* SERVER_BASE = "https://your-cloud-backend.onrender.com"; // or local IP
   ```
4. Connect your ESP32 via USB and click **Upload**.

---

## 📂 Project Structure

```
coach-pilot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_hardware.py   # Compact OLED JSON & direct binary voice upload
│   │   │   ├── routes_voice.py      # Voice ingestion & Whisper transcription
│   │   │   ├── routes_ideas.py      # Idea backlog & Prompt B decomposition
│   │   │   ├── routes_tasks.py      # Actionable task management & auto-scheduling
│   │   │   ├── routes_calendar.py   # Calendar sync & 7-day density endpoint
│   │   │   ├── routes_synthesis.py  # Morning synthesis & coaching nudges
│   │   │   └── routes_nlp.py        # Dynamic NLP rescheduling parser
│   │   ├── models/                  # SQLAlchemy / PostgreSQL Database Models
│   │   ├── schemas/                 # Pydantic v2 validation & LLM output schemas
│   │   ├── services/                # DensityService, LLMService, SchedulerService
│   │   ├── database.py              # SQLite / Supabase database connection
│   │   └── main.py                  # FastAPI server & static preview dashboard
│   ├── static/                      # Web dashboard preview
│   └── tests/                       # Automated Pytest Suite (11 passing tests)
├── hardware/                        # Dedicated Physical Hardware Implementations
│   ├── esp32/
│   │   ├── CoachPilot_ESP32.ino     # C++ Arduino firmware (I2S Mic + SSD1306 OLED)
│   │   ├── platformio.ini           # PlatformIO project configuration
│   │   └── wiring_diagram.md        # Pinout wiring guide for ESP32 + INMP441 + OLED
│   └── raspberry_pi/
│       ├── device_app.py            # Standalone Pi OLED UI + Mic recording daemon
│       ├── coachpilot.service       # Systemd auto-start boot service
│       ├── setup_pi.sh              # One-command Pi installer
│       └── wiring_diagram.md        # GPIO wiring guide for Raspberry Pi
├── frontend/                        # Cross-Platform React Native (Expo) Client
└── README.md
```

---

## 🔌 Connecting External Calendars

### 1. Google Calendar Integration (OAuth 2.0)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Calendar API**.
3. Create **OAuth 2.0 Client Credentials** (Web Application).
4. Set Authorized Redirect URI to: `http://localhost:8000/api/calendar/google/callback`.
5. Add credentials to `coach-pilot/backend/.env`:
   ```env
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

### 2. Apple Calendar Integration (CalDAV)
1. Generate an **App-Specific Password** at [appleid.apple.com](https://appleid.apple.com/).
2. Add credentials to `coach-pilot/backend/.env`:
   ```env
   CALDAV_URL=https://caldav.icloud.com
   CALDAV_USERNAME=your_apple_id@icloud.com
   CALDAV_PASSWORD=your_app_specific_password
   ```

---

## 🧪 Testing Backend Locally
```bash
cd coach-pilot/backend
PYTHONPATH=. .venv/bin/pytest -v
```
