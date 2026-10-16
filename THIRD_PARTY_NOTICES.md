# Third-party notices

MostlyLevel's own code is licensed under the MIT License (see `LICENSE`). The parts listed below come from, or are derived from, other projects and remain under their own licenses.

## Adafruit ILI9341 library — display initialisation values

`src/ili9341.py` (`_init_display`) uses the ILI9341 power, VCOM, frame-rate, display-function, and gamma values from the `initcmd` table in Adafruit's Arduino library, <https://github.com/adafruit/Adafruit_ILI9341> (`Adafruit_ILI9341.cpp`). The values match that table byte for byte (compared on 2026-10-16); the Python driver around them is MostlyLevel's own. The library ships no separate license file; its source header states:

```
Written by Limor "ladyada" Fried for Adafruit Industries.

BSD license, all text here must be included in any redistribution.
```

The full header of `Adafruit_ILI9341.cpp` also reads, in part: "Adafruit invests time and resources providing this open source code, please support Adafruit and open-source hardware by purchasing products from Adafruit!"

## Adafruit GFX library — 5×7 font

The `FONT` table in `src/graphics.py` is a 5×7 column bitmap font of the kind in Adafruit GFX's classic font, <https://github.com/adafruit/Adafruit-GFX-Library> (`glcdfont.c`). Of its original 43 glyphs, 26 are identical to the current `glcdfont.c` (compared on 2026-10-16); the others match variants of the same widely copied 5×7 font, so the exact source is not established. It is attributed to Adafruit as the likely origin. The comma and the accented capitals (`ACCENT_MARKS`, `ACCENTED`), added on 2026-10-16, are MostlyLevel's own. Adafruit GFX's license:

```
Software License Agreement (BSD License)

Copyright (c) 2012 Adafruit Industries.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```

## MicroPython firmware — `firmware/`

`firmware/ESP32_GENERIC_S3-20260824-v1.29.0.bin` is the official MicroPython 1.29.0 build for ESP32-S3: its SHA-256 (`1dd9dcd2…8285e300`) matches the download from <https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20260824-v1.29.0.bin> (checked 2026-10-16). MicroPython is MIT-licensed, Copyright (c) 2013-2026 Damien P. George; the binary also contains third-party components (for example ESP-IDF and NimBLE, under Apache-2.0) under their own licenses. The full MicroPython license, including its component license summary, is in `firmware/MICROPYTHON_LICENSE`, copied from the v1.29.0 source tree.

## Espressif board-support reference — `reference/esp32_s3_es3c28p/`

The ESP-IDF board-support package in `reference/` is not part of the MicroPython application. Its header files state `SPDX-License-Identifier: Apache-2.0` with Espressif Systems (Shanghai) CO LTD copyright. Its README refers to a LICENSE file that was not included when it was copied here; `reference/esp32_s3_es3c28p/LICENSE` now holds the Apache License 2.0 text from <https://www.apache.org/licenses/LICENSE-2.0.txt>, matching those headers. `src/esp32_s3_es3c28p.c` and the board images in `doc/` carry no license statement; their terms are not established.
