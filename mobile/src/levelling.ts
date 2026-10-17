/** Vehicle attitude and corner lift maths, ported from esp32/src/app.py. */

import {
  DISPLAY_PITCH_SENSOR_KEY,
  DISPLAY_PITCH_SIGN,
  DISPLAY_ROLL_SENSOR_KEY,
  DISPLAY_ROLL_SIGN,
  LEVEL_FRAME_RELEASE_THRESHOLD_DEG,
  LEVEL_FRAME_THRESHOLD_DEG,
  NO_WEDGE_NEEDED_THRESHOLD_CM,
  VAN_TILT_GAIN,
  VAN_TILT_MAX_DEG,
} from './config';

export type SensorAngles = { roll: number; pitch: number };
export type LevelReference = { pitch: number; roll: number };
export type Attitude = { pitch: number; roll: number };
export type Dimensions = { wheelbaseMm: number; frontTrackMm: number; rearTrackMm: number };
export type Corner = 'front_left' | 'front_right' | 'rear_left' | 'rear_right';
export type CornerLifts = Record<Corner, number>;

// Order matters: ties in the 2 WEDGES ranking keep this order, as on the ESP32.
export const CORNERS: readonly Corner[] = ['front_left', 'front_right', 'rear_left', 'rear_right'];

export function clamp(value: number, low: number, high: number): number {
  return Math.max(low, Math.min(high, value));
}

/** The sensor's raw angles in vehicle axes, before the level reference. */
export function sensorToVehicle(values: SensorAngles): Attitude {
  return {
    pitch: values[DISPLAY_PITCH_SENSOR_KEY] * DISPLAY_PITCH_SIGN,
    roll: values[DISPLAY_ROLL_SENSOR_KEY] * DISPLAY_ROLL_SIGN,
  };
}

/**
 * Vehicle pitch (positive = front high) and roll (positive = left high),
 * relative to the saved level reference.
 */
export function vehicleAttitude(values: SensorAngles, zero: LevelReference): Attitude {
  const raw = sensorToVehicle(values);
  return { pitch: raw.pitch - zero.pitch, roll: raw.roll - zero.roll };
}

/** The current raw attitude, saved as the new level reference. */
export function levelReferenceFrom(values: SensorAngles): LevelReference {
  return sensorToVehicle(values);
}

/**
 * Minimum lift per corner, in centimetres, to bring every corner up to the
 * highest one. Assumes the sensor sits at the centre of the wheel footprint
 * and the van floor is a rigid plane.
 */
export function cornerLifts(attitude: Attitude, dims: Dimensions): CornerLifts {
  const pitchSlope = Math.tan((attitude.pitch * Math.PI) / 180);
  const rollSlope = Math.tan((attitude.roll * Math.PI) / 180);
  const frontX = dims.wheelbaseMm / 2;
  const rearX = -frontX;
  const frontY = dims.frontTrackMm / 2;
  const rearY = dims.rearTrackMm / 2;
  const elevation: CornerLifts = {
    front_left: frontX * pitchSlope + frontY * rollSlope,
    front_right: frontX * pitchSlope - frontY * rollSlope,
    rear_left: rearX * pitchSlope + rearY * rollSlope,
    rear_right: rearX * pitchSlope - rearY * rollSlope,
  };
  const highest = Math.max(...CORNERS.map((corner) => elevation[corner]));
  const lifts = {} as CornerLifts;
  for (const corner of CORNERS) lifts[corner] = (highest - elevation[corner]) / 10;
  return lifts;
}

/** The 2 WEDGES view: the two corners needing most lift, or 'level'. */
export function wedgeAdvice(lifts: CornerLifts): 'level' | [Corner, Corner] {
  const ranked = [...CORNERS].sort((a, b) => lifts[b] - lifts[a]);
  if (lifts[ranked[0]] < NO_WEDGE_NEEDED_THRESHOLD_CM) return 'level';
  return [ranked[0], ranked[1]];
}

/** Level-frame state with hysteresis: on within ±0.5°, kept until beyond ±0.7°. */
export function isLevel(pitch: number, roll: number, wasLevel = false): boolean {
  const threshold = wasLevel ? LEVEL_FRAME_RELEASE_THRESHOLD_DEG : LEVEL_FRAME_THRESHOLD_DEG;
  return Math.abs(pitch) <= threshold && Math.abs(roll) <= threshold;
}

/** One axis counts as level for its ground line in the VAN view. */
export function axisLevel(angle: number): boolean {
  return Math.abs(angle) < LEVEL_FRAME_THRESHOLD_DEG;
}

/** Displayed van tilt: exaggerated so small angles show, then clamped. */
export function vanTilt(angleDeg: number): number {
  return clamp(angleDeg * VAN_TILT_GAIN, -VAN_TILT_MAX_DEG, VAN_TILT_MAX_DEG);
}
