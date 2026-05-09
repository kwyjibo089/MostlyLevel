# AGENTS.md

This project is a MicroPython embedded system for a camper van levelling device.

Constraints:
- Must run on Raspberry Pi Pico 2 W/Pico HW
- Use MicroPython only
- Optimize for simplicity and reliability
- Avoid heavy allocations inside loops
- Avoid unnecessary dependencies
- Hardware is MPU6050 over I2C and Waveshare 2.9inch eInk touch display

Coding style:
- Small modules
- Clear comments
- Minimal abstraction
- Embedded-friendly code

Code Structure should be like this

MostlyLevel/
├── main.py
├── imu.py
├── calibration.py
├── display.py
├── PROJECT_CONTEXT.md
├── AGENTS.md
├── README.md
└── assets/