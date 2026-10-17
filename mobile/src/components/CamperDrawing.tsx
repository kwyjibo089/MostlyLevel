/** The chosen camper drawn from the side or from behind, as SVG groups. */

import { Circle, G, Path } from 'react-native-svg';

import { archShadows, CamperType, Paint } from '../campers';

const GLASS = '#1B2731';
const TRIM = '#2B3036';
const TAIL = '#D9342B';
const HEAD = '#FFF4C2';
const PLATE = '#E9ECEF';
const TYRE = '#14171A';
const RIM = '#A9B1BA';
const HUB = '#5A626C';

type Props = { type: CamperType; paint: Paint; transform?: string; details?: boolean };

export function SideCamper({ type, paint, transform, details = true }: Props) {
  const { side } = type;
  const r = type.wheelRadius;
  return (
    <G transform={transform}>
      <Path d={archShadows(type)} fill="#15181C" />
      <Path d={side.body} fill={paint.body} stroke={paint.outline} strokeWidth={0.22} strokeLinejoin="round" />
      <Path d={side.accent} fill={paint.accent} />
      <Path d={side.glass} fill={GLASS} />
      <Path d={side.trim} fill={TRIM} />
      {details && <Path d={side.seam} fill="none" stroke={paint.seam} strokeWidth={0.2} strokeLinecap="round" />}
      <Path d={side.head} fill={HEAD} />
      <Path d={side.tail} fill={TAIL} />
      {type.axles.map((x) => (
        <G key={x}>
          <Circle cx={x} cy={-r} r={r} fill={TYRE} />
          <Circle cx={x} cy={-r} r={r * 0.58} fill={RIM} />
          {details && <Circle cx={x} cy={-r} r={r * 0.22} fill={HUB} />}
        </G>
      ))}
    </G>
  );
}

export function RearCamper({ type, paint, transform, details = true }: Props) {
  const { rear } = type;
  return (
    <G transform={transform}>
      <Path d={rear.body} fill={paint.body} stroke={paint.outline} strokeWidth={0.22} strokeLinejoin="round" />
      <Path d={rear.accent} fill={paint.accent} />
      <Path d={rear.glass} fill={GLASS} />
      <Path d={rear.trim} fill={TRIM} />
      <Path d={rear.tail} fill={TAIL} />
      <Path d={rear.plate} fill={PLATE} />
      {details && <Path d={rear.seam} fill="none" stroke={paint.seam} strokeWidth={0.2} strokeLinecap="round" />}
    </G>
  );
}
