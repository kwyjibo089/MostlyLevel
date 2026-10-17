/** The phone's accelerometer as attitude source: signs, filtering, and states. */

import { beforeEach, expect, test } from '@jest/globals';

import { Accelerometer, Gravity, gravityToAttitude, phoneDisplayState, PhoneSensor } from '../src/sensor/phone';

const SIN_2 = Math.sin((2 * Math.PI) / 180);
const COS_2 = Math.cos((2 * Math.PI) / 180);

test('flat phone is level', () => {
  const a = gravityToAttitude({ x: 0, y: 0, z: 1 });
  expect(a.pitch).toBeCloseTo(0, 6);
  expect(a.roll).toBeCloseTo(0, 6);
});

test('top raised by 2° is front high (positive pitch)', () => {
  // Android: raising the top tilts +y upward, so it reads +g·sin.
  const a = gravityToAttitude({ x: 0, y: SIN_2, z: COS_2 });
  expect(a.pitch).toBeCloseTo(2, 6);
  expect(a.roll).toBeCloseTo(0, 6);
});

test('left edge raised by 2° is left high (positive roll)', () => {
  // Raising the left edge tilts +x (right) downward, so it reads −g·sin.
  const a = gravityToAttitude({ x: -SIN_2, y: 0, z: COS_2 });
  expect(a.roll).toBeCloseTo(2, 6);
  expect(a.pitch).toBeCloseTo(0, 6);
});

test('angles do not depend on the reading’s magnitude', () => {
  const a = gravityToAttitude({ x: -SIN_2 * 1.05, y: 0, z: COS_2 * 1.05 });
  expect(a.roll).toBeCloseTo(2, 6);
});

class FakeAccelerometer implements Accelerometer {
  available = true;
  listener: ((g: Gravity) => void) | null = null;
  intervalMs = 0;
  async isAvailable() { return this.available; }
  listen(intervalMs: number, listener: (g: Gravity) => void) {
    this.intervalMs = intervalMs;
    this.listener = listener;
    return () => { this.listener = null; };
  }
}

let now = 0;
let accel: FakeAccelerometer;
let sensor: PhoneSensor;

beforeEach(() => {
  now = 1000;
  accel = new FakeAccelerometer();
  sensor = new PhoneSensor(accel, () => now);
});

test('readings are filtered and states follow them', async () => {
  expect(phoneDisplayState(sensor.getSnapshot(), now)).toBe('IDLE');
  await sensor.start();
  expect(accel.intervalMs).toBe(50);
  expect(phoneDisplayState(sensor.getSnapshot(), now)).toBe('WAIT');

  accel.listener!({ x: 0, y: 0, z: 1 });
  expect(sensor.getSnapshot().raw!.pitch).toBeCloseTo(0, 6);
  expect(phoneDisplayState(sensor.getSnapshot(), now)).toBe('LIVE');

  // A sudden 2° tilt moves the filtered value only part of the way.
  accel.listener!({ x: 0, y: SIN_2, z: COS_2 });
  const first = sensor.getSnapshot().raw!.pitch;
  expect(first).toBeGreaterThan(0.1);
  expect(first).toBeLessThan(1);
  for (let i = 0; i < 60; i += 1) accel.listener!({ x: 0, y: SIN_2, z: COS_2 });
  expect(sensor.getSnapshot().raw!.pitch).toBeCloseTo(2, 2);

  now += 1501;
  expect(phoneDisplayState(sensor.getSnapshot(), now)).toBe('NO DATA');
});

test('stop releases the accelerometer and clears the reading', async () => {
  await sensor.start();
  accel.listener!({ x: 0, y: 0, z: 1 });
  sensor.stop();
  expect(accel.listener).toBeNull();
  expect(sensor.getSnapshot().raw).toBeNull();
});

test('a phone without accelerometer', async () => {
  accel.available = false;
  await sensor.start();
  expect(accel.listener).toBeNull();
  expect(phoneDisplayState(sensor.getSnapshot(), now)).toBe('NO SENSOR');
});
