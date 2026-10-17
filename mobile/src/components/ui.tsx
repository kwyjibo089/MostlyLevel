/** Small shared building blocks: text styles, cards, segmented control, icons. */

import { ReactNode } from 'react';
import { Pressable, StyleProp, StyleSheet, Text, TextProps, View, ViewStyle } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import { colours, fonts } from '../theme';

export function Label({ style, ...props }: TextProps) {
  return <Text {...props} style={[styles.label, style]} />;
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

type Option<T extends string> = { value: T; label: string };

export function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: Option<T>[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <View style={styles.segmented} accessibilityRole="tablist">
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.value}
            onPress={() => onChange(option.value)}
            accessibilityRole="tab"
            accessibilityState={{ selected }}
            style={[styles.segment, selected && styles.segmentSelected]}
          >
            <Text style={[styles.segmentText, selected && styles.segmentTextSelected]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function GearIcon({ colour = colours.textSoft }: { colour?: string }) {
  return (
    <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke={colour} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <Circle cx={12} cy={12} r={3.5} />
      <Path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
    </Svg>
  );
}

export function GlobeIcon({ colour = colours.accent }: { colour?: string }) {
  return (
    <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={colour} strokeWidth={2}>
      <Circle cx={12} cy={12} r={9} />
      <Path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" />
    </Svg>
  );
}

export function BatteryIcon({ percent }: { percent: number }) {
  return (
    <Svg width={18} height={12} viewBox="0 0 18 12">
      <Rect x={0.75} y={0.75} width={14.5} height={10.5} rx={2.5} fill="none" stroke={colours.textSoft} strokeWidth={1.5} />
      <Rect x={16} y={4} width={1.5} height={4} rx={0.75} fill={colours.textSoft} />
      <Rect x={2.5} y={2.5} width={Math.max(1, (11 * percent) / 100)} height={7} rx={1.2} fill={colours.level} />
    </Svg>
  );
}

export function WarningIcon() {
  return (
    <Svg width={28} height={28} viewBox="0 0 24 24" fill="none" stroke={colours.warning} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round">
      <Path d="M12 3 L22 20 H2 Z" />
      <Path d="M12 10v4M12 17v.5" />
    </Svg>
  );
}

export function CheckIcon() {
  return (
    <Svg width={36} height={36} viewBox="0 0 24 24" fill="none" stroke={colours.level} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
      <Circle cx={12} cy={12} r={10} />
      <Path d="M7 12.5l3.2 3.2L17 9" />
    </Svg>
  );
}

export function AttitudeIcon({ colour }: { colour: string }) {
  return (
    <Svg width={24} height={24} viewBox="0 0 24 24" fill="none" stroke={colour} strokeWidth={2} strokeLinejoin="round">
      <Path d="M3 15.5 L19 11 L20 15 L4 19.5 Z" />
      <Circle cx={7.5} cy={19} r={1.6} />
      <Circle cx={16.5} cy={16.5} r={1.6} />
      <Path d="M2 21.5 H22" strokeLinecap="round" />
    </Svg>
  );
}

export function LevellingIcon({ colour }: { colour: string }) {
  return (
    <Svg width={24} height={24} viewBox="0 0 24 24" fill="none" stroke={colour} strokeWidth={2} strokeLinejoin="round">
      <Path d="M3 19 L21 19 L21 12 Z" />
      <Path d="M3 9 H13" strokeLinecap="round" />
      <Circle cx={8} cy={9} r={1.6} />
    </Svg>
  );
}

export const styles = StyleSheet.create({
  label: { fontFamily: fonts.medium, color: colours.text, fontSize: 15 },
  card: {
    backgroundColor: colours.surface,
    borderColor: colours.border,
    borderWidth: 1,
    borderRadius: 20,
    overflow: 'hidden',
  },
  segmented: {
    flexDirection: 'row',
    gap: 4,
    padding: 4,
    backgroundColor: colours.surface,
    borderColor: colours.border,
    borderWidth: 1,
    borderRadius: 14,
  },
  segment: { flex: 1, height: 40, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  segmentSelected: { backgroundColor: colours.selected, borderWidth: 1, borderColor: colours.accent },
  segmentText: { fontFamily: fonts.semibold, fontSize: 15, color: colours.muted },
  segmentTextSelected: { color: '#FFFFFF' },
});
