/** WT901 packet decoding, ported from esp32/src/ble_read.py. */

import {
  SENSOR_ACCEL_RANGE_G,
  SENSOR_ANGLE_RANGE_DEG,
  SENSOR_ATTITUDE_PACKET_LENGTH,
  SENSOR_ATTITUDE_PACKET_TYPE,
  SENSOR_BATTERY_PERCENT_BANDS,
  SENSOR_GYRO_RANGE_DPS,
  SENSOR_PACKET_HEADER,
  SENSOR_POWER_REGISTER,
  SENSOR_POWER_VOLTAGE_DIVISOR,
  SENSOR_RAW_FULL_SCALE,
  SENSOR_REGISTER_PACKET_TYPE,
} from '../config';

export type SensorValues = {
  acc_x: number;
  acc_y: number;
  acc_z: number;
  gyro_x: number;
  gyro_y: number;
  gyro_z: number;
  roll: number;
  pitch: number;
  yaw: number;
};

export type PowerReading = { raw: number; voltage: number; percent: number };

type Bytes = ArrayLike<number>;

/** Read a signed 16-bit little-endian integer. */
export function readInt16(data: Bytes, offset: number): number {
  const value = data[offset] | (data[offset + 1] << 8);
  return value >= 32768 ? value - 65536 : value;
}

/** Map the battery register value using the configured percentage bands. */
export function batteryPercent(raw: number): number {
  for (const [minimumRaw, percent] of SENSOR_BATTERY_PERCENT_BANDS) {
    if (raw >= minimumRaw) return percent;
  }
  return 0;
}

/** Decode a fixed-length 55 61 attitude notification, or return null. */
export function decodePacket(packet: Bytes): SensorValues | null {
  if (
    packet.length !== SENSOR_ATTITUDE_PACKET_LENGTH ||
    packet[0] !== SENSOR_PACKET_HEADER ||
    packet[1] !== SENSOR_ATTITUDE_PACKET_TYPE
  ) {
    return null;
  }
  const raw: number[] = [];
  for (let offset = 2; offset < 20; offset += 2) raw.push(readInt16(packet, offset));
  const accel = SENSOR_ACCEL_RANGE_G / SENSOR_RAW_FULL_SCALE;
  const gyro = SENSOR_GYRO_RANGE_DPS / SENSOR_RAW_FULL_SCALE;
  const angle = SENSOR_ANGLE_RANGE_DEG / SENSOR_RAW_FULL_SCALE;
  return {
    acc_x: raw[0] * accel,
    acc_y: raw[1] * accel,
    acc_z: raw[2] * accel,
    gyro_x: raw[3] * gyro,
    gyro_y: raw[4] * gyro,
    gyro_z: raw[5] * gyro,
    roll: raw[6] * angle,
    pitch: raw[7] * angle,
    yaw: raw[8] * angle,
  };
}

/** True for a 55 71 register response (these are not attitude data). */
export function isRegisterPacket(packet: Bytes): boolean {
  return (
    packet.length >= 4 &&
    packet[0] === SENSOR_PACKET_HEADER &&
    packet[1] === SENSOR_REGISTER_PACKET_TYPE
  );
}

/** Battery reading from a register response to the power read command. */
export function decodePowerResponse(packet: Bytes): PowerReading | null {
  if (!isRegisterPacket(packet) || packet.length < 6) return null;
  const startRegister = packet[2] | (packet[3] << 8);
  if (startRegister !== SENSOR_POWER_REGISTER) return null;
  const raw = packet[4] | (packet[5] << 8);
  return { raw, voltage: raw / SENSOR_POWER_VOLTAGE_DIVISOR, percent: batteryPercent(raw) };
}

/**
 * Split a notification into 20-byte frames. The sensor sometimes sends two
 * frames in one notification (seen 2026-10-17: a 55 71 register response
 * followed by a 55 61 attitude packet, 40 bytes). Anything that is not a
 * whole number of frames starting with 55 is returned as it is.
 */
export function splitFrames(value: number[]): number[][] {
  const size = SENSOR_ATTITUDE_PACKET_LENGTH;
  if (value.length <= size || value.length % size !== 0) return [value];
  const frames: number[][] = [];
  for (let offset = 0; offset < value.length; offset += size) {
    const frame = value.slice(offset, offset + size);
    if (frame[0] !== SENSOR_PACKET_HEADER) return [value];
    frames.push(frame);
  }
  return frames;
}

export function hexToBytes(hex: string): number[] {
  const bytes: number[] = [];
  for (let index = 0; index < hex.length; index += 2) {
    bytes.push(parseInt(hex.slice(index, index + 2), 16));
  }
  return bytes;
}
