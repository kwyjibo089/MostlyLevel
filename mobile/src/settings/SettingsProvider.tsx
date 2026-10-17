/** User settings, saved on the phone; the ESP32 keeps these in config.py and *.cfg files. */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { BodyColour, BODY_COLOURS, CAMPERS, CamperKey, CAMPER_KEYS, DEFAULT_CAMPER, DEFAULT_COLOUR } from '../campers';
import { DEFAULT_LANGUAGE, DEFAULT_SENSOR_ID, Language, LANGUAGES } from '../config';
import { translator, Translate } from '../i18n';
import type { Dimensions, LevelReference } from '../levelling';

export type Settings = {
  language: Language;
  sensorId: string;
  camper: CamperKey;
  colour: BodyColour;
  dimensions: Dimensions;
  /** Level reference from CALIBRATE, in vehicle axes. */
  zero: LevelReference;
};

const STORAGE_KEY = 'mostlylevel.settings.v1';

export const DEFAULT_SETTINGS: Settings = {
  language: DEFAULT_LANGUAGE,
  sensorId: DEFAULT_SENSOR_ID,
  camper: DEFAULT_CAMPER,
  colour: DEFAULT_COLOUR,
  dimensions: { ...CAMPERS[DEFAULT_CAMPER].defaults },
  zero: { pitch: 0, roll: 0 },
};

/** Keep only valid stored values, so a damaged entry falls back to defaults. */
export function sanitize(stored: unknown): Settings {
  const s = (typeof stored === 'object' && stored !== null ? stored : {}) as Partial<Settings>;
  const positive = (value: unknown, fallback: number) =>
    typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : fallback;
  const finite = (value: unknown) => (typeof value === 'number' && Number.isFinite(value) ? value : 0);
  const camper = CAMPER_KEYS.includes(s.camper as CamperKey) ? (s.camper as CamperKey) : DEFAULT_SETTINGS.camper;
  const dims = s.dimensions ?? DEFAULT_SETTINGS.dimensions;
  return {
    language: LANGUAGES.includes(s.language as Language) ? (s.language as Language) : DEFAULT_SETTINGS.language,
    sensorId: typeof s.sensorId === 'string' && s.sensorId.length > 0 ? s.sensorId : DEFAULT_SETTINGS.sensorId,
    camper,
    colour: BODY_COLOURS.some((c) => c.key === s.colour) ? (s.colour as BodyColour) : DEFAULT_SETTINGS.colour,
    dimensions: {
      wheelbaseMm: positive(dims.wheelbaseMm, DEFAULT_SETTINGS.dimensions.wheelbaseMm),
      frontTrackMm: positive(dims.frontTrackMm, DEFAULT_SETTINGS.dimensions.frontTrackMm),
      rearTrackMm: positive(dims.rearTrackMm, DEFAULT_SETTINGS.dimensions.rearTrackMm),
    },
    zero: { pitch: finite(s.zero?.pitch), roll: finite(s.zero?.roll) },
  };
}

type SettingsContextValue = {
  settings: Settings;
  loaded: boolean;
  update: (patch: Partial<Settings>) => void;
  t: Translate;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((text) => {
        if (text) setSettings(sanitize(JSON.parse(text)));
      })
      .catch((error) => console.warn('Settings could not be loaded:', error))
      .finally(() => setLoaded(true));
  }, []);

  const update = useCallback((patch: Partial<Settings>) => {
    setSettings((current) => {
      const next = { ...current, ...patch };
      AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next)).catch((error) =>
        // Like the ESP32: the change stays active until restart.
        console.warn('Settings could not be saved:', error),
      );
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ settings, loaded, update, t: translator(settings.language) }),
    [settings, loaded, update],
  );
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsContextValue {
  const value = useContext(SettingsContext);
  if (value === null) throw new Error('useSettings needs a SettingsProvider');
  return value;
}
