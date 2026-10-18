/**
 * Camper body types and colours the user can choose.
 *
 * The drawings and their geometry (cm) are generated into vanArt.ts by
 * scripts/make_van_art.py; this file adds the typical dimensions each type
 * brings for the lift calculation, which the user can adjust in settings.
 * The panel van's are the owner's (esp32/src/config.py).
 */

import { VAN_ART } from './vanArt';
import type { CamperArt } from './vanArtTypes';

export const CAMPER_KEYS = ['compact', 'panel', 'alcove', 'semi', 'integrated'] as const;
export type CamperKey = (typeof CAMPER_KEYS)[number];
export const DEFAULT_CAMPER: CamperKey = 'panel';

export type CamperType = CamperArt & {
  defaults: { wheelbaseMm: number; frontTrackMm: number; rearTrackMm: number };
};

const motorhomeDefaults = { wheelbaseMm: 4035, frontTrackMm: 1810, rearTrackMm: 1980 };

const DEFAULTS: Record<CamperKey, CamperType['defaults']> = {
  compact: { wheelbaseMm: 3000, frontTrackMm: 1628, rearTrackMm: 1628 },
  panel: { wheelbaseMm: 4035, frontTrackMm: 1810, rearTrackMm: 1790 },
  alcove: motorhomeDefaults,
  semi: motorhomeDefaults,
  integrated: motorhomeDefaults,
};

export const CAMPERS = Object.fromEntries(
  CAMPER_KEYS.map((key) => [key, { ...VAN_ART[key], defaults: DEFAULTS[key] }]),
) as Record<CamperKey, CamperType>;

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

export function colourHex(colour: BodyColour): string {
  return BODY_COLOURS.find((c) => c.key === colour)?.hex ?? BODY_COLOURS[0].hex;
}
