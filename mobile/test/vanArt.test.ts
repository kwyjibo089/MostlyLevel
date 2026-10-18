/// <reference types="node" />
/** The generated camper drawings: up to date, complete, and with a body colour to fill. */

import { execFileSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@jest/globals';

import { CAMPER_KEYS, CAMPERS } from '../src/campers';

test('src/vanArt.ts matches scripts/van_drawings.py', () => {
  // Throws (failing the test) if the generator reports a stale file.
  execFileSync('python3', [path.join(__dirname, '..', 'scripts', 'make_van_art.py'), '--check']);
});

test.each(CAMPER_KEYS)('%s has every view, a body colour, and sensible geometry', (key) => {
  const art = CAMPERS[key];
  for (const view of [art.side, art.rear, art.top]) {
    expect(view.length).toBeGreaterThan(5);
    expect(view.some((s) => s.body)).toBe(true);
  }
  expect(art.sideShadow).not.toBeNull();
  const { length, axles, wheel, track, width } = art.meta;
  expect(axles[0]).toBeGreaterThan(wheel);
  expect(axles[1]).toBeLessThan(length - wheel);
  expect(track).toBeLessThan(width);
});
