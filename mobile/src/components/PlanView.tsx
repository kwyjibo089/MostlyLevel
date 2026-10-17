/**
 * LEVELLING top view: the camper from above, front at the top, each wheel
 * labelled with its lift. 2 WEDGES highlights and ranks the two corners to
 * lift; 4 CORNERS shows all four values, like the ESP32 page.
 */

import Svg, { Circle, G, Path, Rect, Text as SvgText } from 'react-native-svg';

import { CamperType, Paint } from '../campers';
import { NO_WEDGE_NEEDED_THRESHOLD_CM } from '../config';
import { formatCm, Translate } from '../i18n';
import { Corner, CornerLifts } from '../levelling';
import { colours, fonts } from '../theme';

type Props = {
  type: CamperType;
  paint: Paint;
  lifts: CornerLifts | null;
  mode: 'wedges' | 'corners';
  /** 2 WEDGES ranking, or 'level'; null without data. */
  advice: 'level' | [Corner, Corner] | null;
  t: Translate;
};

export function PlanView({ type, paint, lifts, mode, advice, t }: Props) {
  const s = 3.7;
  const bh = type.length * s;
  const bw = type.width * 4.6;
  const bx = 178 - bw / 2;
  const by = 44 + (270 - bh) / 2;
  const wh = Math.round(type.wheelRadius * 2 * s + 6);
  const frontY = by + (type.length - type.axles[1]) * s;
  const rearY = by + (type.length - type.axles[0]) * s;
  const ws = by + type.windscreen * s;
  const level = advice === 'level';
  const ranked: Corner[] = Array.isArray(advice) ? advice : [];

  const corner = (key: Corner, left: boolean, cy: number) => {
    const lift = lifts ? lifts[key] : null;
    const rank = mode === 'wedges' ? ranked.indexOf(key) : -1;
    const shown = mode === 'corners' || rank >= 0 || lifts === null;
    let wheel: string = '#2B323D';
    if (lifts && level && mode === 'wedges') wheel = colours.level;
    else if (lift !== null && lift >= NO_WEDGE_NEEDED_THRESHOLD_CM && (mode === 'corners' || rank >= 0)) wheel = colours.lift;
    const wheelX = left ? bx - 10 : bx + bw - 6;
    const labelX = left ? bx - 22 : bx + bw + 22;
    const anchor = left ? 'end' : 'start';
    const badgeX = left ? bx - 2 : bx + bw + 2;
    const value = mode === 'wedges' && lifts && rank < 0 ? '–' : formatCm(lift, t);
    return (
      <G key={key}>
        <Rect x={wheelX} y={cy - wh / 2} width={16} height={wh} rx={5} fill={wheel} />
        <SvgText x={labelX} y={cy - 6} fill={colours.muted} fontSize={13} fontFamily={fonts.medium} textAnchor={anchor}>
          {t(key)}
        </SvgText>
        <SvgText
          x={labelX}
          y={cy + 20}
          fill={shown && !(mode === 'wedges' && level) ? '#FFFFFF' : '#55606E'}
          fontSize={24}
          fontFamily={fonts.number}
          textAnchor={anchor}
        >
          {value}
        </SvgText>
        {rank >= 0 && (
          <G>
            <Circle cx={badgeX} cy={cy - wh / 2 - 14} r={12} fill={colours.lift} />
            <SvgText x={badgeX} y={cy - wh / 2 - 9} fill="#1A1000" fontSize={14} fontFamily={fonts.bold} textAnchor="middle">
              {String(rank + 1)}
            </SvgText>
          </G>
        )}
      </G>
    );
  };

  const screen =
    `M${bx + 6} ${ws} Q178 ${ws - 7} ${bx + bw - 6} ${ws} ` +
    `L${bx + bw - 10} ${ws + 15} Q178 ${ws + 9} ${bx + 10} ${ws + 15} Z`;
  const my = ws + 10;
  const mirrors = `M${bx - 7} ${my} h7 v6 h-7 Z M${bx + bw} ${my} h7 v6 h-7 Z`;
  const roofY = by + bh * 0.45;
  const roof = `M${178 - bw * 0.22} ${roofY} h${bw * 0.44} v${bw * 0.34} h${-bw * 0.44} Z`;

  return (
    <Svg width="100%" height="100%" viewBox="0 0 356 340" accessibilityLabel="Camper seen from above with lift per wheel">
      <SvgText x={178} y={24} fill={colours.muted} fontSize={13} fontFamily={fonts.medium} textAnchor="middle">
        {`▲ ${t('front')}`}
      </SvgText>
      {corner('front_left', true, frontY)}
      {corner('front_right', false, frontY)}
      {corner('rear_left', true, rearY)}
      {corner('rear_right', false, rearY)}
      <Rect x={bx} y={by} width={bw} height={bh} rx={Math.min(24, bw * 0.22)} fill={paint.body} stroke={paint.planEdge} strokeWidth={1} />
      <Path d={screen} fill="#26313C" />
      <Path d={mirrors} fill="#2B3036" />
      <Path d={roof} fill={paint.roof} />
    </Svg>
  );
}
