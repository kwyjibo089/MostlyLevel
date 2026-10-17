/**
 * The phone's own accelerometer as the attitude source.
 *
 * The phone lies flat, screen up, with its top toward the front of the van.
 * Android reports the reaction to gravity in g: flat gives z ≈ +1, raising
 * the top gives positive y, raising the left edge gives negative x. Pitch
 * (front up) and roll (left up) follow from the gravity direction; a small
 * low-pass filter steadies the readings, since the phone's sensor is noisier
 * than the WT901's fused angles.
 */

import { SENSOR_STALE_MS } from '../config';
import type { Attitude } from '../levelling';
import type { DisplayState } from './client';

export type Gravity = { x: number; y: number; z: number };

export interface Accelerometer {
  isAvailable(): Promise<boolean>;
  /** Start delivering readings every `intervalMs`; returns a stop function. */
  listen(intervalMs: number, listener: (g: Gravity) => void): () => void;
}

export type PhoneSnapshot = {
  available: boolean | null;
  /** Vehicle pitch and roll before the level reference. */
  raw: Attitude | null;
  lastReadingMs: number;
  sequence: number;
};

export const PHONE_INTERVAL_MS = 50;
/** Share of each new reading in the filtered gravity vector (~0.3 s time constant at 20 Hz). */
export const PHONE_FILTER = 0.15;

const DEGREES = 180 / Math.PI;

export function gravityToAttitude({ x, y, z }: Gravity): Attitude {
  return {
    pitch: Math.atan2(y, Math.hypot(x, z)) * DEGREES,
    roll: Math.atan2(-x, Math.hypot(y, z)) * DEGREES,
  };
}

export class PhoneSensor {
  private snapshot: PhoneSnapshot = { available: null, raw: null, lastReadingMs: 0, sequence: 0 };
  private listeners = new Set<() => void>();
  private stopListening: (() => void) | null = null;
  private filtered: Gravity | null = null;

  constructor(
    private readonly accelerometer: Accelerometer,
    private readonly now: () => number = Date.now,
  ) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getSnapshot = (): PhoneSnapshot => this.snapshot;

  private set(patch: Partial<PhoneSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...patch };
    for (const listener of this.listeners) listener();
  }

  async start(): Promise<void> {
    if (this.stopListening) return;
    const available = await this.accelerometer.isAvailable();
    this.set({ available });
    if (!available || this.stopListening) return;
    this.filtered = null;
    this.stopListening = this.accelerometer.listen(PHONE_INTERVAL_MS, (g) => this.onReading(g));
  }

  stop(): void {
    this.stopListening?.();
    this.stopListening = null;
    this.filtered = null;
    this.set({ raw: null, sequence: this.snapshot.sequence + 1 });
  }

  private onReading(g: Gravity): void {
    const f = this.filtered;
    this.filtered = f
      ? {
          x: f.x + (g.x - f.x) * PHONE_FILTER,
          y: f.y + (g.y - f.y) * PHONE_FILTER,
          z: f.z + (g.z - f.z) * PHONE_FILTER,
        }
      : g;
    this.set({
      raw: gravityToAttitude(this.filtered),
      lastReadingMs: this.now(),
      sequence: this.snapshot.sequence + 1,
    });
  }
}

/** What the screen shows for the phone's sensor, like displayState() for the WT901. */
export function phoneDisplayState(snapshot: PhoneSnapshot, now: number): DisplayState {
  if (snapshot.available === false) return 'NO SENSOR';
  if (snapshot.available === null) return 'IDLE';
  if (snapshot.raw === null) return 'WAIT';
  return now - snapshot.lastReadingMs > SENSOR_STALE_MS ? 'NO DATA' : 'LIVE';
}
