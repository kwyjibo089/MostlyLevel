/**
 * Runs the selected attitude source for the app: the WT901 client over
 * Bluetooth, or the phone's own accelerometer. Either runs only while the app
 * is in the foreground. Leaving the WT901 (background, or switching to the
 * phone) disconnects it, since the sensor accepts one connection at a time
 * and the ESP32 display can then use it.
 */

import { useKeepAwake } from 'expo-keep-awake';
import { Accelerometer as ExpoAccelerometer } from 'expo-sensors';
import { createContext, ReactNode, useContext, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { AppState } from 'react-native';

import { SENSOR_MAINTAIN_INTERVAL_MS } from '../config';
import { Attitude, sensorToVehicle } from '../levelling';
import { SensorSource, useSettings } from '../settings/SettingsProvider';
import { bleManagerTransport } from './bleManagerTransport';
import { DisplayState, displayState, WT901Client } from './client';
import { Accelerometer, phoneDisplayState, PhoneSensor } from './phone';
import type { PowerReading } from './protocol';

const expoAccelerometer: Accelerometer = {
  isAvailable: () => ExpoAccelerometer.isAvailableAsync(),
  listen(intervalMs, listener) {
    ExpoAccelerometer.setUpdateInterval(intervalMs);
    const subscription = ExpoAccelerometer.addListener(listener);
    return () => subscription.remove();
  },
};

type SensorContextValue = { client: WT901Client; phone: PhoneSensor };

const SensorContext = createContext<SensorContextValue | null>(null);

export function SensorProvider({ children }: { children: ReactNode }) {
  const { settings, loaded } = useSettings();
  const value = useMemo(
    () => ({
      client: new WT901Client(bleManagerTransport, settings.sensorId, Date.now, (m) => console.log(`[sensor] ${m}`)),
      phone: new PhoneSensor(expoAccelerometer),
    }),
    // Created once; sensor changes go through setSensor().
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
  const { client, phone } = value;
  // The ESP32 display never sleeps; keep the phone screen on while open.
  useKeepAwake();

  useEffect(() => {
    if (!loaded) return;
    void client.setSensor(settings.sensorId);
  }, [client, loaded, settings.sensorId]);

  useEffect(() => {
    if (!loaded) return;
    const source = settings.source;
    const startSource = () => {
      if (source === 'phone') {
        void client.stop();
        void phone.start();
      } else {
        phone.stop();
        void client.start();
      }
    };
    const stopAll = () => {
      phone.stop();
      void client.stop();
    };
    if (AppState.currentState === 'active') startSource();
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') startSource();
      else if (state === 'background') stopAll();
    });
    const timer = setInterval(() => {
      if (source === 'wt901') client.maintain();
    }, SENSOR_MAINTAIN_INTERVAL_MS);
    return () => {
      subscription.remove();
      clearInterval(timer);
      stopAll();
    };
  }, [client, phone, loaded, settings.source]);

  return <SensorContext.Provider value={value}>{children}</SensorContext.Provider>;
}

function useSensors(): SensorContextValue {
  const value = useContext(SensorContext);
  if (value === null) throw new Error('useSensor needs a SensorProvider');
  return value;
}

export function useSensorClient(): WT901Client {
  return useSensors().client;
}

export type SensorView = {
  source: SensorSource;
  shown: DisplayState;
  /** Vehicle pitch and roll before the level reference, or null without data. */
  raw: Attitude | null;
  /** Changes with every new reading. */
  sequence: number;
  battery: PowerReading | null;
};

/** The active source's latest reading and the state to show, re-checked for staleness. */
export function useSensor(): SensorView {
  const { client, phone } = useSensors();
  const { settings } = useSettings();
  const wt901 = useSyncExternalStore(client.subscribe, client.getSnapshot);
  const own = useSyncExternalStore(phone.subscribe, phone.getSnapshot);
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), SENSOR_MAINTAIN_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);
  const time = Math.max(now, Date.now());
  if (settings.source === 'phone') {
    return { source: 'phone', shown: phoneDisplayState(own, time), raw: own.raw, sequence: own.sequence, battery: null };
  }
  return {
    source: 'wt901',
    shown: displayState(wt901, time),
    raw: wt901.latest ? sensorToVehicle(wt901.latest) : null,
    sequence: wt901.sequence,
    battery: wt901.battery,
  };
}
