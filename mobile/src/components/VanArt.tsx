/**
 * Renders the generated camper drawings (vanArt.ts) with react-native-svg.
 *
 * Put <ArtDefs /> once inside each <Svg> that shows a drawing: the shapes
 * refer to its gradients by id. <Art> is memoised, so a tilting van only
 * re-renders the transform of its parent group, not its many shapes.
 */

import { memo } from 'react';
import { Circle, Defs, Ellipse, LinearGradient, Path, RadialGradient, Rect, Stop } from 'react-native-svg';

import { ART_GRADIENTS } from '../vanArt';
import type { ArtShape } from '../vanArtTypes';

export const ArtDefs = memo(function ArtDefs() {
  return (
    <Defs>
      {ART_GRADIENTS.map((g) => {
        const stops = g.stops.map(([offset, colour, opacity], index) => (
          <Stop key={index} offset={offset} stopColor={colour} stopOpacity={opacity} />
        ));
        return g.kind === 'linear' ? (
          <LinearGradient key={g.id} id={g.id} x1={g.x1} y1={g.y1} x2={g.x2} y2={g.y2}>
            {stops}
          </LinearGradient>
        ) : (
          <RadialGradient key={g.id} id={g.id} cx={g.cx} cy={g.cy} r={g.r}>
            {stops}
          </RadialGradient>
        );
      })}
    </Defs>
  );
});

function shape(s: ArtShape, index: number, colour: string) {
  const paint = {
    fill: s.body ? colour : s.fill,
    stroke: s.stroke,
    strokeWidth: s.sw,
    strokeLinecap: s.lc,
    opacity: s.op,
  };
  switch (s.t) {
    case 'path':
      return <Path key={index} d={s.d} {...paint} />;
    case 'rect':
      return <Rect key={index} x={s.x} y={s.y} width={s.w} height={s.h} rx={s.rx} {...paint} />;
    case 'circle':
      return <Circle key={index} cx={s.cx} cy={s.cy} r={s.r} {...paint} />;
    case 'ellipse':
      return <Ellipse key={index} cx={s.cx} cy={s.cy} rx={s.rx} ry={s.ry} {...paint} />;
  }
}

/** The shapes of one view, with `colour` as the body colour. */
export const Art = memo(function Art({ shapes, colour }: { shapes: ArtShape[]; colour: string }) {
  return <>{shapes.map((s, index) => shape(s, index, colour))}</>;
});
