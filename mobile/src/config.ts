/**
 * Sensor, levelling, and timing settings, mirroring esp32/src/config.py.
 *
 * Keep the values here and in the ESP32 config in step; shared/fixtures/
 * (generated from the ESP32 code) checks the logic that uses them. Values the
 * user can change per van (sensor, camper, dimensions) live in settings and
 * only take their defaults from here.
 */

// WT901BLE67-compatible sensor. The owner's unit; the user can pick another
// sensor in settings.
export const DEFAULT_SENSOR_ID = 'F0:A0:7A:DB:7D:45';
export const SENSOR_NAME_PREFIX = 'WT';
export const SENSOR_NOTIFY_UUID = '0000ffe4-0000-1000-8000-00805f9a34fb';
export const SENSOR_WRITE_UUID = '0000ffe9-0000-1000-8000-00805f9a34fb';
export const SENSOR_POWER_REGISTER = 0x64;
export const SENSOR_POWER_READ_COMMAND = [0xff, 0xaa, 0x27, SENSOR_POWER_REGISTER, 0x00];

// Fixed assumptions used by the sensor packet decoder.
export const SENSOR_PACKET_HEADER = 0x55;
export const SENSOR_ATTITUDE_PACKET_TYPE = 0x61;
export const SENSOR_REGISTER_PACKET_TYPE = 0x71;
export const SENSOR_ATTITUDE_PACKET_LENGTH = 20;
export const SENSOR_RAW_FULL_SCALE = 32768;
export const SENSOR_ACCEL_RANGE_G = 16;
export const SENSOR_GYRO_RANGE_DPS = 2000;
export const SENSOR_ANGLE_RANGE_DEG = 180;
export const SENSOR_POWER_VOLTAGE_DIVISOR = 100;
// Raw register value (centivolts) to percent, from the WT9011DCL-BT50 table.
// One point (385 = 60 %) matched the vendor's app; others are unchecked.
export const SENSOR_BATTERY_PERCENT_BANDS: ReadonlyArray<readonly [number, number]> = [
  [397, 100],
  [393, 90],
  [387, 75],
  [382, 60],
  [379, 50],
  [377, 40],
  [373, 30],
  [370, 20],
  [368, 15],
  [350, 10],
  [340, 5],
];

// Decoded sensor channels mapped to vehicle axes. Hardware-tested 2026-10-16
// with the installed sensor: front up gives positive pitch, left up positive
// roll. Recheck if the sensor is remounted.
export const DISPLAY_PITCH_SENSOR_KEY = 'roll' as const;
export const DISPLAY_PITCH_SIGN = 1;
export const DISPLAY_ROLL_SENSOR_KEY = 'pitch' as const;
export const DISPLAY_ROLL_SIGN = 1;

// CALIBRATE acts only after being held this long. Untested on a phone.
export const LONG_PRESS_MS = 1000;

export const NO_WEDGE_NEEDED_THRESHOLD_CM = 0.5;
export const LEVEL_FRAME_THRESHOLD_DEG = 0.5;
export const LEVEL_FRAME_RELEASE_THRESHOLD_DEG = 0.7;
// VAN view: tilt drawn at the measured angle times the gain, clamped.
export const VAN_TILT_GAIN = 3;
export const VAN_TILT_MAX_DEG = 20;
// HORIZON view: screen pixels the horizon moves per degree of pitch.
export const HORIZON_PIXELS_PER_DEGREE = 6;

// Data counts as stale when no sample arrived for this long.
export const SENSOR_STALE_MS = 1500;
// BLE link recovery, as in WT901BLEClient.maintain(). Untested values.
export const SENSOR_ERROR_RETRY_MS = 5000;
export const SENSOR_SETUP_TIMEOUT_MS = 20000;
export const SENSOR_SCAN_TIMEOUT_MS = 30000;
export const SENSOR_SILENT_RECONNECT_MS = 10000;
// The ESP32 hard-resets after this many recoveries without data; the app
// restarts its Bluetooth stack instead.
export const SENSOR_RECOVERY_RESET_COUNT = 5;
export const BATTERY_POLL_INTERVAL_MS = 60000;
// How often the client checks for a stuck link.
export const SENSOR_MAINTAIN_INTERVAL_MS = 250;

export const LANGUAGES = ['en', 'de', 'fr', 'es'] as const;
export type Language = (typeof LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = 'en';
