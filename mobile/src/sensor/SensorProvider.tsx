/**
 * Runs the WT901 client for the app: connects while the app is in the
 * foreground and lets go of the sensor in the background (the sensor accepts
 * one connection at a time, so the ESP32 display can then use it).
 */

import { useKeepAwake } from 'expo-keep-awake';
import { createContext, ReactNode, useContext, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { AppState } from 'react-native';

import { SENSOR_MAINTAIN_INTERVAL_MS } from '../config';
import { useSettings } from '../settings/SettingsProvider';
import { bleManagerTransport } from './bleManagerTransport';
import { DisplayState, displayState, Snapshot, WT901Client } from './client';

type SensorContextValue = { client: WT901Client };

const SensorContext = createContext<SensorContextValue | null>(null);

export function SensorProvider({ children }: { children: ReactNode }) {
  const { settings, loaded } = useSettings();
  const client = useMemo(
    () => new WT901Client(bleManagerTransport, settings.sensorId, Date.now, (m) => console.log(`[sensor] ${m}`)),
    // The client is created once; sensor changes go through setSensor().
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
  // The ESP32 display never sleeps; keep the phone screen on while open.
  useKeepAwake();

  useEffect(() => {
    if (!loaded) return;
    void client.setSensor(settings.sensorId);
  }, [client, loaded, settings.sensorId]);

  useEffect(() => {
    if (!loaded) return;
    if (AppState.currentState === 'active') void client.start();
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') void client.start();
      else if (state === 'background') void client.stop();
    });
    const timer = setInterval(() => client.maintain(), SENSOR_MAINTAIN_INTERVAL_MS);
    return () => {
      subscription.remove();
      clearInterval(timer);
      void client.stop();
    };
  }, [client, loaded]);

  const value = useMemo(() => ({ client }), [client]);
  return <SensorContext.Provider value={value}>{children}</SensorContext.Provider>;
}

export function useSensorClient(): WT901Client {
  const value = useContext(SensorContext);
  if (value === null) throw new Error('useSensorClient needs a SensorProvider');
  return value.client;
}

/** The latest sensor snapshot and the state to show, re-checked for staleness. */
export function useSensor(): { snapshot: Snapshot; shown: DisplayState } {
  const client = useSensorClient();
  const snapshot = useSyncExternalStore(client.subscribe, client.getSnapshot);
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), SENSOR_MAINTAIN_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);
  return { snapshot, shown: displayState(snapshot, Math.max(now, Date.now())) };
}
