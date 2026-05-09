# MostlyLevel

Camper van levelling system using a Raspberry Pi Pico 2 W (Prototyping with a Pi Pico HW).

## Hardware

- Raspberry Pi Pico 2 W/Pi Pico HW
- MPU6050 IMU over I2C
- WaveShare 2.9inch E-Ink Touch Display 
- Calibration button on GP14
- 5V powered through USB in Camper

## Wiring

### MPU6050
- SDA -> GP4
- SCL -> GP5
- VCC -> 3V3
- GND -> GND

### Calibration button
- GP14 -> button -> GND

## Goals

- Read pitch and roll
- Smooth noisy IMU data
- Store calibration offsets
- Display levelling guidance
- Run fully standalone at boot

## Notes

- Designed for camper van use
- Fast boot preferred
- Low power preferred
- No Linux required
- Prefer MicroPython

## Current Status

- Pico setup working
- I2C working
- MPU6050 communication working
- Button input working
- Tilt calculations working