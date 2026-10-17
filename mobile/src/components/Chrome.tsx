/** Header, bottom navigation, and the level/warning overlays around the pages. */

import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import type { TextKey, Translate } from '../i18n';
import type { DisplayState } from '../sensor/client';
import { colours, fonts } from '../theme';
import { AttitudeIcon, BatteryIcon, GearIcon, LevellingIcon, WarningIcon } from './ui';

// Text keys of the states shown in the header, as on the ESP32.
const STATUS_KEYS: Record<DisplayState, TextKey> = {
  LIVE: 'status_live',
  SCANNING: 'status_scanning',
  CONNECTING: 'status_connecting',
  DISCOVERING: 'status_setup',
  'SETTING UP': 'status_setup',
  DISCONNECTING: 'status_disconnected',
  DISCONNECTED: 'status_disconnected',
  'NO DATA': 'status_stale',
  WAIT: 'status_wait',
  ERROR: 'status_error',
  IDLE: 'status_idle',
  'BLUETOOTH OFF': 'status_bluetooth_off',
  'NO PERMISSION': 'status_no_permission',
};

const WARN_STATES: DisplayState[] = ['ERROR', 'DISCONNECTED', 'NO DATA', 'BLUETOOTH OFF', 'NO PERMISSION'];

function statusColour(state: DisplayState): string {
  if (state === 'LIVE') return colours.level;
  return WARN_STATES.includes(state) ? colours.warning : colours.accent;
}

export function warningText(state: DisplayState, t: Translate): string {
  switch (state) {
    case 'NO DATA':
      return t('warning_stale');
    case 'DISCONNECTED':
    case 'ERROR':
      return t('warning_disconnected');
    case 'BLUETOOTH OFF':
      return t('warning_bluetooth_off');
    case 'NO PERMISSION':
      return t('warning_no_permission');
    default:
      return t('warning_waiting');
  }
}

type HeaderProps = {
  state: DisplayState;
  batteryPercent: number | null;
  onSettings: () => void;
  t: Translate;
};

export function Header({ state, batteryPercent, onSettings, t }: HeaderProps) {
  const colour = statusColour(state);
  return (
    <View style={styles.header}>
      <View style={styles.brand}>
        <Svg width={28} height={28} viewBox="0 0 28 28">
          <Rect x={1} y={1} width={26} height={26} rx={8} fill={colours.selected} />
          <Path d="M6 17 L22 17" stroke={colours.level} strokeWidth={2.5} strokeLinecap="round" />
          <Circle cx={14} cy={11} r={3} fill={colours.accent} />
        </Svg>
        <Text style={styles.wordmark}>
          Mostly<Text style={{ color: colours.accent }}>Level</Text>
        </Text>
      </View>
      <View style={styles.right}>
        <View style={styles.chip}>
          <View style={[styles.dot, { backgroundColor: colour }]} />
          <Text style={[styles.chipText, { color: colour }]} numberOfLines={1}>
            {t(STATUS_KEYS[state])}
          </Text>
          {batteryPercent !== null && (
            <>
              <View style={styles.chipDivider} />
              <BatteryIcon percent={batteryPercent} />
              <Text style={[styles.chipNumber, { color: colours.textSoft }]}>{batteryPercent}%</Text>
            </>
          )}
        </View>
        <Pressable onPress={onSettings} style={styles.iconButton} accessibilityRole="button" accessibilityLabel={t('settings')}>
          <GearIcon />
        </Pressable>
      </View>
    </View>
  );
}

type NavProps = { page: 'attitude' | 'levelling'; onPage: (page: 'attitude' | 'levelling') => void; t: Translate; bottomInset: number };

export function BottomNav({ page, onPage, t, bottomInset }: NavProps) {
  const item = (key: 'attitude' | 'levelling', label: string) => {
    const selected = page === key;
    const colour = selected ? '#FFFFFF' : colours.faint;
    return (
      <Pressable
        key={key}
        onPress={() => onPage(key)}
        style={styles.navItem}
        accessibilityRole="tab"
        accessibilityState={{ selected }}
      >
        <View style={[styles.navPill, selected && { backgroundColor: colours.selected }]}>
          {key === 'attitude' ? <AttitudeIcon colour={colour} /> : <LevellingIcon colour={colour} />}
        </View>
        <Text style={[styles.navText, { color: colour }]}>{label}</Text>
      </Pressable>
    );
  };
  return (
    <View style={[styles.nav, { paddingBottom: bottomInset, height: 80 + bottomInset }]} accessibilityRole="tablist">
      {item('attitude', t('nav_attitude'))}
      {item('levelling', t('nav_levelling'))}
    </View>
  );
}

export function SensorWarning({ text }: { text: string }) {
  return (
    <View style={styles.warning} pointerEvents="none" accessibilityLiveRegion="polite">
      <WarningIcon />
      <Text style={styles.warningText}>{text}</Text>
    </View>
  );
}

/** Green frame while level; red while the sensor data is missing. */
export function StatusFrame({ level, warn }: { level: boolean; warn: boolean }) {
  if (!level && !warn) return null;
  return (
    <View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, { borderWidth: level ? 6 : 4, borderColor: level ? colours.level : colours.danger }]}
    />
  );
}

export function Toast({ text, ok }: { text: string; ok: boolean }) {
  return (
    <View style={[styles.toast, { backgroundColor: ok ? colours.saved : colours.refused }]} pointerEvents="none" accessibilityLiveRegion="polite">
      <Text style={styles.toastText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    height: 60,
    paddingLeft: 16,
    paddingRight: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 1 },
  wordmark: { fontFamily: fonts.bold, fontSize: 19, color: colours.text },
  right: { flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 1, marginLeft: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    height: 30,
    paddingHorizontal: 12,
    borderRadius: 15,
    backgroundColor: colours.surface,
    borderWidth: 1,
    borderColor: colours.border,
  },
  chipText: { fontFamily: fonts.semibold, fontSize: 13, flexShrink: 1 },
  chipDivider: { width: 1, height: 14, backgroundColor: colours.borderStrong, marginHorizontal: 2 },
  chipNumber: { fontFamily: fonts.number, fontSize: 15 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colours.border,
    backgroundColor: colours.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nav: { flexDirection: 'row', borderTopWidth: 1, borderTopColor: '#1F252E', backgroundColor: colours.navBar },
  navItem: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4 },
  navPill: { width: 64, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  navText: { fontFamily: fonts.semibold, fontSize: 13 },
  warning: {
    position: 'absolute',
    left: 24,
    right: 24,
    top: '38%',
    paddingVertical: 18,
    paddingHorizontal: 20,
    borderRadius: 18,
    backgroundColor: 'rgba(23,27,34,0.96)',
    borderWidth: 1.5,
    borderColor: colours.danger,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  warningText: { flex: 1, fontFamily: fonts.semibold, fontSize: 17, color: colours.warningText },
  toast: {
    position: 'absolute',
    left: 24,
    right: 24,
    bottom: 170,
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: 14,
  },
  toastText: { fontFamily: fonts.semibold, fontSize: 15, color: '#FFFFFF', textAlign: 'center' },
});
