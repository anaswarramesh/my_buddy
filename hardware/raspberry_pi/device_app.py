#!/usr/bin/env python3
import time
import os
import sys
import io
import wave
import requests
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
import sounddevice as sd
import numpy as np

# ================= CONFIGURATION =================
SERVER_URL = "http://localhost:8000"
PIN_BUTTON = 17  # GPIO 17 (Pin 11)
PIN_LED = 27     # GPIO 27 (Pin 13)

SAMPLE_RATE = 16000
CHANNELS = 1

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_LED, GPIO.OUT)
GPIO.output(PIN_LED, GPIO.LOW)

# Initialize I2C OLED Display
try:
    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial, width=128, height=64)
except Exception as e:
    print(f"[OLED] Warning: Hardware display not found: {e}")
    device = None

font_small = ImageFont.load_default()

def draw_screen(title, main_text, sub_text="", density_pct=35, density_level="LIGHT"):
    if not device:
        return
    image = Image.new('1', (device.width, device.height))
    draw = ImageDraw.Draw(image)

    # Header
    draw.text((0, 0), title, font=font_small, fill=255)
    draw.text((85, 0), density_level, font=font_small, fill=255)
    draw.line((0, 10, 127, 10), fill=255)

    # Density Box
    draw.rectangle((0, 14, 40, 50), outline=255)
    draw.text((6, 20), f"{density_pct}%", font=font_small, fill=255)
    draw.text((6, 36), "LOAD", font=font_small, fill=255)

    # Main Details
    draw.text((46, 16), main_text[:14], font=font_small, fill=255)
    draw.text((46, 30), sub_text[:14], font=font_small, fill=255)

    # Bottom Ticker
    draw.line((0, 53, 127, 53), fill=255)
    draw.text((0, 55), "Hold BTN to speak", font=font_small, fill=255)

    device.display(image)

def record_audio(duration_max=10):
    GPIO.output(PIN_LED, GPIO.HIGH)
    if device:
        image = Image.new('1', (device.width, device.height))
        draw = ImageDraw.Draw(image)
        draw.text((20, 20), ">> LISTENING <<", font=font_small, fill=255)
        draw.text((15, 38), "Speak your thought...", font=font_small, fill=255)
        device.display(image)

    audio_frames = []
    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
    stream.start()

    # Record while button is held
    while GPIO.input(PIN_BUTTON) == GPIO.LOW:
        data, _ = stream.read(512)
        audio_frames.append(data)
        time.sleep(0.01)

    stream.stop()
    stream.close()
    GPIO.output(PIN_LED, GPIO.LOW)

    if not audio_frames:
        return None

    audio_data = np.concatenate(audio_frames, axis=0)
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

    return wav_io.getvalue()

def process_and_display():
    try:
        res = requests.get(f"{SERVER_URL}/api/hardware/display-data", timeout=5)
        if res.status_code == 200:
            data = res.json()
            draw_screen(
                title=data.get("date_str", "Today"),
                main_text=f"Mtgs: {data.get('meeting_count', 0)}",
                sub_text=data.get("starter_task_title", "No tasks"),
                density_pct=data.get("density_pct", 35),
                density_level=data.get("density_level", "LIGHT")
            )
    except Exception as e:
        print(f"[Fetch Error] {e}")

def main():
    print("[CoachPilot Pi] Starting hardware listener...")
    process_and_display()
    last_poll = time.time()

    try:
        while True:
            # Check button press
            if GPIO.input(PIN_BUTTON) == GPIO.LOW:
                wav_bytes = record_audio()
                if wav_bytes and len(wav_bytes) > 2000:
                    if device:
                        image = Image.new('1', (device.width, device.height))
                        draw = ImageDraw.Draw(image)
                        draw.text((15, 25), "Whisper + AI Coach", font=font_small, fill=255)
                        draw.text((25, 40), "Analyzing...", font=font_small, fill=255)
                        device.display(image)

                    try:
                        resp = requests.post(
                            f"{SERVER_URL}/api/hardware/voice-upload",
                            data=wav_bytes,
                            headers={"Content-Type": "audio/wav"},
                            timeout=15
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            if device:
                                image = Image.new('1', (device.width, device.height))
                                draw = ImageDraw.Draw(image)
                                draw.text((5, 10), res_json.get("action_label", "PROCESSED"), font=font_small, fill=255)
                                draw.text((5, 30), res_json.get("starter_task", "")[:20], font=font_small, fill=255)
                                device.display(image)
                                time.sleep(3)
                    except Exception as err:
                        print(f"[Upload Error] {err}")

                process_and_display()

            # Refresh every 60 seconds
            if time.time() - last_poll > 60:
                process_and_display()
                last_poll = time.time()

            time.sleep(0.05)

    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
