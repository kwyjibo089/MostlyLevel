/**
 * CALIBRATE acts only after a 1 s hold, like on the ESP32, so a stray touch
 * cannot overwrite the level reference. The fill shows the hold progress;
 * releasing early cancels.
 */

import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { LONG_PRESS_MS } from '../config';
import { colours, fonts } from '../theme';

type Props = { label: string; hint: string; onCalibrate: () => void };

export function CalibrateButton({ label, hint, onCalibrate }: Props) {
  const [progress, setProgress] = useState(0);
  const start = useRef<number | null>(null);
  const frame = useRef(0);

  const stop = () => {
    start.current = null;
    cancelAnimationFrame(frame.current);
    setProgress(0);
  };

  const tick = () => {
    if (start.current === null) return;
    const held = Date.now() - start.current;
    if (held >= LONG_PRESS_MS) {
      stop();
      onCalibrate();
      return;
    }
    setProgress(held / LONG_PRESS_MS);
    frame.current = requestAnimationFrame(tick);
  };

  useEffect(() => () => cancelAnimationFrame(frame.current), []);

  return (
    <Pressable
      onPressIn={() => {
        start.current = Date.now();
        frame.current = requestAnimationFrame(tick);
      }}
      onPressOut={stop}
      accessibilityRole="button"
      accessibilityLabel={`${label}, ${hint}`}
      style={styles.button}
    >
      <View style={[styles.fill, { width: `${Math.round(progress * 100)}%` }]} />
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.hint}>{hint}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flex: 1,
    height: 56,
    borderRadius: 16,
    backgroundColor: colours.calibrate,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fill: { position: 'absolute', left: 0, top: 0, bottom: 0, backgroundColor: colours.calibrateFill },
  label: { fontFamily: fonts.bold, fontSize: 17, color: '#1A1500' },
  hint: { fontFamily: fonts.medium, fontSize: 12, color: 'rgba(26,21,0,0.75)' },
});
