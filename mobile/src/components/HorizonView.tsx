/**
 * HORIZON view: aircraft-style attitude indicator with the camper seen from
 * behind as the fixed symbol. As on the ESP32 (owner choice 2026-10-16),
 * positive roll (left side high) banks to the right, so the horizon rises on
 * the right; positive pitch (front up) moves the horizon down.
 */

import { StyleSheet, View } from 'react-native';
import Svg, { G, Line, Path, Rect, Text as SvgText } from 'react-native-svg';

import { CamperType, Paint } from '../campers';
import { HORIZON_PIXELS_PER_DEGREE } from '../config';
import { clamp } from '../levelling';
import { colours, fonts } from '../theme';
import { RearCamper } from './CamperDrawing';

const C = 170; // Centre of the 340 × 340 drawing.

// Bank scale ticks: [x1, y1, x2, y2] for 0, ±10, ±20, ±30, ±45, ±60 degrees.
const TICKS = [
  [170, 30, 170, 44],
  [194.3, 32.1, 193.1, 39], [145.7, 32.1, 146.9, 39],
  [217.9, 38.4, 215.5, 45], [122.1, 38.4, 124.5, 45],
  [240, 48.8, 234, 59.1], [100, 48.8, 106, 59.1],
  [269, 71, 263.3, 76.7], [71, 71, 76.7, 76.7],
  [291.2, 100, 280.8, 106], [48.8, 100, 59.2, 106],
];
const LADDER = [20, 15, 10, 5, -5, -10, -15, -20];

export function HorizonView({ pitch, roll, type, paint }: { pitch: number; roll: number; type: CamperType; paint: Paint }) {
  const rotation = -clamp(roll, -45, 45);
  const shift = clamp(pitch, -35, 35) * HORIZON_PIXELS_PER_DEGREE;
  const symbolScale = 62 / type.height;
  return (
    <View style={styles.frame}>
      <Svg width="100%" height="100%" viewBox="-9 -9 358 358" accessibilityLabel="Virtual horizon">
        <G transform={`rotate(${rotation} ${C} ${C}) translate(0 ${shift})`}>
          <Rect x={-400} y={-600} width={1140} height={770} fill={colours.sky} />
          <Rect x={-400} y={C} width={1140} height={770} fill={colours.ground} />
          <Rect x={-400} y={C - 1} width={1140} height={2.5} fill="#FFFFFF" />
          {LADDER.map((mark) => {
            const y = C - mark * HORIZON_PIXELS_PER_DEGREE;
            const major = mark % 10 === 0;
            const half = major ? 40 : 20;
            return (
              <G key={mark}>
                <Rect x={C - half} y={y - 1} width={half * 2} height={2} fill="#FFFFFF" />
                {major && (
                  <>
                    <SvgText x={C - half - 8} y={y + 4} fill="#FFFFFF" fontSize={12} fontFamily={fonts.semibold} textAnchor="end">
                      {mark < 0 ? `−${-mark}` : `${mark}`}
                    </SvgText>
                    <SvgText x={C + half + 8} y={y + 4} fill="#FFFFFF" fontSize={12} fontFamily={fonts.semibold} textAnchor="start">
                      {mark < 0 ? `−${-mark}` : `${mark}`}
                    </SvgText>
                  </>
                )}
              </G>
            );
          })}
        </G>
        <Path d="M48.8 100 A140 140 0 0 1 291.2 100" fill="none" stroke="#FFFFFF" strokeWidth={2} />
        {TICKS.map(([x1, y1, x2, y2], index) => (
          <Line key={index} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#FFFFFF" strokeWidth={2} strokeLinecap="round" />
        ))}
        <G transform={`rotate(${rotation} ${C} ${C})`}>
          <Path d="M170 46 L163 58 L177 58 Z" fill="#FFFFFF" />
        </G>
        <RearCamper type={type} paint={paint} details={false} transform={`translate(${C} 200) scale(${symbolScale})`} />
        <Path d="M170 204 L162 216 L178 216 Z" fill={colours.calibrate} />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  frame: { width: '100%', aspectRatio: 1, borderRadius: 28, overflow: 'hidden', backgroundColor: colours.sky },
});
