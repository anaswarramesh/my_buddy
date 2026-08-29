#!/bin/bash
echo "=== Installing CoachPilot Standalone Hardware on Raspberry Pi ==="

# Update package lists
sudo apt-get update
sudo apt-get install -y python3-pip python3-pil python3-dev libasound2-dev libatlas-base-dev portaudio19-dev i2c-tools

# Enable I2C interface
sudo raspi-config nonint do_i2c 0

# Install Python packages
pip3 install luma.oled sounddevice numpy requests RPi.GPIO

# Install systemd auto-start service
sudo cp coachpilot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable coachpilot.service
sudo systemctl start coachpilot.service

echo "=== CoachPilot Hardware Service Installed & Running on Boot ==="
