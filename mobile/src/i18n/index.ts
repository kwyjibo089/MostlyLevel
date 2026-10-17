/** Screen texts per language. Missing keys fall back to English, then the key. */

import type { Language } from '../config';
import de from './de.json';
import en from './en.json';
import es from './es.json';
import fr from './fr.json';

export type TextKey = keyof typeof en;

const TEXTS: Record<Language, Partial<Record<TextKey, string>>> = { en, de, fr, es };

export type Translate = (key: TextKey) => string;

export function translator(language: Language): Translate {
  const texts = TEXTS[language];
  return (key) => texts[key] ?? en[key] ?? key;
}

/** Format with the language's decimal separator, e.g. "+1.2" or "−0,4". */
export function formatSigned(value: number, t: Translate): string {
  const rounded = Math.round(value * 10) / 10;
  const sign = rounded < 0 ? '−' : '+';
  return sign + Math.abs(rounded).toFixed(1).replace('.', t('decimal'));
}

export function formatCm(value: number | null, t: Translate): string {
  const text = value === null ? '--.-' : value.toFixed(1);
  return `${text.replace('.', t('decimal'))} cm`;
}

export function formatMm(value: number): string {
  return `${Math.round(value)} mm`;
}
