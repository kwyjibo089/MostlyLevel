/**
 * LEVELLING top view: the camper from above, front at the top, each wheel
 * labelled with its lift. 2 WEDGES highlights and ranks the two corners to
 * lift; 4 CORNERS shows all four values, like the ESP32 page.
 */

import Svg, { Circle, G, Rect, Text as SvgText } from 'react-native-svg';

import type { CamperType } from '../campers';
import { NO_WEDGE_NEEDED_THRESHOLD_CM } from '../config';
import { formatCm, Translate } from '../i18n';
import { Corner, CornerLifts } from '../levelling';
import { colours, fonts } from '../theme';
import { Art, ArtDefs } from './VanArt';

type Props = {
  type: CamperType;
  /** Body colour. */
  colour: string;
  lifts: CornerLifts | null;
  mode: 'wedges' | 'corners';
  /** 2 WEDGES ranking, or 'level'; null without data. */
  advice: 'level' | [Corner, Corner] | null;
  t: Translate;
};

export function PlanView({ type, colour, lifts, mode, advice, t }: Props) {
  const { meta } = type;
  const s = 0.37; // px per cm
  const bh = meta.length * s;
  const bw = meta.width * s;
  const bx = 178 - bw / 2;
  const by = 44 + (270 - bh) / 2;
  const wh = Math.round(meta.wheel * 2 * s + 6);
  const frontY = by + (meta.length - meta.axles[1]) * s;
  const rearY = by + (meta.length - meta.axles[0]) * s;
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

  return (
    <Svg width="100%" height="100%" viewBox="0 0 356 340" accessibilityLabel="Camper seen from above with lift per wheel">
      <ArtDefs />
      <SvgText x={178} y={24} fill={colours.muted} fontSize={13} fontFamily={fonts.medium} textAnchor="middle">
        {`▲ ${t('front')}`}
      </SvgText>
      {corner('front_left', true, frontY)}
      {corner('front_right', false, frontY)}
      {corner('rear_left', true, rearY)}
      {corner('rear_right', false, rearY)}
      <G transform={`translate(178 ${by}) scale(${s})`}>
        <Art shapes={type.top} colour={colour} />
      </G>
    </Svg>
  );
}
