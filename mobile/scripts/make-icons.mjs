#!/usr/bin/env node
/**
 * Render the app icon PNGs in assets/ from the vector design below.
 *
 * The icon is a spirit-level vial with a green (level) bubble above the
 * panel van from src/campers.ts, standing on a green level line. Android
 * crops adaptive icons to various shapes, so the foreground stays inside
 * the central safe circle (66 of 108 dp).
 *
 * Usage: node scripts/make-icons.mjs
 */

import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { Resvg } from '@resvg/resvg-js';

const ASSETS = join(dirname(fileURLToPath(import.meta.url)), '..', 'assets');

const NAVY_TOP = '#16395A';
const NAVY_BOTTOM = '#0B1B2A';
const LEVEL = '#4ADE80';
const WHITE = '#F4F5F7';

// Panel van side view from src/campers.ts (decimetres, ground at y = 0).
const VAN = {
  length: 63.6,
  axles: [14, 54.3],
  wheelRadius: 3.4,
  arch: { y: -4, r: 4.4 },
  body:
    'M0.3 -4.4 L0.3 -24.6 Q0.3 -26 1.8 -26 L48.2 -26 Q50 -26 50.8 -24.6 L57.2 -14.4 Q57.9 -13.4 59.2 -13.2 ' +
    'L62.2 -12.4 Q63.6 -12 63.6 -10.2 L63.6 -5.2 Q63.6 -4 62.4 -4 L58.7 -4 A4.4 4.4 0 0 0 49.9 -4 L18.4 -4 ' +
    'A4.4 4.4 0 0 0 9.6 -4 L1.5 -4 Q0.3 -4 0.3 -5.2 Z',
  glass: 'M45.8 -22.4 L50.9 -22.4 L55.6 -14.8 L45.8 -14.8 Z M30 -21.6 h9.4 v6.2 h-9.4 Z M4.6 -21.6 h10.6 v6.2 h-10.6 Z',
  trim:
    'M58.9 -6.8 L63.6 -6.8 L63.6 -5.2 Q63.6 -4 62.4 -4 L58.7 -4 Z M0.3 -6.6 L9.9 -6.6 L9.7 -4 L1.5 -4 Q0.3 -4 0.3 -5.2 Z ' +
    'M18.8 -6.4 L49.5 -6.4 L49.6 -5.4 L18.7 -5.4 Z',
  head: 'M59.6 -13 L62.8 -12.2 Q63.3 -11.4 62.9 -10.6 L60 -11.2 Z',
  tail: 'M0.3 -17 L1.4 -17 L1.4 -9 L0.3 -9 Z',
};

const SCALE = 7.4;
const GROUND_Y = 692;
const vanTransform = `translate(${512 - (VAN.length / 2) * SCALE} ${GROUND_Y}) scale(${SCALE})`;

function vial(mono) {
  const stroke = mono ? WHITE : WHITE;
  const inside = mono ? 'none' : '#0E2A3E';
  return `
    <rect x="336" y="322" width="352" height="92" rx="46" fill="${inside}" stroke="${stroke}" stroke-width="18"/>
    <line x1="448" y1="344" x2="448" y2="392" stroke="${stroke}" stroke-width="10" stroke-linecap="round"/>
    <line x1="576" y1="344" x2="576" y2="392" stroke="${stroke}" stroke-width="10" stroke-linecap="round"/>
    <ellipse cx="512" cy="368" rx="48" ry="26" fill="${mono ? WHITE : LEVEL}"/>`;
}

function van(mono) {
  const r = VAN.wheelRadius;
  const arches = VAN.axles
    .map((x) => `M${x - VAN.arch.r} ${VAN.arch.y} A${VAN.arch.r} ${VAN.arch.r} 0 0 1 ${x + VAN.arch.r} ${VAN.arch.y} Z`)
    .join(' ');
  if (mono) {
    // One colour: the silhouette and the wheels, no details.
    return `<g transform="${vanTransform}">
      <path d="${VAN.body}" fill="${WHITE}"/>
      ${VAN.axles.map((x) => `<circle cx="${x}" cy="${-r}" r="${r}" fill="${WHITE}"/>`).join('')}
    </g>`;
  }
  return `<g transform="${vanTransform}">
    <path d="${arches}" fill="#0A1520"/>
    <path d="${VAN.body}" fill="${WHITE}"/>
    <path d="${VAN.glass}" fill="${NAVY_BOTTOM}"/>
    <path d="${VAN.trim}" fill="#2B3036"/>
    <path d="${VAN.head}" fill="#FFE27A"/>
    <path d="${VAN.tail}" fill="#E0453B"/>
    ${VAN.axles
      .map(
        (x) =>
          `<circle cx="${x}" cy="${-r}" r="${r}" fill="#0A1118"/><circle cx="${x}" cy="${-r}" r="${r * 0.55}" fill="#A9B1BA"/>`,
      )
      .join('')}
  </g>`;
}

function ground(mono) {
  return `<rect x="292" y="${GROUND_Y + 2}" width="440" height="16" rx="8" fill="${mono ? WHITE : LEVEL}"/>`;
}

const background = `
  <defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${NAVY_TOP}"/><stop offset="1" stop-color="${NAVY_BOTTOM}"/>
  </linearGradient></defs>
  <rect width="1024" height="1024" fill="url(#bg)"/>`;

const foreground = (mono = false) => `${vial(mono)}${van(mono)}${ground(mono)}`;

const svg = (body) => `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">${body}</svg>`;

function render(name, body, size) {
  const png = new Resvg(svg(body), { fitTo: { mode: 'width', value: size } }).render().asPng();
  writeFileSync(join(ASSETS, name), png);
  console.log(`Wrote assets/${name} (${size}×${size})`);
}

// The plain icon is not cropped by Android, so the motif can be larger.
const large = `<g transform="translate(512 512) scale(1.4) translate(-512 -505)">${foreground()}</g>`;

render('icon.png', background + large, 1024);
render('android-icon-background.png', background, 1024);
render('android-icon-foreground.png', foreground(), 1024);
render('android-icon-monochrome.png', foreground(true), 1024);
render('splash-icon.png', foreground(), 1024);
render('favicon.png', background + large, 48);
