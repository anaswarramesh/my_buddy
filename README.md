# CoachPilot AI (My Buddy) — Waveshare ESP32-S3 Mini AI Desk Companion & Productivity Engine

**CoachPilot AI** is a physical hardware desk assistant powered by the **Waveshare ESP32-S3 Mini Development Board, Based on ESP32-S3FH4R2 Dual-Core Processor, 240MHz Running Frequency, 2.4GHz Wi-Fi & Bluetooth 5**, paired with an **INMP441 I2S digital microphone** and an **SSD1306 OLED display**. It syncs bi-directionally with your Google and Apple calendars, captures unfiltered voice notes, evaluates the feasibility of big ideas, generates frictionless $\le 15$-minute micro-ignition tasks, and automatically schedules them into low-density calendar slots.

---

## 🌟 End-to-End System Architecture

```
 ┌─────────────────────────────────────────────────────────────────┐
 │       PHYSICAL DESK COMPANION (WAVESHARE ESP32-S3 MINI)         │
 │                                                                 │
 │  ┌────────────────┐   ┌────────────────┐   ┌─────────────────┐  │
 │  │ 0.96" I2C OLED │   │ INMP441 I2S Mic│   │ TS1215CJ Tactile│  │
 │  │  (128x64 Pix)  │   │  (16kHz/16-bit)│   │ Push-To-Talk BTN│  │
 │  └───────▲────────┘   └───────▲────────┘   └────────▲────────┘  │
 │          │ (I2C)              │ (I2S DMA)           │ (GPIO)    │
 │  ┌───────┴────────────────────┴─────────────────────┴─────────┐ │
 │  │ Waveshare ESP32-S3 Mini (ESP32-S3FH4R2 240MHz Dual-Core)   │ │
 │  │ 4MB Flash + 2MB On-Chip Quad-SPI PSRAM (R2)                │ │
 │  └────────────────────────────┬───────────────────────────────┘ │
 └───────────────────────────────┼─────────────────────────────────┘
                                 │ Wi-Fi (HTTPS REST / JSON)
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │       24/7 CLOUD-HOSTED BACKEND (No Laptop Needed)              │
 │                                                                 │
 │  ┌──────────────────┐  ┌─────────────────────────────────────┐  │
 │  │  FastAPI Backend │  │   Supabase / SQLite DB              │  │
 │  └────────▲─────────┘  └──────────────▲──────────────────────┘  │
 │           │                           │                         │
 │  ┌────────┴─────────┐  ┌──────────────┴──────────────────────┐  │
 │  │ Whisper STT API  │  │ Google / Apple Calendar API         │  │
 │  │ Gemini / GPT-4o  │  │ (Bi-directional Sync)               │  │
 │  └──────────────────┘  └─────────────────────────────────────┘  │
 └─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 The AI & LLM Intelligence Pipeline

CoachPilot uses a multi-stage cognitive pipeline that converts uncompressed voice recordings into structured, scheduled calendar commitments and executive coaching insights.

```mermaid
flowchart TD
    A[Raw Audio: 16kHz WAV from ESP32-S3] --> B[Whisper STT / Speech-to-Text]
    B --> C[Clean Raw Transcript Text]
    
    C --> D{Prompt A: Cognitive Triage & Feasibility Coach}
    
    D -->|Immediate Errand| E[IMMEDIATE_TASK: Log directly to DB]
    D -->|Calendar Modification| F[CALENDAR_COMMAND: Route to Prompt C]
    D -->|Ambitious Concept| G[BIG_IDEA: Feasibility & Friction Analysis]
    
    G --> H[Prompt B: Behavioral Step Decomposition]
    H --> I[Step 1: <=15m Micro-Ignition Action]
    H --> J[Steps 2-4: Progressive Execution Milestones]
    
    I --> K[Prompt C: Schedule Density Allocator]
    K --> L[Calculate 7-Day Density D(d)]
    L --> M[Auto-Book into Green Day Focus Slot]
    M --> N[Bi-directional Write to Google/Apple Calendar]
    N --> O[Instant OLED Feedback on ESP32-S3]
```

---

### 🚦 How Prompts A, B, and C Are Identified & Routed

The system orchestrates Prompts A, B, and C through a **Hierarchical Decision Pipeline** in the backend:

```mermaid
flowchart TD
    A[Raw Voice Ingestion from ESP32-S3 / Mobile] --> B[Whisper STT: Audio to Text]
    B --> C[Always Ingest into PROMPT A: Triage & Intent Classifier]
    
    C -->|Intent Classification Result| D{What is the Classification?}
    
    D -->|BIG_IDEA / HYBRID| E[1. Save Idea with Feasibility & Friction Scores]
    E --> F[2. Automatically Chain to PROMPT B: Step Decomposition]
    F --> G[3. Automatically Chain to PROMPT C: Green Day Auto-Placement]
    
    D -->|IMMEDIATE_TASK| H[Log task into DB -> Schedule into Next Open Slot]
    
    D -->|CALENDAR_COMMAND| I[Direct Hand-off to PROMPT C: Dynamic NLP Rescheduler]
    
    J[Explicit User NLP Chat Command e.g. /api/nlp/command] --> I
```

#### 1. How Prompt A is Identified (The Front-Door Gateway)
- **Trigger:** *Every single raw voice recording or thought enters Prompt A first.*
- **Classification Engine:** Evaluates semantic markers and vocabulary:
  - **`BIG_IDEA`**: Ambitious vision, startup concept, new product, or open-ended thought (*"I want to build an automated legal client intake bot..."*).
  - **`IMMEDIATE_TASK`**: Concrete errand or logistical requirement (*"Email Sarah the revised budget by 3 PM"*).
  - **`CALENDAR_COMMAND`**: Time manipulation verbs (*"Clear Thursday afternoon", "Move my 2 PM meeting"*).
  - **`HYBRID`**: Contains both a strategic thought and an immediate action.

#### 2. How Prompt B is Identified (Conditional Automatic Chaining)
- **Trigger:** *Triggered automatically whenever Prompt A outputs `BIG_IDEA` or `HYBRID` (or on-demand via `/api/ideas/{id}/decompose`).*
- **Action:** Ingests the idea title, feasibility rating, and obstacle diagnosis to generate 3–5 sequential milestones where **Step 1 is strictly a $\le 15$-minute Micro-Ignition Action** (zero activation friction).

#### 3. How Prompt C is Identified (Intent Routing & Auto-Scheduling)
- **Trigger Scenario 1 (Natural Language Rescheduling):** Triggered when Prompt A detects `CALENDAR_COMMAND` or the user enters a prompt in the dynamic NLP command bar. Prompt C shifts conflicted blocks and floats tasks to low-density days.
- **Trigger Scenario 2 (Smart Auto-Placement):** Triggered automatically after Prompt B produces the Step 1 ignition task. The backend's `SchedulerService` evaluates 7-day density ($D(d)$) and calls Prompt C to book the task into the earliest **Green Focus Day** ($D < 0.45$).

#### Summary Table: Prompts A, B, and C

| Prompt | Role | Input Data | Trigger Condition | Output & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Prompt A** | **Triage & Feasibility Coach** | Transcribed voice text | **Always** on any incoming voice note | Classification (`BIG_IDEA`, `IMMEDIATE_TASK`, `CALENDAR_COMMAND`) + Feasibility (1-100) & Coaching Verdict |
| **Prompt B** | **Behavioral Decomposer** | Idea title, summary, obstacle | Automatically chained on **`BIG_IDEA`** | 3–5 sequential tasks with **Step 1 as a $\le 15$-min Micro-Ignition action** |
| **Prompt C** | **Density Allocator & Rescheduler** | 7-day density snapshots + NLP command + tasks | Triggered on **`CALENDAR_COMMAND`**, NLP command bar, or auto-placement | Rebalanced calendar slots, floated tasks, and Google/Apple Calendar event writes |

---

### Step 1: Speech-to-Text (STT) Ingestion
- When you hold the TS1215CJ physical button on the Waveshare ESP32-S3 Mini, the **INMP441 I2S microphone** streams 16,000 samples/sec at 16-bit mono depth into the **2MB on-chip PSRAM buffer**.
- Releasing the button sends the binary WAV stream to `/api/hardware/voice-upload`.
- The backend passes the audio payload to **OpenAI Whisper (`whisper-1`)** or **Google Gemini Multimodal Audio**, converting messy, unfiltered spoken thoughts into clean natural text.

---

### Step 2: Prompt A — Input Triage, Classification & Feasibility Coaching
**Prompt A** acts as an Executive Coach. It analyzes the raw transcript and categorizes it into one of four intent classes:

1. **`BIG_IDEA`**: An entrepreneurial, creative, or technical vision requiring multiple execution steps.
2. **`IMMEDIATE_TASK`**: A single-action errand or logistical item (*"Email Sarah the revised budget by 3 PM"*).
3. **`CALENDAR_COMMAND`**: A directive to clear, shift, or reschedule time (*"Clear my Thursday afternoon"*).
4. **`HYBRID`**: A thought containing both an idea and an immediate task.

#### Feasibility & Friction Evaluation Engine (For Big Ideas)
For any `BIG_IDEA`, Prompt A computes:
- **Feasibility Score ($1–100$)**: Realistic execution probability considering real-world constraints.
- **Impact Potential ($1–100$)**: Strategic upside and value creation.
- **Friction Score ($1–100$)**: Psychological, technical, or capital barrier causing procrastination.
- **Primary Obstacle**: The exact emotional or technical bottleneck blocking progress.
- **Coaching Verdict**: A blunt, 2-sentence reality check and actionable challenge.

#### Prompt A Output Schema (Structured JSON)
```json
{
  "classification": "BIG_IDEA",
  "confidence": 0.96,
  "idea_analysis": {
    "title": "AI Client Intake for Law Firms",
    "category": "business",
    "summary": "Voice-enabled intake bot that summarizes client claims before consultation calls.",
    "feasibility_score": 88,
    "impact_score": 92,
    "friction_score": 40,
    "primary_obstacle": "Over-engineering compliance before validating attorney interest.",
    "coaching_verdict": "High commercial demand with standard tech stack. Don't build custom models before closing 2 pilot test firms with a 1-page script.",
    "nudge_strategy": "Draft 5 core intake questions in Apple Notes and send to 1 attorney contact today."
  },
  "extracted_tasks": [],
  "coaching_nudge": "This idea has strong potential. Let's knock out the 10-minute starter action before lunch!"
}
```

---

### Step 3: Prompt B — Micro-Ignition Task Decomposition
To prevent task paralysis, **Prompt B** decomposes the approved idea into 3–5 progressive milestones, strictly enforcing the **Micro-Ignition Rule**:
- **Step 1 MUST be a Micro-Ignition Action ($\le 15$ mins, Friction: `micro`)**: Zero complex setup required. Provides instant emotional momentum.
- Each subsequent step is classified by **Energy Type** (`creative`, `deep_focus`, `admin`, `low_energy`) and **Friction Level** (`micro`, `easy`, `medium`, `deep_work`).

#### Prompt B Output Schema (Structured JSON)
```json
{
  "tasks": [
    {
      "sequence_order": 1,
      "title": "Draft 5 core intake questionnaire prompts (10 mins)",
      "description": "Write down the exact 5 questions an intake bot must ask incoming personal injury leads.",
      "is_starter_step": true,
      "estimated_minutes": 15,
      "friction_level": "micro",
      "energy_requirement": "creative",
      "priority": "high"
    },
    {
      "sequence_order": 2,
      "title": "Set up minimal FastAPI route accepting voice audio",
      "description": "Build endpoint testing Whisper transcription latency.",
      "is_starter_step": false,
      "estimated_minutes": 35,
      "friction_level": "easy",
      "energy_requirement": "deep_focus",
      "priority": "medium"
    }
  ]
}
```

---

### Step 4: Prompt C — Cognitive Density Auto-Placement & Dynamic Rescheduling
**Prompt C** evaluates your upcoming 7-day calendar density $D(d)$ and automatically matches the cognitive demands of the task with open focus windows on low-density **Green Days** ($D < 0.45$).

It also handles conversational natural language calendar modifications:
- *"Clear my Thursday afternoon and float those tasks to next week."*
- *"Free up Friday morning for deep focus."*

#### Prompt C Output Schema (Structured JSON)
```json
{
  "operation_type": "NLP_RESCHEDULE_AND_FLOAT",
  "command_summary": "Cleared Thursday afternoon (shifted 2 tasks to Monday morning). Auto-scheduled starter task into Friday 10:00 AM green slot.",
  "mutations": [
    {
      "action": "SCHEDULE_STARTER_TASK",
      "item_title": "Draft 5 core intake questionnaire prompts",
      "new_start": "2026-09-01T10:00:00Z",
      "new_end": "2026-09-01T10:15:00Z",
      "reason": "Placed into Monday morning low-density focus window (Density: 0.35)"
    }
  ],
  "coaching_nudge": "Thursday is cleared. Your 15-minute starter action is lined up for Monday at 10:00 AM!"
}
```

---

## 🔌 How to Connect to LLMs (OpenAI / Gemini / Claude)

CoachPilot supports **Google Gemini**, **OpenAI GPT-4o & Whisper**, **Anthropic Claude**, and an **Offline Cognitive Simulation Mode** (no API key required).

### Option 1: Google Gemini (Recommended — Ultra-Fast & Free Tier Available)
1. Get a free API Key at **[aistudio.google.com](https://aistudio.google.com/)**.
2. Open `backend/.env` (or configure in Render/Fly.io Environment Variables):
   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
   ```

### Option 2: OpenAI (Whisper STT + GPT-4o)
1. Get an API Key at **[platform.openai.com](https://platform.openai.com/)**.
2. Set in `backend/.env`:
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-proj-YourOpenAIApiKeyHere
   ```

### Option 3: Anthropic Claude (Claude 3.5 Sonnet)
1. Get an API Key at **[console.anthropic.com](https://console.anthropic.com/)**.
2. Set in `backend/.env`:
   ```env
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-YourAnthropicApiKeyHere
   ```

### Option 4: Offline Cognitive Simulation Mode (Default)
If you leave the API key blank or set `LLM_PROVIDER=simulation`, the backend automatically uses an embedded deterministic intelligence engine. This allows full testing of voice classification, feasibility scoring, task decomposition, and density scheduling with **zero external API costs**.

---

## 📐 Schedule Density Mathematical Model

For any given date $d$, the **Schedule Density Score** $D(d)$ is calculated as:

$$D(d) = \min\left(1.0, \frac{\sum_{i=1}^{N} (T_{i} \times W_{i}) + (N \times C_{\text{switch}})}{T_{\text{work\_window}}}\right)$$

### Parameters & Cognitive Weights:
- $T_i$: Duration of calendar event $i$ in minutes.
- $W_i$: Cognitive fatigue weight:
  - High-stakes client meetings / Architecture reviews: **$1.5\times$**
  - Standard team syncs / 1-on-1s: **$1.0\times$**
  - Light webinars / passive info sessions: **$0.6\times$**
  - Deep focus blocks: **$1.2\times$**
- $N$: Total number of distinct scheduled appointments on day $d$.
- $C_{\text{switch}}$: **15-minute Context-Switching Penalty** added per meeting transition.
- $T_{\text{work\_window}}$: Total working minutes in the day (**$540\text{ minutes} = 9\text{ hours}$**).

### Schedule Density Tiers:
| Tier | Score Range | Status | Auto-Scheduling Behavior |
| :--- | :--- | :--- | :--- |
| 🟢 **Green (Light)** | $0.00 \le D < 0.45$ | High cognitive bandwidth | **Primary target for Deep Work ($>45$m) & Idea Ignition Steps** |
| 🟡 **Yellow (Moderate)**| $0.45 \le D < 0.70$ | Balanced schedule | Target for quick 15-minute administrative micro-tasks |
| 🟠 **Orange (Dense)** | $0.70 \le D < 0.85$ | High fatigue risk | Protected buffers; no new automated tasks scheduled |
| 🔴 **Red (Overloaded)** | $D \ge 0.85$ | Burnout zone | Proactively prompts user to float non-essential tasks |

---

## 🛠️ Hardware Bill of Materials (BOM)

| Component | Recommended Model | Purpose | Est. Cost |
| :--- | :--- | :--- | :--- |
| **MCU** | **Waveshare ESP32-S3 Mini Development Board** | Based on **ESP32-S3FH4R2** Dual-Core Processor, 240MHz Running Frequency, 2.4GHz Wi-Fi & Bluetooth 5 (4MB Flash, 2MB on-chip PSRAM) | \$4.00 – \$5.50 |
| **Display** | **0.96" or 1.3" I2C OLED (SSD1306)** | 128x64 graphic screen for daily synthesis | \$2.00 – \$3.00 |
| **Microphone** | **INMP441 I2S Omnidirectional Mic** | 24-bit digital audio capture with high SNR | \$1.20 – \$2.00 |
| **Button** | **TS1215CJ 12x12mm Tactile Push Button** | 250gf actuation force, 15mm stem height | \$0.20 |
| **Status LED** | **Onboard WS2812 RGB LED (GPIO 21)** | Status feedback (or external 3mm LED on GPIO 10) | Included |
| **Resistor** | **220Ω 1/4W Resistor** | Only needed if using external LED | \$0.05 |
| **Power** | **USB-C Cable + 5V/1A Wall Adapter** | Continuous desk power (or 3.7V LiPo battery) | \$2.00 |
| **Total BOM** | | | **\$9.40 – \$12.50** |

---

## 🔌 Circuit Schematic & Wiring Pinout

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

### Complete Pin Assignment Table

| Module / Component | Pin / Terminal | Connects To (Waveshare ESP32-S3 Mini) | Logic / Electrical Level | Description & Wiring Details |
| :--- | :--- | :--- | :--- | :--- |
| **SSD1306 OLED (128x64)** | **VCC** | **3V3** | 3.3V DC | Display logic & power supply |
| | **GND** | **GND** | 0V | Common circuit ground |
| | **SDA** | **GPIO 8** | 3.3V I2C Data | Hardware I2C Serial Data line |
| | **SCL** | **GPIO 9** | 3.3V I2C Clock | Hardware I2C Serial Clock line |
| **INMP441 I2S Mic** | **VDD** | **3V3** | 3.3V DC | Digital microphone power |
| | **GND** | **GND** | 0V | Common circuit ground |
| | **L/R** | **GND** | 0V (GND) | Left Audio Channel Select |
| | **SD** | **GPIO 1** | 3.3V I2S Data | I2S Serial Data Out (to ESP32) |
| | **WS** | **GPIO 2** | 3.3V I2S Clock | Word Select / LR Frame Clock |
| | **SCK** | **GPIO 3** | 3.3V I2S Clock | Bit Clock Line |
| **TS1215CJ Push Button** | **Pin 1 (or 2)** | **GPIO 6** | Active LOW | Push-to-Talk input (internal `INPUT_PULLUP`) |
| | **Pin 4 (or 3)** | **GND** | 0V | Connects to Ground (closes on press) |
| **220Ω Resistor** | **Lead 1** | **GPIO 10** | 3.3V Output | In-series current-limiting resistor for LED |
| | **Lead 2** | **Status LED Anode (+)** | Forward Current | Connects directly to positive leg of LED |
| **Status LED (External)** | **Anode (+)** | **220Ω Resistor Lead 2** | Current limited | Longer leg of external LED |
| | **Cathode (-)**| **GND** | 0V | Shorter leg of external LED to Ground |
| **WS2812 RGB (Onboard)** | **Data In** | **GPIO 21 (Internal)** | 3.3V Logic | Built-in RGB on Waveshare board (no external resistor needed) |


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

## ⚡ Flashing the Waveshare ESP32-S3 Mini Firmware

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
4. Connect the board via USB-C and set the following in the **Tools Menu**:
   - **Board:** `ESP32S3 Dev Module` (or `Waveshare ESP32-S3-Zero / Mini`)
   - **USB CDC On Boot:** `Enabled` *(Crucial: ensures Serial Monitor works over USB-C)*
   - **Flash Size:** `4MB (32Mb)`
   - **Flash Mode:** `QIO 80MHz`
   - **PSRAM:** `QSPI PSRAM` *(Enables the on-chip 2MB Quad PSRAM R2 chip)*
   - **Upload Mode:** `UART0 / Hardware CDC`
5. Click **Upload**.

---

## ☁️ 24/7 Cloud Backend Deployment (No Laptop Needed)

Deploy the backend to **Render.com** (or Fly.io / Railway) for free in 3 minutes so your ESP32 companion works 24/7 independently:

1. Log in to [Render.com](https://render.com/) and click **New + $\rightarrow$ Web Service**.
2. Connect your GitHub repository (`anaswarramesh/my_buddy`).
3. Configure:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add your API Keys in **Environment Variables**:
   - `GEMINI_API_KEY`: `your_gemini_api_key`
   - `LLM_PROVIDER`: `gemini`
5. Copy your live Render URL (e.g., `https://coachpilot-backend.onrender.com`) and paste it into `SERVER_BASE` in the ESP32 firmware.

---

## 📱 Cross-Platform Mobile Client (React Native / Expo)

In addition to your physical ESP32 desk companion, CoachPilot includes a mobile companion app for iOS & Android:

```bash
cd frontend
npm install
npx expo start
```
- Inspect your **Idea Backlog** and feasibility radar scores.
- View your **7-Day Rolling Density Forecast**.
- Tap **Auto-Schedule** on any starter step or manual task.

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

## 🧪 Local Backend Testing & Web Preview

Run the automated test suite locally:
```bash
cd backend
PYTHONPATH=. .venv/bin/pytest -v
```

Launch the interactive local web dashboard:
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **`http://localhost:8000`** in your browser.
