# CoachPilot AI (My Buddy) — ESP32 Physical AI Desk Companion & Productivity Engine

**CoachPilot AI** is a physical hardware desk assistant powered by the **ESP32** microcontroller, an **I2S digital microphone**, and an **OLED display**. It syncs bi-directionally with your Google and Apple calendars, captures unfiltered voice notes, evaluates the feasibility of your big ideas, generates frictionless $\le 15$-minute micro-ignition tasks, and automatically schedules them into low-density calendar slots.

---

## 🌟 How the ESP32 Desk Companion Works

```
 ┌─────────────────────────────────────────────────────────┐
 │               PHYSICAL DESK COMPANION (ESP32)           │
 │                                                         │
 │  ┌────────────────┐   ┌────────────────┐   ┌─────────┐  │
 │  │ 0.96" I2C OLED │   │ INMP441 I2S Mic│   │ Push-To-│  │
 │  │  (128x64 Pix)  │   │  (16kHz/16-bit)│   │  Talk   │  │
 │  └───────▲────────┘   └───────▲────────┘   └───▲─────┘  │
 │          │ (I2C)              │ (I2S DMA)      │ (GPIO) │
 │  ┌───────┴────────────────────┴────────────────┴──────┐ │
 │  │             ESP32-S3 / ESP32-WROOM-32              │ │
 │  └────────────────────────────┬───────────────────────┘ │
 └───────────────────────────────┼─────────────────────────┘
                                 │ Wi-Fi (HTTPS REST / JSON)
                                 ▼
 ┌─────────────────────────────────────────────────────────┐
 │       24/7 CLOUD-HOSTED BACKEND (No Laptop Needed)      │
 │                                                         │
 │  ┌──────────────────┐  ┌─────────────────────────────┐  │
 │  │  FastAPI Backend │  │   Supabase / SQLite DB      │  │
 │  └────────▲─────────┘  └──────────────▲──────────────┘  │
 │           │                           │                 │
 │  ┌────────┴─────────┐  ┌──────────────┴──────────────┐  │
 │  │ Whisper STT API  │  │ Google / Apple Calendar API │  │
 │  │ Gemini / GPT-4o  │  │ (Bi-directional Sync)       │  │
 │  └──────────────────┘  └─────────────────────────────┘  │
 └─────────────────────────────────────────────────────────┘
```

1. **Daily Morning Synthesis on OLED**: At your desk, the OLED display shows today's date, your **Cognitive Schedule Density %**, upcoming meetings count, the highest-priority **Step 1 Micro-Ignition Task**, and an AI executive coaching nudge.
2. **Push-to-Talk Voice Capture**: Hold down the physical button to speak an idea, errand, or calendar command. The ESP32 records high-definition 16kHz audio using the INMP441 I2S microphone with a live VU-meter animation on the OLED screen.
3. **Idea Feasibility & Coaching Engine**: Releasing the button sends the audio directly to the cloud backend. Whisper transcribes the voice, Prompt A evaluates venture feasibility (1-100), and Prompt B breaks it down into a 15-minute starter action.
4. **Smart Density Auto-Placement**: The system calculates schedule density across the upcoming 7 days and automatically books your starter task into an open **Green Focus Day** without overloading your schedule.

---

## 🛠️ Hardware Bill of Materials (BOM)

| Component | Part / Spec | Purpose | Est. Cost |
| :--- | :--- | :--- | :--- |
| **Microcontroller** | **ESP32-S3-DevKitC-1** (or ESP32-WROOM-32) | Wi-Fi processing, I2S DMA, OLED rendering | \$3.50 – \$5.00 |
| **Display** | **0.96" or 1.3" I2C OLED (SSD1306)** | 128x64 graphic screen for daily synthesis | \$2.00 – \$3.00 |
| **Microphone** | **INMP441 I2S Omnidirectional Mic** | 24-bit digital audio capture with high SNR | \$1.20 – \$2.00 |
| **Button** | **12x12mm Tactile Push Button** | Push-to-Talk actuation switch | \$0.20 |
| **Status LED** | **3mm / 5mm Blue or RGB LED** | Recording / upload indicator | \$0.10 |
| **Resistor** | **220Ω 1/4W Resistor** | Current limiter for status LED | \$0.05 |
| **Power** | **USB-C Cable + 5V/1A Wall Adapter** | Continuous desk power (or 3.7V LiPo battery) | \$2.00 |
| **Total BOM** | | | **\$9.00 – \$12.00** |

---

## 🔌 Circuit Schematic & Wiring Pinout

```
   ┌────────────────────────────────────────────────────────┐
   │                       ESP32 PINOUT                     │
   │                                                        │
   │   [3.3V]  ────────────┬─────────────┬────────────┐     │
   │   [GND]   ─────────┐  │ (3.3V)      │ (3.3V)     │     │
   │                    │  │             │            │     │
   │   [GPIO 21] ───────┼──┼── SDA       │            │     │
   │   [GPIO 22] ───────┼──┼── SCL       │            │     │
   │                    │  │  (OLED)     │            │     │
   │                    │  │             │            │     │
   │   [GPIO 33] ───────┼──┼─────────────┼── SCK      │     │
   │   [GPIO 25] ───────┼──┼─────────────┼── WS       │     │
   │   [GPIO 32] ───────┼──┼─────────────┼── SD       │     │
   │                    │  │             │  (INMP441) │     │
   │                    │  └─────────────┴── VDD      │     │
   │                    └──┬─────────────┬── GND/L/R  │     │
   │                       │             │            │     │
   │   [GPIO 4]  ──────────┼── Push BTN ─┘            │     │
   │   [GPIO 2]  ──[220Ω]──┼── Status LED ────────────┘     │
   └───────────────────────┴────────────────────────────────┘
```

### Pin Connections Table

| Module | Pin | ESP32 Pin | Description |
| :--- | :--- | :--- | :--- |
| **SSD1306 OLED (128x64)** | **VCC** | **3V3** | 3.3V Power |
| | **GND** | **GND** | Ground |
| | **SDA** | **GPIO 21** | I2C Data Line |
| | **SCL** | **GPIO 22** | I2C Clock Line |
| **INMP441 I2S Mic** | **VDD** | **3V3** | 3.3V Power |
| | **GND** | **GND** | Ground |
| | **L/R** | **GND** | Left Channel Select |
| | **SD** | **GPIO 32** | I2S Serial Data Out |
| | **WS** | **GPIO 25** | I2S Word Select Clock |
| | **SCK** | **GPIO 33** | I2S Bit Clock |
| **Push Button** | **Pin 1** | **GPIO 4** | Configured with `INPUT_PULLUP` |
| | **Pin 2** | **GND** | Ground (pressing pulls LOW) |
| **Status LED** | **Anode (+)** | **GPIO 2** | Via 220Ω resistor |
| | **Cathode (-)**| **GND** | Ground |

---

## 💻 OLED Visual UI Layouts

```
1. Idle Dashboard                  2. Recording State (Held)        3. AI Coaching Result
+--------------------------------+ +--------------------------------+ +--------------------------------+
| Mon Sep 01          LIGHT [35%]| |        >> RECORDING <<         | | STATUS: IDEA (88% Feasible)    |
|--------------------------------| |                                | |--------------------------------|
| [ 35% ]  Mtgs: 2               | |     |||| | | |||||| | |||      | | Starter Action:                |
| [LOAD ]  Step 1 (Micro):       | |                                | | Draft 3 value propositions     |
|          Draft 3 value ...     | |    Speak thought / idea...     | |--------------------------------|
|--------------------------------| +--------------------------------+ | Feasibility: 88%               |
| GREEN DAY: Launch ideas!       |                                    +--------------------------------+
+--------------------------------+
```

---

## ⚡ Flashing the ESP32 Firmware

1. Open [`hardware/esp32/CoachPilot_ESP32.ino`](hardware/esp32/CoachPilot_ESP32.ino) in **Arduino IDE** or **VS Code PlatformIO**.
2. Install the required libraries in Arduino IDE (*Sketch $\rightarrow$ Include Library $\rightarrow$ Manage Libraries*):
   - `Adafruit SSD1306`
   - `Adafruit GFX Library`
   - `ArduinoJson` (v7)
3. Set your Wi-Fi credentials and cloud server URL:
   ```cpp
   const char* WIFI_SSID = "YOUR_WIFI_SSID";
   const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";
   const char* SERVER_BASE = "https://your-backend-app.onrender.com"; // or local IP http://192.168.x.x:8000
   ```
4. Connect the ESP32 board via USB, select **ESP32-S3 Dev Module** (or **ESP32 Dev Module**), and click **Upload**.

---

## ☁️ 24/7 Cloud Backend Deployment (No Laptop Needed)

Deploy the backend to **Render.com** (or Fly.io / Railway) for free in 3 minutes so your ESP32 works 24/7 independently:

1. Log in to [Render.com](https://render.com/) and click **New + $\rightarrow$ Web Service**.
2. Connect your GitHub repository.
3. Configure:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add your API Keys in **Environment Variables**:
   - `OPENAI_API_KEY`: `your_openai_key`
   - `GEMINI_API_KEY`: `your_gemini_key`
   - `LLM_PROVIDER`: `gemini` (or `openai`)
5. Copy your live Render URL (e.g., `https://coachpilot-backend.onrender.com`) and paste it into `SERVER_BASE` in the ESP32 firmware.

---

## 📂 Repository Structure

```
coach-pilot/
├── hardware/
│   └── esp32/
│       ├── CoachPilot_ESP32.ino     # Production C++ firmware (I2S DMA + SSD1306 OLED)
│       ├── HARDWARE_DESIGN.md       # Complete hardware engineering specification
│       ├── wiring_diagram.md        # Pinout schematic and connection table
│       └── platformio.ini           # PlatformIO project configuration
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_hardware.py   # Compact OLED JSON & raw binary audio ingestion
│   │   │   ├── routes_voice.py      # Voice ingestion & Whisper transcription
│   │   │   ├── routes_ideas.py      # Idea feasibility backlog & Prompt B decomposition
│   │   │   ├── routes_tasks.py      # Actionable task management & auto-scheduling
│   │   │   ├── routes_calendar.py   # Calendar sync & 7-day density map
│   │   │   ├── routes_synthesis.py  # Morning synthesis & coaching nudges
│   │   │   └── routes_nlp.py        # Dynamic NLP rescheduling parser
│   │   ├── models/                  # SQLAlchemy / PostgreSQL Database Models
│   │   ├── schemas/                 # Pydantic v2 schemas and prompt validation
│   │   ├── services/                # DensityService, LLMService, SchedulerService, WhisperService
│   │   ├── database.py              # SQLite / Supabase connection
│   │   └── main.py                  # FastAPI application & static preview server
│   ├── static/                      # Interactive Web Preview Dashboard
│   ├── tests/                       # Automated Pytest Suite (11 passing tests)
│   ├── Dockerfile                   # Cloud container definition
│   ├── render.yaml                  # 1-click cloud deployment specification
│   └── requirements.txt
├── frontend/                        # Cross-Platform React Native (Expo) Mobile App
│   ├── src/
│   │   ├── components/              # DensityGauge, VoiceCaptureButton, StarterTaskCard, IdeaCard
│   │   ├── screens/                 # DashboardScreen, IdeasScreen, CalendarDensityScreen
│   │   ├── services/                # API client
│   │   └── types/                   # TypeScript interfaces
│   └── App.tsx
└── README.md
```

---

## 🔌 Connecting Google Calendar & Apple Calendar

### 1. Google Calendar (OAuth 2.0)
1. Go to [Google Cloud Console](https://console.cloud.google.com/) and enable the **Google Calendar API**.
2. Create **OAuth 2.0 Client Credentials** (Web Application).
3. Set Redirect URI to `https://your-domain.com/api/calendar/google/callback`.
4. Add to `backend/.env`:
   ```env
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

### 2. Apple Calendar (CalDAV)
1. Generate an **App-Specific Password** at [appleid.apple.com](https://appleid.apple.com/).
2. Add to `backend/.env`:
   ```env
   CALDAV_URL=https://caldav.icloud.com
   CALDAV_USERNAME=your_apple_id@icloud.com
   CALDAV_PASSWORD=your_app_specific_password
   ```

---

## 🧪 Local Backend Testing

Run the automated test suite locally:
```bash
cd backend
PYTHONPATH=. .venv/bin/pytest -v
```
