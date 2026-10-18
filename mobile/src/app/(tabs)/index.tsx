/** ATTITUDE page: VAN (tilting campers) and HORIZON views, CALIBRATE, language. */

import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { CAMPERS, colourHex } from '../../campers';
import { CalibrateButton } from '../../components/CalibrateButton';
import { Toast } from '../../components/Chrome';
import { HorizonView } from '../../components/HorizonView';
import { Card, GlobeIcon, Segmented } from '../../components/ui';
import { hintFor, VanScene } from '../../components/VanScene';
import { LANGUAGES } from '../../config';
import { useAttitude } from '../../hooks/useAttitude';
import { formatSigned, TextKey } from '../../i18n';
import { useSensor } from '../../sensor/SensorProvider';
import { useSettings } from '../../settings/SettingsProvider';
import { colours, fonts } from '../../theme';

export default function AttitudePage() {
  const { settings, update, t } = useSettings();
  const { raw, source } = useSensor();
  const { shown, attitude, drawn } = useAttitude();
  const [view, setView] = useState<'van' | 'horizon'>('van');
  const [toast, setToast] = useState<{ key: TextKey; ok: boolean } | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(toastTimer.current), []);

  const type = CAMPERS[settings.camper];
  const colour = colourHex(settings.colour);

  const showToast = (key: TextKey, ok: boolean) => {
    clearTimeout(toastTimer.current);
    setToast({ key, ok });
    toastTimer.current = setTimeout(() => setToast(null), ok ? 2200 : 2600);
  };

  const calibrate = () => {
    // Save the live attitude as level, or explain why that is not possible.
    if (shown === 'LIVE' && raw !== null) {
      // Each source keeps its own reference: the phone rests elsewhere than the sensor.
      update(source === 'phone' ? { phoneZero: raw } : { zero: raw });
      showToast('calibrate_saved', true);
    } else {
      showToast('warning_calibrate_needs_sensor', false);
    }
  };

  const nextLanguage = () => {
    const index = LANGUAGES.indexOf(settings.language);
    update({ language: LANGUAGES[(index + 1) % LANGUAGES.length] });
  };

  return (
    <View style={styles.page}>
      <Segmented
        options={[
          { value: 'van', label: t('tab_van') },
          { value: 'horizon', label: t('tab_horizon') },
        ]}
        value={view}
        onChange={setView}
      />
      {view === 'van' ? (
        <>
          <VanScene view="rear" type={type} colour={colour} angle={attitude?.roll ?? null} drawnAngle={drawn.roll} t={t} />
          <VanScene view="side" type={type} colour={colour} angle={attitude?.pitch ?? null} drawnAngle={drawn.pitch} t={t} />
        </>
      ) : (
        <>
          <HorizonView pitch={drawn.pitch} roll={drawn.roll} type={type} colour={colour} />
          <View style={styles.tiles}>
            <ReadoutTile label={t('pitch')} angle={attitude?.pitch ?? null} hint={hintFor('side', attitude?.pitch ?? null, t)} decimal={t('decimal')} format={(v) => formatSigned(v, t)} />
            <ReadoutTile label={t('roll')} angle={attitude?.roll ?? null} hint={hintFor('rear', attitude?.roll ?? null, t)} decimal={t('decimal')} format={(v) => formatSigned(v, t)} />
          </View>
          <View style={{ flex: 1 }} />
        </>
      )}
      <View style={styles.actions}>
        <Pressable onPress={nextLanguage} style={styles.language} accessibilityRole="button" accessibilityLabel={t('language')}>
          <GlobeIcon />
          <Text style={styles.languageText}>{settings.language.toUpperCase()}</Text>
        </Pressable>
        <CalibrateButton label={t('calibrate')} hint={t('calibrate_hold')} onCalibrate={calibrate} />
      </View>
      {toast && <Toast text={t(toast.key)} ok={toast.ok} />}
    </View>
  );
}

type TileProps = {
  label: string;
  angle: number | null;
  hint: { text: string; level: boolean };
  decimal: string;
  format: (value: number) => string;
};

function ReadoutTile({ label, angle, hint, decimal, format }: TileProps) {
  return (
    <Card style={styles.tile}>
      <Text style={styles.tileLabel}>{label}</Text>
      <Text style={styles.tileValue}>{angle === null ? `--${decimal}-°` : `${format(angle)}°`}</Text>
      <Text style={[styles.tileHint, hint.level && { color: colours.level }]}>{hint.text}</Text>
    </Card>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, paddingHorizontal: 16, paddingTop: 4, gap: 12 },
  tiles: { flexDirection: 'row', gap: 12 },
  tile: { flex: 1, paddingVertical: 14, paddingHorizontal: 16 },
  tileLabel: { fontFamily: fonts.regular, fontSize: 14, color: colours.muted },
  tileValue: { fontFamily: fonts.number, fontSize: 34, lineHeight: 40, color: colours.text },
  tileHint: { fontFamily: fonts.regular, fontSize: 13, color: colours.muted },
  actions: { flexDirection: 'row', gap: 12, paddingBottom: 12 },
  language: {
    width: 64,
    height: 56,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colours.borderStrong,
    backgroundColor: colours.surface,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
  },
  languageText: { fontFamily: fonts.bold, fontSize: 14, color: colours.accent },
});
