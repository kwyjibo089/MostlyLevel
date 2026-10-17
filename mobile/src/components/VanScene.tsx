/**
 * VAN view card: the camper from behind (tilting with roll) or from the side
 * (tilting with pitch), standing on level ground and pivoting on its lower
 * wheel. The tilt is exaggerated like on the ESP32; the readout is true.
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Rect } from 'react-native-svg';

import { CamperType, Paint } from '../campers';
import { formatSigned, Translate } from '../i18n';
import { axisLevel, vanTilt } from '../levelling';
import { colours, fonts } from '../theme';
import { RearCamper, SideCamper } from './CamperDrawing';
import { Card } from './ui';

const SCENE_W = 356;
const SCENE_H = 210;
const GROUND_Y = 186;

type Props = {
  view: 'rear' | 'side';
  type: CamperType;
  paint: Paint;
  /** True angle for the readout, null without data. */
  angle: number | null;
  /** Smoothed angle for the drawing. */
  drawnAngle: number;
  t: Translate;
};

export function hintFor(view: 'rear' | 'side', angle: number | null, t: Translate) {
  if (angle === null) return { text: ' ', level: false };
  if (axisLevel(angle)) return { text: t('level'), level: true };
  if (view === 'side') return { text: t(angle > 0 ? 'front_high' : 'rear_high'), level: false };
  return { text: t(angle > 0 ? 'left_high' : 'right_high'), level: false };
}

export function VanScene({ view, type, paint, angle, drawnAngle, t }: Props) {
  const hint = hintFor(view, angle, t);
  const groundLevel = angle !== null && axisLevel(angle);
  let drawing;
  if (view === 'rear') {
    // Positive roll lifts the left side: seen from behind, clockwise.
    const tilt = vanTilt(drawnAngle);
    const scale = Math.min(118 / type.width, 128 / type.height);
    const pivot = tilt > 0 ? type.rearPivot : -type.rearPivot;
    drawing = (
      <RearCamper
        type={type}
        paint={paint}
        transform={`translate(${SCENE_W / 2} ${GROUND_Y}) scale(${scale}) rotate(${tilt} ${pivot} 0)`}
      />
    );
  } else {
    // Positive pitch lifts the front, which faces right: anticlockwise.
    const tilt = -vanTilt(drawnAngle);
    const scale = Math.min(236 / type.length, 118 / type.height);
    const pivot = tilt > 0 ? type.axles[1] : type.axles[0];
    const mid = (type.axles[0] + type.axles[1]) / 2;
    drawing = (
      <SideCamper
        type={type}
        paint={paint}
        transform={`translate(${SCENE_W / 2} ${GROUND_Y}) scale(${scale}) translate(${-mid} 0) rotate(${tilt} ${pivot} 0)`}
      />
    );
  }

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>{t(view === 'rear' ? 'roll' : 'pitch')}</Text>
          <Text style={styles.subtitle}>{t(view === 'rear' ? 'seen_behind' : 'seen_side')}</Text>
        </View>
        <View style={styles.readout}>
          <Text style={styles.value}>{angle === null ? `--${t('decimal')}-°` : `${formatSigned(angle, t)}°`}</Text>
          <Text style={[styles.hint, hint.level && { color: colours.level }]}>{hint.text}</Text>
        </View>
      </View>
      <View style={styles.scene}>
        <Svg width="100%" height="100%" viewBox={`0 0 ${SCENE_W} ${SCENE_H}`} preserveAspectRatio="xMidYMax meet">
          <Rect x={-2000} y={GROUND_Y} width={4356} height={400} fill={colours.ground} />
          <Rect x={-2000} y={GROUND_Y} width={4356} height={3} fill={groundLevel ? colours.level : '#FFFFFF'} />
          {drawing}
        </Svg>
        {view === 'side' && <Text style={styles.exaggerated}>{t('tilt_exaggerated')}</Text>}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { flex: 1 },
  header: {
    height: 58,
    paddingHorizontal: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: { fontFamily: fonts.semibold, fontSize: 17, color: colours.text },
  subtitle: { fontFamily: fonts.regular, fontSize: 13, color: colours.muted },
  readout: { alignItems: 'flex-end' },
  value: { fontFamily: fonts.number, fontSize: 30, lineHeight: 32, color: colours.text },
  hint: { fontFamily: fonts.regular, fontSize: 13, color: colours.muted },
  scene: { flex: 1, backgroundColor: colours.sky, overflow: 'hidden' },
  exaggerated: {
    position: 'absolute',
    right: 12,
    top: 10,
    fontFamily: fonts.regular,
    fontSize: 12,
    color: 'rgba(255,255,255,0.85)',
  },
});
