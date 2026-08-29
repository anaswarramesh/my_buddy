/**
 * CoachPilot AI — ESP32 Hardware Companion Firmware
 * Features:
 * - INMP441 I2S Digital Microphone recording with automatic 44-byte WAV header encoding
 * - 0.96" / 1.3" I2C SSD1306 OLED Display UI (128x64 pixels)
 * - Push-to-Talk Tactile Button with Live VU-Meter animation
 * - Schedule Density Gauge, Starter Steps scroller, and Coaching Ticker
 * - HTTP REST client communicating with FastAPI backend
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>

// ================= USER CONFIGURATION =================
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// Replace with your Cloud URL (e.g. Render/Fly.io) or local LAN IP
const char* SERVER_BASE = "https://your-coachpilot-app.onrender.com";

// Pin Configurations
#define PIN_BUTTON      4
#define PIN_STATUS_LED  2

// INMP441 I2S Microphone Pins
#define I2S_WS          25   // L/R Word Select Clock
#define I2S_SD          32   // Serial Data In
#define I2S_SCK         33   // Bit Clock
#define I2S_PORT        I2S_NUM_0

// OLED Display (I2C SSD1306)
#define SCREEN_WIDTH    128
#define SCREEN_HEIGHT   64
#define OLED_RESET      -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Audio Buffer (16 kHz, 16-bit, Mono)
#define SAMPLE_RATE     16000
#define BITS_PER_SAMPLE 16
#define MAX_RECORD_SECS 10
#define BUFFER_SIZE     (SAMPLE_RATE * (BITS_PER_SAMPLE / 8) * MAX_RECORD_SECS)

// State Machine
enum DeviceState {
    STATE_BOOT,
    STATE_IDLE,
    STATE_RECORDING,
    STATE_UPLOADING,
    STATE_RESULT,
    STATE_ERROR
};

DeviceState currentState = STATE_BOOT;
uint8_t* audioBuffer = nullptr;
size_t recordedBytes = 0;
unsigned long lastDisplayPoll = 0;
int animFrame = 0;

// Dashboard Data
int densityPct = 35;
String densityLevel = "LIGHT";
String dateStr = "Today";
int meetingCount = 2;
String starterTask = "Draft 3 value props";
String shortNudge = "GREEN DAY: Launch ideas!";

// Result Screen Data
String resultStatus = "PROCESSED";
String resultTask = "";
int resultFeasibility = 0;

// Function Prototypes
void initI2S();
void writeWavHeader(uint8_t* header, uint32_t wavDataSize, uint32_t sampleRate, uint16_t channels, uint16_t bitsPerSample);
void fetchDisplayData();
void drawDashboard();
void drawRecordingScreen();
void drawUploadingScreen();
void drawResultScreen();
void drawErrorScreen(String errorMsg);

// ================= SETUP =================
void setup() {
    Serial.begin(115200);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    // Initialize I2C OLED (Default Address 0x3C)
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("SSD1306 allocation failed!");
    }
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 15);
    display.println("CoachPilot AI");
    display.setCursor(10, 32);
    display.println("Hardware Companion");
    display.setCursor(10, 48);
    display.println("Connecting WiFi...");
    display.display();

    // Connect to Wi-Fi
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 25) {
        delay(400);
        Serial.print(".");
        retries++;
    }

    // Allocate Audio Buffer (with 44-byte WAV header offset)
    audioBuffer = (uint8_t*)malloc(BUFFER_SIZE + 44);
    if (!audioBuffer) {
        Serial.println("Error: Failed to allocate audio buffer!");
    }

    // Initialize I2S Audio Driver
    initI2S();

    // Initial Data Fetch & Transition to Idle
    fetchDisplayData();
    currentState = STATE_IDLE;
    drawDashboard();
}

// ================= MAIN LOOP =================
void loop() {
    switch (currentState) {
        case STATE_IDLE: {
            // Check Push-to-Talk Button (Active LOW)
            if (digitalRead(PIN_BUTTON) == LOW) {
                currentState = STATE_RECORDING;
                recordedBytes = 0;
                digitalWrite(PIN_STATUS_LED, HIGH);
                drawRecordingScreen();
            }

            // Periodic 60-second background refresh
            if (millis() - lastDisplayPoll > 60000) {
                fetchDisplayData();
                drawDashboard();
                lastDisplayPoll = millis();
            }
            break;
        }

        case STATE_RECORDING: {
            // Draw animated VU waveform while button is held
            drawRecordingScreen();

            // Read I2S audio chunk
            if (recordedBytes < BUFFER_SIZE) {
                size_t bytesRead = 0;
                uint8_t temp[512];
                i2s_read(I2S_PORT, temp, sizeof(temp), &bytesRead, portMAX_DELAY);
                if (bytesRead > 0 && (recordedBytes + bytesRead <= BUFFER_SIZE)) {
                    memcpy(audioBuffer + 44 + recordedBytes, temp, bytesRead);
                    recordedBytes += bytesRead;
                }
            }

            // Button released: Stop and upload
            if (digitalRead(PIN_BUTTON) == HIGH) {
                digitalWrite(PIN_STATUS_LED, LOW);
                if (recordedBytes > 1500) {
                    currentState = STATE_UPLOADING;
                    drawUploadingScreen();
                    uploadAudio();
                } else {
                    // Audio too short
                    currentState = STATE_IDLE;
                    drawDashboard();
                }
            }
            break;
        }

        case STATE_UPLOADING: {
            // Handled synchronously in uploadAudio()
            break;
        }

        case STATE_RESULT: {
            drawResultScreen();
            delay(3500);
            fetchDisplayData();
            currentState = STATE_IDLE;
            drawDashboard();
            break;
        }

        case STATE_ERROR: {
            delay(3000);
            fetchDisplayData();
            currentState = STATE_IDLE;
            drawDashboard();
            break;
        }
    }

    delay(20);
}

// ================= I2S DRIVER =================
void initI2S() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 1024,
        .use_apll = false
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD
    };

    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin_config);
}

// ================= AUDIO UPLOAD =================
void uploadAudio() {
    // Generate standard 44-byte WAV header at buffer start
    writeWavHeader(audioBuffer, recordedBytes, SAMPLE_RATE, 1, 16);

    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        String url = String(SERVER_BASE) + "/api/hardware/voice-upload";
        http.begin(url);
        http.addHeader("Content-Type", "audio/wav");
        http.setTimeout(15000); // 15-second timeout for LLM

        int httpCode = http.POST(audioBuffer, recordedBytes + 44);
        if (httpCode == 200) {
            String respStr = http.getString();
            JsonDocument doc;
            deserializeJson(doc, respStr);

            resultStatus = doc["action_label"].as<String>();
            resultTask = doc["starter_task"].as<String>();
            resultFeasibility = doc["feasibility"] | 0;

            currentState = STATE_RESULT;
        } else {
            drawErrorScreen("HTTP " + String(httpCode));
            currentState = STATE_ERROR;
        }
        http.end();
    } else {
        drawErrorScreen("WiFi Disconnected");
        currentState = STATE_ERROR;
    }
}

// ================= DISPLAY RENDERING =================
void fetchDisplayData() {
    if (WiFi.status() != WL_CONNECTED) return;

    HTTPClient http;
    String url = String(SERVER_BASE) + "/api/hardware/display-data";
    http.begin(url);
    http.setTimeout(5000);
    int httpCode = http.GET();
    if (httpCode == 200) {
        String payload = http.getString();
        JsonDocument doc;
        deserializeJson(doc, payload);

        densityPct = doc["density_pct"] | 35;
        densityLevel = doc["density_level"].as<String>();
        dateStr = doc["date_str"].as<String>();
        meetingCount = doc["meeting_count"] | 0;
        shortNudge = doc["short_nudge"].as<String>();
        starterTask = doc["starter_task_title"].as<String>();
    }
    http.end();
}

void drawDashboard() {
    display.clearDisplay();

    // 1. Header Bar: Date & Density Level
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(dateStr);
    display.setCursor(82, 0);
    display.print(densityLevel);
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    // 2. Left Column: Density Load Gauge Box
    display.drawRoundRect(0, 13, 44, 37, 4, SSD1306_WHITE);
    display.setCursor(5, 20);
    display.setTextSize(2);
    display.print(densityPct);
    display.setTextSize(1);
    display.setCursor(31, 20);
    display.print("%");
    display.setCursor(8, 38);
    display.print("LOAD");

    // 3. Right Column: Meetings & Actionable Starter Step
    display.setCursor(50, 14);
    display.print("Mtgs: ");
    display.print(meetingCount);

    display.setCursor(50, 26);
    display.print("Step 1 (Micro):");
    display.setCursor(50, 38);
    display.print(starterTask.substring(0, 12));

    // 4. Bottom Ticker: Coaching Nudge
    display.drawLine(0, 52, 127, 52, SSD1306_WHITE);
    display.setCursor(0, 55);
    display.print(shortNudge.substring(0, 21));

    display.display();
}

void drawRecordingScreen() {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(18, 8);
    display.println(">> RECORDING <<");

    // Dynamic animated waveform bars
    animFrame = (animFrame + 1) % 6;
    for (int i = 0; i < 11; i++) {
        int h = 6 + ((i + animFrame) % 5) * 4;
        display.fillRect(20 + i * 8, 38 - (h / 2), 4, h, SSD1306_WHITE);
    }

    display.setCursor(10, 48);
    display.println("Speak thought / idea");
    display.display();
}

void drawUploadingScreen() {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(12, 16);
    display.println("Whisper + AI Coach");
    display.setCursor(20, 32);
    display.println("Analyzing idea...");
    display.drawRoundRect(20, 48, 88, 8, 3, SSD1306_WHITE);
    display.fillRoundRect(22, 50, 44, 4, 2, SSD1306_WHITE);
    display.display();
}

void drawResultScreen() {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println(resultStatus);
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    display.setCursor(0, 16);
    display.println("Starter Action:");
    display.setCursor(0, 28);
    display.println(resultTask.substring(0, 21));

    display.drawLine(0, 48, 127, 48, SSD1306_WHITE);
    display.setCursor(0, 53);
    if (resultFeasibility > 0) {
        display.print("Feasibility: ");
        display.print(resultFeasibility);
        display.print("%");
    } else {
        display.print("Saved to Daily Plan");
    }

    display.display();
}

void drawErrorScreen(String errorMsg) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(20, 15);
    display.println("Network Error");
    display.setCursor(10, 35);
    display.println(errorMsg);
    display.display();
}

// ================= WAV HEADER UTILITY =================
void writeWavHeader(uint8_t* header, uint32_t wavDataSize, uint32_t sampleRate, uint16_t channels, uint16_t bitsPerSample) {
    uint32_t totalDataLen = wavDataSize + 36;
    uint32_t byteRate = sampleRate * channels * (bitsPerSample / 8);

    header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
    header[4] = (uint8_t)(totalDataLen & 0xff);
    header[5] = (uint8_t)((totalDataLen >> 8) & 0xff);
    header[6] = (uint8_t)((totalDataLen >> 16) & 0xff);
    header[7] = (uint8_t)((totalDataLen >> 24) & 0xff);
    header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
    header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
    header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0;
    header[20] = 1; header[21] = 0;
    header[22] = (uint8_t)channels; header[23] = 0;
    header[24] = (uint8_t)(sampleRate & 0xff);
    header[25] = (uint8_t)((sampleRate >> 8) & 0xff);
    header[26] = (uint8_t)((sampleRate >> 16) & 0xff);
    header[27] = (uint8_t)((sampleRate >> 24) & 0xff);
    header[28] = (uint8_t)(byteRate & 0xff);
    header[29] = (uint8_t)((byteRate >> 8) & 0xff);
    header[30] = (uint8_t)((byteRate >> 16) & 0xff);
    header[31] = (uint8_t)((byteRate >> 24) & 0xff);
    header[32] = (uint8_t)(channels * (bitsPerSample / 8)); header[33] = 0;
    header[34] = (uint8_t)bitsPerSample; header[35] = 0;
    header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
    header[40] = (uint8_t)(wavDataSize & 0xff);
    header[41] = (uint8_t)((wavDataSize >> 8) & 0xff);
    header[42] = (uint8_t)((wavDataSize >> 16) & 0xff);
    header[43] = (uint8_t)((wavDataSize >> 24) & 0xff);
}
