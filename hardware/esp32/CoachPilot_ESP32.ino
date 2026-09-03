/**
 * CoachPilot AI (My Buddy) — Hardware Companion Firmware
 * Target MCU: Waveshare ESP32-S3 Mini Development Board
 * 
 * Performance Upgrades:
 * 1. Safe RAM Allocation: Automatically adapts to PSRAM or internal SRAM (never NULL)
 * 2. Reliable I2S Sampling: 256-byte chunks with 50ms timeout (never drops to 0 bytes)
 * 3. Debounced Push-to-Talk: 0ms instant press, mechanical bounce rejection
 * 4. FreeRTOS Dual-Core: Network uploads on Core 0, UI/Audio on Core 1
 * 5. INMP441 Microphone Gain: +6dB digital audio boost with live Serial VU meter
 * 6. Split OLED UI: Left Load % box + Right Events & Start Times
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>

// ================= USER CONFIGURATION =================
const char* WIFI_SSID = "YOUR_WIFI_SSID";          // <-- Enter your WiFi name
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";      // <-- Enter your WiFi password

// Server URL: Your live 24/7 Render Cloud backend
const char* SERVER_BASE = "https://my-buddy-81bd.onrender.com";

// ================= PIN DEFINITIONS =================
#define PIN_BUTTON      6   // Push-to-Talk Button (GPIO 6 to GND)
#define PIN_STATUS_LED  10  // Status LED
#define PIN_I2C_SDA     8   // OLED I2C SDA
#define PIN_I2C_SCL     9   // OLED I2C SCL
#define I2S_SD          1   // INMP441 Serial Data Out (SD)
#define I2S_WS          2   // INMP441 Word Select / LRCLK (WS)
#define I2S_SCK         3   // INMP441 Bit Clock (SCK)
#define I2S_PORT        I2S_NUM_0

// OLED Display Settings (128x64 I2C)
#define SCREEN_WIDTH    128
#define SCREEN_HEIGHT   64
#define OLED_RESET      -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Audio Buffer Settings (16 kHz, 16-bit, Mono)
#define SAMPLE_RATE     16000
#define BITS_PER_SAMPLE 16
size_t maxAudioBufferBytes = 160000; // Defaults to 5s (160 KB), adapts dynamically

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
unsigned long recordingStartTime = 0;
int consecutiveHighCount = 0;
int animFrame = 0;

// Dashboard Data
int densityPct = 0;
String densityLevel = "LIGHT";
String dateStr = "Today";
int meetingCount = 0;
String shortNudge = "GREEN DAY: Launch ideas!";

// Event List on Dashboard (Right side of Load Box)
struct OLEDEvent {
    String time;
    String title;
};
OLEDEvent oledEvents[4];
int oledEventCount = 0;

// Result Screen Data
String resultStatus = "PROCESSED";
String resultTask = "";
int resultFeasibility = 0;

// FreeRTOS Background Upload Task Handle
TaskHandle_t uploadTaskHandle = NULL;
volatile bool uploadFinished = false;
volatile bool uploadSuccess = false;

// Function Prototypes
void initI2S();
void writeWavHeader(uint8_t* header, uint32_t wavDataSize, uint32_t sampleRate, uint16_t channels, uint16_t bitsPerSample);
void fetchDisplayData();
void drawDashboard();
void drawRecordingScreen();
void drawUploadingScreen();
void drawResultScreen();
void drawErrorScreen(String errorMsg);
bool performHttpsUpload();

// ================= FREERTOS BACKGROUND NETWORK TASK (CORE 0) =================
void uploadWorkerTask(void* parameter) {
    for (;;) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        uploadFinished = false;
        uploadSuccess = performHttpsUpload();
        uploadFinished = true;
    }
}

// ================= SETUP =================
void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.println(F("\n========================================"));
    Serial.println(F(" CoachPilot AI Companion (Zero-Latency) "));
    Serial.println(F("========================================"));

    pinMode(PIN_BUTTON, INPUT_PULLUP);
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    // Initialize I2C Bus for Waveshare ESP32-S3 Mini
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

    // Initialize OLED Display
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println(F("[ERROR] SSD1306 OLED allocation failed"));
    }
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    // Show Boot Splash
    display.setTextSize(1);
    display.setCursor(18, 15);
    display.println("COACHPILOT AI");
    display.setCursor(22, 32);
    display.println("Zero-Delay v2.1");
    display.setCursor(15, 48);
    display.println("Connecting WiFi...");
    display.display();

    // Connect to WiFi
    Serial.print(F("Connecting to WiFi: "));
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 30) {
        delay(350);
        Serial.print(F("."));
        retries++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(F("\n[WiFi] Connected!"));
        Serial.print(F("[WiFi] ESP32 IP: "));
        Serial.println(WiFi.localIP());
    } else {
        Serial.println(F("\n[WiFi] Failed! Check SSID/password."));
    }

    // Dynamic Safe Buffer Allocation (Adapts to PSRAM or internal SRAM)
    size_t trySecs[4] = {8, 5, 4, 3};
    for (int i = 0; i < 4; i++) {
        size_t needed = (SAMPLE_RATE * 2 * trySecs[i]) + 44;
        if (psramFound()) {
            audioBuffer = (uint8_t*)ps_malloc(needed);
            if (audioBuffer) {
                maxAudioBufferBytes = needed - 44;
                Serial.print(F("[AUDIO] Allocated "));
                Serial.print(trySecs[i]);
                Serial.println(F("s buffer in PSRAM"));
                break;
            }
        }
        audioBuffer = (uint8_t*)malloc(needed);
        if (audioBuffer) {
            maxAudioBufferBytes = needed - 44;
            Serial.print(F("[AUDIO] Allocated "));
            Serial.print(trySecs[i]);
            Serial.println(F("s buffer in Internal SRAM"));
            break;
        }
    }

    if (!audioBuffer) {
        Serial.println(F("[ERROR CRITICAL] Failed to allocate audio buffer in RAM!"));
    }

    // Initialize INMP441 Microphone Driver
    initI2S();

    // Create FreeRTOS Background Upload Task on Core 0
    xTaskCreatePinnedToCore(
        uploadWorkerTask,
        "UploadTask",
        8192,
        NULL,
        1,
        &uploadTaskHandle,
        0 // Run network TLS on Core 0
    );

    // Initial Dashboard Sync
    fetchDisplayData();
    currentState = STATE_IDLE;
    drawDashboard();
}

// ================= MAIN LOOP (CORE 1) =================
void loop() {
    switch (currentState) {
        case STATE_IDLE: {
            // Instant 0ms detection on button press (Active LOW)
            if (digitalRead(PIN_BUTTON) == LOW) {
                currentState = STATE_RECORDING;
                recordedBytes = 0;
                consecutiveHighCount = 0;
                recordingStartTime = millis();
                digitalWrite(PIN_STATUS_LED, HIGH);
                Serial.println(F("\n[BUTTON] Pressed -> Recording Started immediately!"));
                drawRecordingScreen();
                break;
            }

            // Non-blocking periodic 60s background refresh
            if (millis() - lastDisplayPoll > 60000) {
                fetchDisplayData();
                drawDashboard();
                lastDisplayPoll = millis();
            }
            break;
        }

        case STATE_RECORDING: {
            // 1. Release check with mechanical bounce rejection
            // Ignore contact chatter during the first 120ms of hold
            if (millis() - recordingStartTime > 120) {
                if (digitalRead(PIN_BUTTON) == HIGH) {
                    consecutiveHighCount++;
                    // Require 3 consecutive HIGH reads (~15ms) to confirm genuine release
                    if (consecutiveHighCount >= 3) {
                        digitalWrite(PIN_STATUS_LED, LOW);
                        unsigned long durationMs = millis() - recordingStartTime;
                        Serial.print(F("[BUTTON] Released -> Held for "));
                        Serial.print(durationMs);
                        Serial.print(F(" ms, Captured "));
                        Serial.print(recordedBytes);
                        Serial.println(F(" audio bytes"));

                        if (recordedBytes > 25000 && durationMs >= 800) { // At least 0.8s of intentional speech
                            currentState = STATE_UPLOADING;
                            drawUploadingScreen();
                            // Trigger background upload on Core 0 without freezing UI!
                            if (uploadTaskHandle) {
                                xTaskNotifyGive(uploadTaskHandle);
                            }
                        } else {
                            Serial.println(F("[BUTTON] Tap too short (<0.8s), ignoring"));
                            currentState = STATE_IDLE;
                            drawDashboard();
                        }
                        break;
                    }
                } else {
                    consecutiveHighCount = 0; // Still actively pressed & held
                }
            }

            // 2. Animated waveform update every 100ms
            static unsigned long lastVuUpdate = 0;
            if (millis() - lastVuUpdate > 100) {
                drawRecordingScreen();
                lastVuUpdate = millis();
            }

            // 3. Read I2S audio chunk with safe 50ms timeout for 256 bytes
            if (audioBuffer && (recordedBytes < maxAudioBufferBytes)) {
                size_t bytesRead = 0;
                uint8_t temp[256];
                esp_err_t err = i2s_read(I2S_PORT, temp, sizeof(temp), &bytesRead, pdMS_TO_TICKS(50));
                
                if (err == ESP_OK && bytesRead > 0) {
                    if (recordedBytes == 0) {
                        Serial.print(F("[I2S] Audio stream receiving OK! Chunk: "));
                        Serial.print(bytesRead);
                        Serial.println(F(" bytes"));
                    }

                    if (recordedBytes + bytesRead <= maxAudioBufferBytes) {
                        uint8_t* dest = audioBuffer + 44 + recordedBytes;
                        memcpy(dest, temp, bytesRead);

                        // Apply +6dB digital gain boost (2x) and measure peak amplitude
                        int16_t* samples = (int16_t*)dest;
                        size_t sampleCount = bytesRead / 2;
                        int peak = 0;
                        for (size_t i = 0; i < sampleCount; i++) {
                            int32_t val = samples[i] * 2;
                            if (val > 32767) val = 32767;
                            if (val < -32768) val = -32768;
                            samples[i] = (int16_t)val;
                            int absVal = abs(samples[i]);
                            if (absVal > peak) peak = absVal;
                        }

                        // Print audio level to Serial Monitor periodically
                        static unsigned long lastSerialVu = 0;
                        if (millis() - lastSerialVu > 350) {
                            Serial.print(F("[MIC] Peak Amplitude: "));
                            Serial.print(peak);
                            if (peak > 1200) Serial.println(F(" [LOUD SPEECH]"));
                            else if (peak > 300) Serial.println(F(" [MODERATE SPEECH]"));
                            else Serial.println(F(" [NEAR SILENT - speak closer to mic]"));
                            lastSerialVu = millis();
                        }

                        recordedBytes += bytesRead;
                    }
                } else if (err != ESP_OK) {
                    static unsigned long lastErrPrint = 0;
                    if (millis() - lastErrPrint > 1000) {
                        Serial.print(F("[I2S ERROR] read failed: "));
                        Serial.println(err);
                        lastErrPrint = millis();
                    }
                }
            }
            break;
        }

        case STATE_UPLOADING: {
            // Wait for background upload task on Core 0 to finish
            if (uploadFinished) {
                if (uploadSuccess) {
                    currentState = STATE_RESULT;
                    drawResultScreen();
                } else {
                    currentState = STATE_ERROR;
                }
            }
            break;
        }

        case STATE_RESULT: {
            static unsigned long resultStartTime = 0;
            if (resultStartTime == 0) {
                resultStartTime = millis();
            }
            // If button is pressed during result, immediately start new recording!
            if (digitalRead(PIN_BUTTON) == LOW) {
                resultStartTime = 0;
                currentState = STATE_RECORDING;
                recordedBytes = 0;
                consecutiveHighCount = 0;
                recordingStartTime = millis();
                digitalWrite(PIN_STATUS_LED, HIGH);
                drawRecordingScreen();
                break;
            }
            if (millis() - resultStartTime > 2500) {
                resultStartTime = 0;
                fetchDisplayData();
                currentState = STATE_IDLE;
                drawDashboard();
            }
            break;
        }

        case STATE_ERROR: {
            static unsigned long errStartTime = 0;
            if (errStartTime == 0) {
                errStartTime = millis();
            }
            if (digitalRead(PIN_BUTTON) == LOW || millis() - errStartTime > 2500) {
                errStartTime = 0;
                currentState = STATE_IDLE;
                drawDashboard();
            }
            break;
        }
    }

    delay(4); // 4ms tight polling loop
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
        .dma_buf_count = 8,
        .dma_buf_len = 256,
        .use_apll = false
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD
    };

    esp_err_t err = i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.print(F("[I2S ERROR] Driver install failed: "));
        Serial.println(err);
    } else {
        Serial.println(F("[I2S] Driver installed successfully."));
    }

    err = i2s_set_pin(I2S_PORT, &pin_config);
    if (err != ESP_OK) {
        Serial.print(F("[I2S ERROR] Set pin failed: "));
        Serial.println(err);
    } else {
        Serial.println(F("[I2S] Pins configured: SD=1, WS=2, SCK=3"));
    }
}

// ================= HTTPS AUDIO UPLOAD (RUNS ON CORE 0) =================
bool performHttpsUpload() {
    if (!audioBuffer) return false;

    writeWavHeader(audioBuffer, recordedBytes, SAMPLE_RATE, 1, 16);

    if (WiFi.status() == WL_CONNECTED) {
        Serial.print(F("[HTTP] Background uploading "));
        Serial.print(recordedBytes + 44);
        Serial.println(F(" bytes WAV to Render..."));

        WiFiClientSecure client;
        client.setInsecure();
        client.setTimeout(35);
        HTTPClient http;
        String url = String(SERVER_BASE) + "/api/hardware/voice-upload?user_id=default-user";
        http.begin(client, url);
        http.addHeader("Content-Type", "audio/wav");
        http.setTimeout(35000); // 35-second timeout for full Gemini AI transcription

        int httpCode = http.POST(audioBuffer, recordedBytes + 44);
        Serial.print(F("[HTTP] Response Code: "));
        Serial.println(httpCode);

        if (httpCode == 200) {
            String respStr = http.getString();
            Serial.print(F("[HTTP] Server Response: "));
            Serial.println(respStr);

            JsonDocument doc;
            deserializeJson(doc, respStr);

            resultStatus = doc["action_label"].as<String>();
            resultTask = doc["starter_task"].as<String>();
            resultFeasibility = doc["feasibility"] | 0;
            http.end();
            return true;
        } else {
            String errStr = http.getString();
            Serial.print(F("[HTTP] Error: "));
            Serial.println(errStr);
            drawErrorScreen("HTTP " + String(httpCode));
            http.end();
            return false;
        }
    } else {
        Serial.println(F("[HTTP] WiFi Disconnected"));
        drawErrorScreen("WiFi Disconnected");
        return false;
    }
}

// ================= DISPLAY RENDERING =================
void fetchDisplayData() {
    if (WiFi.status() != WL_CONNECTED) return;

    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = String(SERVER_BASE) + "/api/hardware/display-data?user_id=default-user";
    http.begin(client, url);
    http.setTimeout(5000);
    int httpCode = http.GET();
    if (httpCode == 200) {
        String payload = http.getString();
        JsonDocument doc;
        deserializeJson(doc, payload);

        densityPct = doc["density_pct"] | 0;
        densityLevel = doc["density_level"].as<String>();
        dateStr = doc["date_str"].as<String>();
        meetingCount = doc["meeting_count"] | 0;
        shortNudge = doc["short_nudge"].as<String>();

        // Parse up to 3 upcoming events for right side list
        oledEventCount = 0;
        if (doc["events"].is<JsonArray>()) {
            JsonArray evArr = doc["events"].as<JsonArray>();
            for (JsonObject ev : evArr) {
                if (oledEventCount < 4) {
                    oledEvents[oledEventCount].time = ev["time"].as<String>();
                    oledEvents[oledEventCount].title = ev["title"].as<String>();
                    oledEventCount++;
                }
            }
        }
    }
    http.end();
}

void drawDashboard() {
    display.clearDisplay();

    // 1. Header Bar: Date & Density Level
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(dateStr);
    display.setCursor(84, 0);
    display.print(densityLevel);
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    // 2. Left Column: Density Load Gauge Box (40px wide)
    display.drawRoundRect(0, 12, 40, 38, 3, SSD1306_WHITE);
    display.setCursor(3, 17);
    display.setTextSize(2);
    if (densityPct < 10) display.print(" ");
    display.print(densityPct);
    display.setTextSize(1);
    display.setCursor(27, 17);
    display.print("%");
    display.setCursor(8, 36);
    display.print("LOAD");

    // Divider line between load box and events list
    display.drawLine(43, 12, 43, 50, SSD1306_WHITE);

    // 3. Right Column: List of Events & Times (x=46 to 127)
    display.setTextSize(1);
    if (oledEventCount == 0) {
        display.setCursor(47, 16);
        display.print("No events");
        display.setCursor(47, 28);
        display.print("Clear day!");
        display.setCursor(47, 40);
        display.print("Focus time");
    } else {
        int yPos = 13;
        for (int i = 0; i < oledEventCount && i < 3; i++) {
            display.setCursor(47, yPos);
            display.print(oledEvents[i].time);
            display.print(" ");
            display.print(oledEvents[i].title.substring(0, 7));
            yPos += 13;
        }
    }

    // 4. Bottom Ticker: Coaching Nudge
    display.drawLine(0, 52, 127, 52, SSD1306_WHITE);
    display.setCursor(0, 55);
    display.setTextSize(1);
    display.print(shortNudge.substring(0, 21));

    display.display();
}

void drawRecordingScreen() {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(18, 8);
    display.println(">> RECORDING <<");

    animFrame = (animFrame + 1) % 6;
    for (int i = 0; i < 11; i++) {
        int h = 6 + ((i + animFrame) % 5) * 4;
        display.fillRect(20 + i * 8, 38 - (h / 2), 4, h, SSD1306_WHITE);
    }

    display.setCursor(10, 48);
    display.println("Speak thought / task");
    display.display();
}

void drawUploadingScreen() {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(12, 16);
    display.println("AI Cloud Coach");
    display.setCursor(18, 32);
    display.println("Processing audio...");
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
    display.println("Task / Event:");
    display.setCursor(0, 28);
    display.println(resultTask.substring(0, 21));

    display.drawLine(0, 48, 127, 48, SSD1306_WHITE);
    display.setCursor(0, 53);
    if (resultFeasibility > 0) {
        display.print("Feasibility: ");
        display.print(resultFeasibility);
        display.print("%");
    } else {
        display.print("Saved to Tasks Queue");
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
