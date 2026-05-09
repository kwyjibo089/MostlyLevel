# Mostly Level

A tiny digital leveling tool built with a Raspberry Pi Pico WH, MPU6050, and Waveshare Pico-CapTouch-ePaper-2.9 display.

The project reads accelerometer data from the MPU6050, calculates pitch and roll, applies smoothing + calibration offsets, and displays the leveling guidance on a 2.9" e-paper screen.

---

# Features

- Pitch + roll measurement
- Calibration button
- Persistent calibration storage
- Smoothed sensor readings
- E-paper display output
- Simple leveling guidance:
  - FRONT HIGH
  - REAR HIGH
  - LEFT HIGH
  - RIGHT HIGH
  - LEVEL

---

# Hardware

## Main Components

- Raspberry Pi Pico WH
- MPU6050 accelerometer / gyroscope
- Waveshare Pico-CapTouch-ePaper-2.9
- Push button

---

# Wiring

## MPU6050

| MPU6050 | Pico |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GP4 |
| SCL | GP5 |

## Calibration Button

| Button | Pico |
|---|---|
| One side | GP14 |
| Other side | GND |

The button uses the Pico's internal pull-up resistor.

---

# Software Structure

```text
main.py        # Main application loop
display.py     # E-paper display driver
calibration.json
```

---

# Installation

## 1. Flash MicroPython

Install MicroPython on the Pico WH:

https://micropython.org/download/rp2-pico-w/

---

## 2. Upload Files

Using Thonny, upload:

```text
main.py
display.py
```

to the Pico filesystem.

---

## 3. Run

Run:

```python
main.py
```

or simply reboot the Pico.

---

# Calibration

1. Place the device in the desired "level" position
2. Press the calibration button
3. The current pitch + roll become the new zero reference
4. Calibration is saved to:

```text
calibration.json
```

---

# Display Refresh Notes

E-paper displays refresh slowly and should not be updated continuously.

The current firmware refreshes every few seconds to reduce:
- ghosting
- flashing
- panel wear

---

# Known Working Configuration

## Pico WH
- MicroPython RP2040 build

## E-paper display
- Waveshare Pico-CapTouch-ePaper-2.9

Important display fix:

```python
self.send_command(0x21)
self.send_data(0x00)
self.send_data(0x80)
```

Without this, the display may show a noisy border band.

---

# Future Improvements

- Better UI graphics
- Bubble level visualization
- Touch support
- Battery support
- Deep sleep mode
- Partial e-paper refresh
- Auto-rotation
- WiFi logging
- Web dashboard

---

# License

MIT

---

# Project Name

Mostly Level

Because perfectly level is overrated.