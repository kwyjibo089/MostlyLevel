/**
 * Camper body types the user can choose, drawn as vector layers.
 *
 * Drawings are in decimetres: side views run from the rear (x = 0) to the
 * front, rear views are centred on x = 0, y up is negative and the ground is
 * y = 0. Each layer is one SVG path; EMPTY draws nothing. The shapes are
 * generic (no brand details or logos). Each type carries typical dimensions
 * that the user can adjust in settings; the panel van's are the owner's
 * (esp32/src/config.py).
 */

export const EMPTY = 'M0 0';

export type SideLayers = {
  body: string;
  accent: string;
  glass: string;
  trim: string;
  seam: string;
  head: string;
  tail: string;
};

export type RearLayers = {
  body: string;
  accent: string;
  glass: string;
  trim: string;
  tail: string;
  plate: string;
  seam: string;
};

export type CamperType = {
  /** Body length and height (dm), and width for the top view. */
  length: number;
  height: number;
  width: number;
  /** Rear and front axle positions along the side view (dm). */
  axles: [number, number];
  wheelRadius: number;
  archY: number;
  archRadius: number;
  /** Rear view: tyre centres at ±rearPivot (dm); the van pivots there. */
  rearPivot: number;
  /** Distance of the windscreen from the front, for the top view (dm). */
  windscreen: number;
  defaults: { wheelbaseMm: number; frontTrackMm: number; rearTrackMm: number };
  side: SideLayers;
  rear: RearLayers;
};

export const CAMPER_KEYS = ['compact', 'panel', 'alcove', 'semi', 'integrated'] as const;
export type CamperKey = (typeof CAMPER_KEYS)[number];
export const DEFAULT_CAMPER: CamperKey = 'panel';

const motorhomeRear: RearLayers = {
  body: 'M-11.5 -4.4 L-11.5 -27.6 Q-11.5 -29 -10.1 -29 L10.1 -29 Q11.5 -29 11.5 -27.6 L11.5 -4.4 Z',
  accent: 'M-11.5 -9.6 L11.5 -9.6 L11.5 -8.6 L-11.5 -8.6 Z M-3.4 -29 L-3 -29.8 L3 -29.8 L3.4 -29 Z',
  glass: 'M-6 -23 L6 -23 L6 -17.4 L-6 -17.4 Z',
  trim:
    'M-11.7 -7.2 L11.7 -7.2 L11.6 -4.4 L-11.6 -4.4 Z M-11.2 -4.4 h2.6 v4.4 h-2.6 Z M8.6 -4.4 h2.6 v4.4 h-2.6 Z ' +
    'M7.6 -27.6 h0.5 v17.4 h-0.5 Z M9.8 -27.6 h0.5 v17.4 h-0.5 Z M7.6 -25 h2.7 v0.4 h-2.7 Z M7.6 -22 h2.7 v0.4 h-2.7 Z ' +
    'M7.6 -19 h2.7 v0.4 h-2.7 Z M7.6 -16 h2.7 v0.4 h-2.7 Z M7.6 -13 h2.7 v0.4 h-2.7 Z',
  tail: 'M-11.5 -12.6 L-8.6 -12.6 L-8.6 -10.2 L-11.5 -10.2 Z M8.6 -12.6 L11.5 -12.6 L11.5 -10.2 L8.6 -10.2 Z',
  plate: 'M-2.6 -10.4 h5.2 v1.8 h-5.2 Z',
  seam: EMPTY,
};

const motorhomeDefaults = { wheelbaseMm: 4035, frontTrackMm: 1810, rearTrackMm: 1980 };

export const CAMPERS: Record<CamperKey, CamperType> = {
  compact: {
    length: 49, height: 20.3, width: 19, axles: [9, 39], wheelRadius: 3.3, archY: -3.8, archRadius: 4.3,
    rearPivot: 8, windscreen: 7.5, defaults: { wheelbaseMm: 3000, frontTrackMm: 1628, rearTrackMm: 1628 },
    side: {
      body:
        'M0.4 -4.2 L0.2 -16.5 Q0.3 -19.2 2.6 -19.4 L31.5 -19.4 Q33.6 -19.4 34.6 -18.2 L39.8 -12.6 Q40.6 -11.8 42 -11.5 ' +
        'L47.2 -10.4 Q48.9 -10 49 -8.2 L49 -5 Q49 -3.8 47.8 -3.8 L43.3 -3.8 A4.3 4.3 0 0 0 34.7 -3.8 L13.3 -3.8 ' +
        'A4.3 4.3 0 0 0 4.7 -3.8 L1.6 -3.8 Q0.4 -3.8 0.4 -4.2 Z',
      accent: 'M3 -19.4 L31 -19.4 Q32 -19.4 32.2 -20 L32 -20.3 L3.6 -20.3 Q2.8 -20.3 3 -19.4 Z',
      glass:
        'M2 -17.6 L11.2 -17.6 L11.2 -12.4 L1.8 -12.4 Z M12.6 -17.6 L24.4 -17.6 L24.4 -12.4 L12.6 -12.4 Z ' +
        'M27.2 -17.6 L33.4 -17.6 L38.2 -12.4 L27.2 -12.4 Z',
      trim:
        'M43.6 -6.2 L49 -6.2 L49 -5 Q49 -3.8 47.8 -3.8 L43.3 -3.8 Z M0.4 -6 L4.9 -6 L4.7 -3.8 L1.6 -3.8 Q0.4 -3.8 0.4 -5 Z ' +
        'M13.6 -5.4 L34.4 -5.4 L34.5 -4.4 L13.5 -4.4 Z M35.6 -15.2 L37.4 -15.6 L37.6 -13.6 L35.8 -13.4 Z ' +
        'M23.2 -11.2 h1.6 v0.6 h-1.6 Z M28 -11.2 h1.6 v0.6 h-1.6 Z',
      seam: 'M12 -18.6 L12 -4.6 M26 -18.6 L26 -4.6 M34.6 -11.5 L35.2 -5',
      head: 'M46.4 -10.2 L48.6 -9.6 Q48.9 -8.9 48.6 -8.6 L46.4 -8.8 Z',
      tail: 'M0.25 -15 L1.3 -15 L1.3 -10 L0.3 -10 Z',
    },
    rear: {
      body: 'M-9.4 -4 L-9.5 -12.4 Q-9.4 -14 -8.7 -18.2 Q-8.3 -19.4 -7 -19.4 L7 -19.4 Q8.3 -19.4 8.7 -18.2 Q9.4 -14 9.5 -12.4 L9.4 -4 Z',
      accent: 'M-7 -19.4 L7 -19.4 Q7.4 -20.3 6.6 -20.3 L-6.6 -20.3 Q-7.4 -20.3 -7 -19.4 Z',
      glass: 'M-7.4 -18.2 L7.4 -18.2 L8.2 -12.8 L-8.2 -12.8 Z',
      trim:
        'M-9.7 -6.4 L9.7 -6.4 L9.6 -3.8 L-9.6 -3.8 Z M-9.2 -3.8 h2.4 v3.8 h-2.4 Z M6.8 -3.8 h2.4 v3.8 h-2.4 Z ' +
        'M-10.8 -15 L-9.4 -15.2 L-9.4 -13.6 L-10.8 -13.4 Z M10.8 -15 L9.4 -15.2 L9.4 -13.6 L10.8 -13.4 Z',
      tail: 'M-9.4 -12.4 L-8.2 -12.4 L-8.4 -7.6 L-9.4 -7.6 Z M8.2 -12.4 L9.4 -12.4 L9.4 -7.6 L8.4 -7.6 Z',
      plate: 'M-2.6 -9.4 h5.2 v1.8 h-5.2 Z',
      seam: 'M-8.6 -11.4 L8.6 -11.4',
    },
  },
  panel: {
    length: 63.6, height: 26.9, width: 20.5, axles: [14, 54.3], wheelRadius: 3.4, archY: -4, archRadius: 4.4,
    rearPivot: 8.8, windscreen: 6.6, defaults: { wheelbaseMm: 4035, frontTrackMm: 1810, rearTrackMm: 1790 },
    side: {
      body:
        'M0.3 -4.4 L0.3 -24.6 Q0.3 -26 1.8 -26 L48.2 -26 Q50 -26 50.8 -24.6 L57.2 -14.4 Q57.9 -13.4 59.2 -13.2 ' +
        'L62.2 -12.4 Q63.6 -12 63.6 -10.2 L63.6 -5.2 Q63.6 -4 62.4 -4 L58.7 -4 A4.4 4.4 0 0 0 49.9 -4 L18.4 -4 ' +
        'A4.4 4.4 0 0 0 9.6 -4 L1.5 -4 Q0.3 -4 0.3 -5.2 Z',
      accent: 'M22 -26 L22.6 -26.9 L28.4 -26.9 L29 -26 Z',
      glass: 'M45.8 -22.4 L50.9 -22.4 L55.6 -14.8 L45.8 -14.8 Z M30 -21.6 h9.4 v6.2 h-9.4 Z M4.6 -21.6 h10.6 v6.2 h-10.6 Z',
      trim:
        'M58.9 -6.8 L63.6 -6.8 L63.6 -5.2 Q63.6 -4 62.4 -4 L58.7 -4 Z M0.3 -6.6 L9.9 -6.6 L9.7 -4 L1.5 -4 Q0.3 -4 0.3 -5.2 Z ' +
        'M18.8 -6.4 L49.5 -6.4 L49.6 -5.4 L18.7 -5.4 Z M50.2 -18.4 L52.4 -18.9 L52.6 -16.4 L50.4 -16.2 Z ' +
        'M38 -13.2 h1.8 v0.6 h-1.8 Z M43 -13.4 h1.6 v0.6 h-1.6 Z',
      seam: 'M44.6 -25 L44.6 -4.8 M28.6 -24 L28.6 -4.8 M42.8 -24 L42.8 -4.8 M53.4 -12.6 L53.6 -9',
      head: 'M59.6 -13 L62.8 -12.2 Q63.3 -11.4 62.9 -10.6 L60 -11.2 Z',
      tail: 'M0.3 -17 L1.4 -17 L1.4 -9 L0.3 -9 Z',
    },
    rear: {
      body: 'M-10.25 -4 L-10.25 -24.6 Q-10.25 -26 -8.85 -26 L8.85 -26 Q10.25 -26 10.25 -24.6 L10.25 -4 Z',
      accent: 'M-3 -26 L-2.6 -26.9 L2.6 -26.9 L3 -26 Z',
      glass: 'M-8.6 -23.6 L-1.2 -23.6 L-1.2 -17.4 L-8.6 -17.4 Z M1.2 -23.6 L8.6 -23.6 L8.6 -17.4 L1.2 -17.4 Z',
      trim:
        'M-10.6 -6.6 L10.6 -6.6 L10.5 -4 L-10.5 -4 Z M-10 -4 h2.4 v4 h-2.4 Z M7.6 -4 h2.4 v4 h-2.4 Z ' +
        'M-11.8 -17.6 L-10.25 -17.8 L-10.25 -15.6 L-11.8 -15.4 Z M11.8 -17.6 L10.25 -17.8 L10.25 -15.6 L11.8 -15.4 Z',
      tail: 'M-10.25 -16 L-9.1 -16 L-9.1 -7.6 L-10.25 -7.6 Z M9.1 -16 L10.25 -16 L10.25 -7.6 L9.1 -7.6 Z',
      plate: 'M-2.6 -9.6 h5.2 v1.8 h-5.2 Z',
      seam: 'M0 -25.2 L0 -6.8 M-1.6 -14 L-0.6 -14 M0.6 -14 L1.6 -14',
    },
  },
  alcove: {
    length: 70, height: 32, width: 23, axles: [21, 61.4], wheelRadius: 3.5, archY: -4.2, archRadius: 4.4,
    rearPivot: 9.9, windscreen: 7.2, defaults: motorhomeDefaults,
    side: {
      body:
        'M0.2 -5 L0.2 -30.6 Q0.2 -32 1.6 -32 L58 -32 Q63.2 -32 64.4 -28.4 Q64.9 -25.6 62.6 -25 L58.4 -23.6 ' +
        'Q57.6 -23.3 57.6 -22.4 L63.6 -14.4 Q64.3 -13.5 65.6 -13.3 L68.6 -12.6 Q70 -12.2 70 -10.4 L70 -5.4 ' +
        'Q70 -4.2 68.8 -4.2 L65.8 -4.2 A4.4 4.4 0 0 0 57 -4.2 L25.4 -4.2 A4.4 4.4 0 0 0 16.6 -4.2 L1.4 -4.2 ' +
        'Q0.2 -4.2 0.2 -5.4 Z',
      accent: 'M0.2 -9.6 L52 -9.6 L52 -8.6 L0.2 -8.6 Z',
      glass:
        'M52.6 -20.2 L57.6 -20.2 L61.8 -14.8 L52.6 -14.8 Z M53.8 -30.4 L59.6 -30.4 L59.6 -26.6 L53.8 -26.6 Z ' +
        'M6 -23.4 h10 v6.4 h-10 Z M30 -23.4 h9 v6.4 h-9 Z M43.2 -24.2 h3.6 v5 h-3.6 Z',
      trim:
        'M66 -7 L70 -7 L70 -5.4 Q70 -4.2 68.8 -4.2 L65.8 -4.2 Z M0.2 -7.2 L16.9 -7.2 L16.6 -4.2 L1.4 -4.2 Q0.2 -4.2 0.2 -5.4 Z ' +
        'M25.8 -6 L56.6 -6 L56.8 -4.2 L25.4 -4.2 Z M57 -18.2 L59.2 -18.6 L59.4 -16.2 L57.2 -16 Z M46 -15 h1 v0.6 h-1 Z',
      seam: 'M42 -26 L48 -26 L48 -6.2 L42 -6.2 Z M51.8 -21.6 L51.8 -6.2 M50.2 -31.6 L50.2 -22 M2 -16 L12 -16 L12 -10.2 L2 -10.2 Z',
      head: 'M65.8 -13.2 L69 -12.4 Q69.6 -11.6 69.2 -10.8 L66.2 -11.4 Z',
      tail: 'M0.2 -12.8 L1.3 -12.8 L1.3 -8 L0.2 -8 Z',
    },
    rear: {
      body: 'M-11.5 -4.4 L-11.5 -30.6 Q-11.5 -32 -10.1 -32 L10.1 -32 Q11.5 -32 11.5 -30.6 L11.5 -4.4 Z',
      accent: 'M-11.5 -9.6 L11.5 -9.6 L11.5 -8.6 L-11.5 -8.6 Z',
      glass: 'M-6 -25 L6 -25 L6 -19.4 L-6 -19.4 Z',
      trim:
        'M-11.7 -7.2 L11.7 -7.2 L11.6 -4.4 L-11.6 -4.4 Z M-11.2 -4.4 h2.6 v4.4 h-2.6 Z M8.6 -4.4 h2.6 v4.4 h-2.6 Z ' +
        'M7.6 -30.6 h0.5 v20.4 h-0.5 Z M9.8 -30.6 h0.5 v20.4 h-0.5 Z M7.6 -28 h2.7 v0.4 h-2.7 Z M7.6 -25 h2.7 v0.4 h-2.7 Z ' +
        'M7.6 -22 h2.7 v0.4 h-2.7 Z M7.6 -19 h2.7 v0.4 h-2.7 Z M7.6 -16 h2.7 v0.4 h-2.7 Z M7.6 -13 h2.7 v0.4 h-2.7 Z',
      tail: 'M-11.5 -12.6 L-8.6 -12.6 L-8.6 -10.2 L-11.5 -10.2 Z M8.6 -12.6 L11.5 -12.6 L11.5 -10.2 L8.6 -10.2 Z',
      plate: 'M-2.6 -10.4 h5.2 v1.8 h-5.2 Z',
      seam: EMPTY,
    },
  },
  semi: {
    length: 70, height: 29.8, width: 23, axles: [21, 61.4], wheelRadius: 3.5, archY: -4.2, archRadius: 4.4,
    rearPivot: 9.9, windscreen: 7.2, defaults: motorhomeDefaults,
    side: {
      body:
        'M0.2 -5 L0.2 -27.6 Q0.2 -29 1.6 -29 L50 -29 Q55.6 -29 57.8 -25.6 L58.4 -22.8 L63.6 -14.4 Q64.3 -13.5 65.6 -13.3 ' +
        'L68.6 -12.6 Q70 -12.2 70 -10.4 L70 -5.4 Q70 -4.2 68.8 -4.2 L65.8 -4.2 A4.4 4.4 0 0 0 57 -4.2 L25.4 -4.2 ' +
        'A4.4 4.4 0 0 0 16.6 -4.2 L1.4 -4.2 Q0.2 -4.2 0.2 -5.4 Z',
      accent: 'M0.2 -9.6 L52 -9.6 L52 -8.6 L0.2 -8.6 Z M24 -29 L24.6 -29.8 L31.4 -29.8 L32 -29 Z',
      glass: 'M52.6 -21 L58.2 -21 L62 -15 L52.6 -15 Z M6 -22.6 h10 v6.4 h-10 Z M30 -22.6 h9 v6.4 h-9 Z M43.2 -23.4 h3.6 v5 h-3.6 Z',
      trim:
        'M66 -7 L70 -7 L70 -5.4 Q70 -4.2 68.8 -4.2 L65.8 -4.2 Z M0.2 -7.2 L16.9 -7.2 L16.6 -4.2 L1.4 -4.2 Q0.2 -4.2 0.2 -5.4 Z ' +
        'M25.8 -6 L56.6 -6 L56.8 -4.2 L25.4 -4.2 Z M57.2 -18.6 L59.4 -19 L59.6 -16.6 L57.4 -16.4 Z M46 -15 h1 v0.6 h-1 Z',
      seam: 'M42 -25.4 L48 -25.4 L48 -6.2 L42 -6.2 Z M51.8 -22.6 L51.8 -6.2 M2 -16 L12 -16 L12 -10.2 L2 -10.2 Z',
      head: 'M65.8 -13.2 L69 -12.4 Q69.6 -11.6 69.2 -10.8 L66.2 -11.4 Z',
      tail: 'M0.2 -12.8 L1.3 -12.8 L1.3 -8 L0.2 -8 Z',
    },
    rear: motorhomeRear,
  },
  integrated: {
    length: 72, height: 29.8, width: 23, axles: [20, 60.4], wheelRadius: 3.5, archY: -4.2, archRadius: 4.4,
    rearPivot: 9.9, windscreen: 1.6, defaults: motorhomeDefaults,
    side: {
      body:
        'M0.2 -5 L0.2 -27.6 Q0.2 -29 1.6 -29 L62.4 -29 Q65.6 -29 66.8 -27 L71 -13.6 Q71.8 -11 71.8 -8.6 L71.8 -5.4 ' +
        'Q71.8 -4.2 70.6 -4.2 L64.8 -4.2 A4.4 4.4 0 0 0 56 -4.2 L24.4 -4.2 A4.4 4.4 0 0 0 15.6 -4.2 L1.4 -4.2 ' +
        'Q0.2 -4.2 0.2 -5.4 Z',
      accent: 'M0.2 -9.6 L60 -9.6 L60 -8.6 L0.2 -8.6 Z M24 -29 L24.6 -29.8 L31.4 -29.8 L32 -29 Z',
      glass:
        'M60 -24.6 L64.8 -24.6 L67.6 -16.6 L60 -16.6 Z M66.2 -26.4 L67.2 -26.8 L70.8 -14.6 L70 -14.4 Z ' +
        'M6 -22.6 h10 v6.4 h-10 Z M28 -22.6 h9 v6.4 h-9 Z M43.2 -23.4 h3.6 v5 h-3.6 Z',
      trim:
        'M65 -7.2 L71.8 -7.2 L71.8 -5.4 Q71.8 -4.2 70.6 -4.2 L64.8 -4.2 Z M0.2 -7.2 L15.9 -7.2 L15.6 -4.2 L1.4 -4.2 Q0.2 -4.2 0.2 -5.4 Z ' +
        'M24.6 -6 L55.8 -6 L55.8 -4.2 L24.4 -4.2 Z M66 -24 L68.8 -25.6 L69.4 -22 L68 -21.4 Z M46 -15 h1 v0.6 h-1 Z',
      seam: 'M42 -25.4 L48 -25.4 L48 -6.2 L42 -6.2 Z M58.6 -26 L58.6 -6.2 M2 -16 L12 -16 L12 -10.2 L2 -10.2 Z',
      head: 'M68.8 -8.4 L71.4 -8.6 L71.6 -7.4 L69 -7.4 Z',
      tail: 'M0.2 -12.8 L1.3 -12.8 L1.3 -8 L0.2 -8 Z',
    },
    rear: motorhomeRear,
  },
};

/** The two wheel-arch shadows behind a side view, as one path. */
export function archShadows(type: CamperType): string {
  const r = type.archRadius;
  const y = type.archY;
  return type.axles
    .map((x) => `M${x - r} ${y} A${r} ${r} 0 0 1 ${x + r} ${y} Z`)
    .join(' ');
}

export const BODY_COLOURS = [
  { key: 'white', hex: '#F4F5F7' },
  { key: 'silver', hex: '#C3C9D1' },
  { key: 'grey', hex: '#7A828E' },
  { key: 'anthracite', hex: '#3A3F47' },
  { key: 'blue', hex: '#2D5C99' },
  { key: 'red', hex: '#A8322D' },
  { key: 'sand', hex: '#D8C6A0' },
  { key: 'green', hex: '#6F8A62' },
] as const;
export type BodyColour = (typeof BODY_COLOURS)[number]['key'];
export const DEFAULT_COLOUR: BodyColour = 'white';

export type Paint = { body: string; outline: string; seam: string; accent: string; roof: string; planEdge: string };

/** Body colour plus outline and detail colours that stay readable on it. */
export function paintFor(colour: BodyColour): Paint {
  const hex = BODY_COLOURS.find((c) => c.key === colour)?.hex ?? BODY_COLOURS[0].hex;
  const n = parseInt(hex.slice(1), 16);
  const luminance = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
  const dark = luminance < 0.45;
  return {
    body: hex,
    outline: dark ? '#0E1116' : '#2A2F36',
    seam: dark ? '#6B737E' : '#8A929C',
    accent: dark ? '#9AA2AC' : '#3A4048',
    roof: dark ? '#4A515B' : '#D4D9DF',
    planEdge: dark ? '#5A626C' : '#9AA2AC',
  };
}
