#!/usr/bin/env node
/**
 * Render the app icon and splash PNGs in assets/ from the SVG layers in
 * assets/icon/ (written by scripts/app_icon.py).
 *
 * Android adaptive icons use the background, foreground, and monochrome
 * layers as they are; launchers show their central 683 of 1024 px. The plain
 * icon and the splash image show that same visible part, so they look like
 * the icon on the home screen.
 *
 * Usage: python3 scripts/app_icon.py && node scripts/make-icons.mjs
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { Resvg } from '@resvg/resvg-js';

const ASSETS = join(dirname(fileURLToPath(import.meta.url)), '..', 'assets');
const layer = (name) => readFileSync(join(ASSETS, 'icon', `${name}.svg`), 'utf8');
const VISIBLE = 683;
const OFFSET = (1024 - VISIBLE) / 2;

/** Background and foreground combined, cropped to the visible part, optionally rounded. */
function visibleIcon(rounded) {
  const defs = (svg) => svg.match(/<defs>([\s\S]*?)<\/defs>/)[1];
  const body = (svg) => svg.replace(/^[\s\S]*?<\/defs>/, '').replace(/<\/svg>\s*$/, '');
  const bg = layer('background');
  const fg = layer('foreground');
  const clip = rounded
    ? '<clipPath id="r"><rect width="1024" height="1024" rx="230"/></clipPath>'
    : '';
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">` +
    `<defs>${defs(bg)}${clip}</defs>` +
    `<g${rounded ? ' clip-path="url(#r)"' : ''}>` +
    `<g transform="scale(${1024 / VISIBLE}) translate(${-OFFSET} ${-OFFSET})">${body(bg)}${body(fg)}</g></g></svg>`
  );
}

function render(name, svg, size) {
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: size } }).render().asPng();
  writeFileSync(join(ASSETS, name), png);
  console.log(`Wrote assets/${name} (${size}×${size})`);
}

render('android-icon-background.png', layer('background'), 1024);
render('android-icon-foreground.png', layer('foreground'), 1024);
render('android-icon-monochrome.png', layer('monochrome'), 1024);
render('icon.png', visibleIcon(false), 1024);
render('splash-icon.png', visibleIcon(true), 1024);
render('favicon.png', visibleIcon(true), 48);
