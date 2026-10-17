/**
 * Vehicle attitude for the screens, like the ESP32 main loop: pitch and roll
 * relative to the level reference, the level frame with hysteresis, and the
 * display state. Readouts and lifts use the latest sample as it is; only the
 * drawn vans and horizon are smoothed so they move fluidly between samples.
 */

import { useEffect, useRef, useState } from 'react';

import { Attitude, isLevel, vehicleAttitude } from '../levelling';
import type { DisplayState } from '../sensor/client';
import { useSensor } from '../sensor/SensorProvider';
import { useSettings } from '../settings/SettingsProvider';

export type AttitudeView = {
  shown: DisplayState;
  /** Latest attitude, or null when no sample is available. */
  attitude: Attitude | null;
  /** Smoothed attitude for drawing; level (0, 0) without data. */
  drawn: Attitude;
  levelFrame: boolean;
  batteryPercent: number | null;
};

const SMOOTHING = 0.25; // Share of the remaining distance covered per frame.

export function useAttitude(): AttitudeView {
  const { snapshot, shown } = useSensor();
  const { settings } = useSettings();
  const hasValues = snapshot.latest !== null;
  const attitude = snapshot.latest ? vehicleAttitude(snapshot.latest, settings.zero) : null;

  // Hysteresis: decided once per new sample (or state change), as on the ESP32.
  const level = useRef(false);
  const decidedFor = useRef<string>('');
  const key = `${snapshot.sequence}|${shown}|${settings.zero.pitch}|${settings.zero.roll}`;
  if (decidedFor.current !== key) {
    decidedFor.current = key;
    level.current = shown === 'LIVE' && attitude !== null && isLevel(attitude.pitch, attitude.roll, level.current);
  }

  const target = attitude ?? { pitch: 0, roll: 0 };
  const targetRef = useRef(target);
  targetRef.current = target;
  const [drawn, setDrawn] = useState<Attitude>(target);
  useEffect(() => {
    let frame = 0;
    const step = () => {
      setDrawn((current) => {
        const goal = targetRef.current;
        const dp = goal.pitch - current.pitch;
        const dr = goal.roll - current.roll;
        if (Math.abs(dp) < 0.005 && Math.abs(dr) < 0.005) {
          return current.pitch === goal.pitch && current.roll === goal.roll ? current : goal;
        }
        return { pitch: current.pitch + dp * SMOOTHING, roll: current.roll + dr * SMOOTHING };
      });
      frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, []);

  return {
    shown,
    attitude: hasValues ? attitude : null,
    drawn,
    levelFrame: level.current,
    // Like the ESP32 header: the last known reading stays until a new one.
    batteryPercent: snapshot.battery?.percent ?? null,
  };
}
