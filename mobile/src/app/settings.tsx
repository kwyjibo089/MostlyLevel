/** Settings: language, sensor scan and selection, camper type and colour, dimensions. */

import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg from 'react-native-svg';

import { BODY_COLOURS, CAMPERS, CamperKey, CAMPER_KEYS, colourHex } from '../campers';
import { Art, ArtDefs } from '../components/VanArt';
import { LANGUAGES, SENSOR_NAME_PREFIX } from '../config';
import { translator, TextKey } from '../i18n';
import type { Dimensions } from '../levelling';
import type { FoundDevice } from '../sensor/client';
import { useSensorClient } from '../sensor/SensorProvider';
import { SENSOR_SOURCES, useSettings } from '../settings/SettingsProvider';
import { colours, fonts } from '../theme';

const SCAN_SECONDS = 10;

export default function SettingsScreen() {
  const { settings, update, t } = useSettings();
  const insets = useSafeAreaInsets();
  const colour = colourHex(settings.colour);

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      <View style={styles.titleRow}>
        <Text style={styles.title}>{t('settings')}</Text>
        <Pressable onPress={() => router.back()} style={styles.done} accessibilityRole="button">
          <Text style={styles.doneText}>{t('done')}</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 24 }]}>
        <Section title={t('language')}>
          <View style={styles.wrap}>
            {LANGUAGES.map((language) => (
              <Chip
                key={language}
                label={translator(language)('language_name')}
                selected={settings.language === language}
                onPress={() => update({ language })}
              />
            ))}
          </View>
        </Section>

        <Section title={t('source')}>
          <View style={styles.grid}>
            {SENSOR_SOURCES.map((source) => {
              const selected = settings.source === source;
              return (
                <Pressable
                  key={source}
                  onPress={() => update({ source })}
                  style={[styles.camperCard, selected && styles.selectedCard]}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                >
                  <Text style={styles.cardTitle}>{t(source === 'phone' ? 'source_phone' : 'source_wt901')}</Text>
                  <Text style={styles.cardHint}>{t(source === 'phone' ? 'source_phone_hint' : 'source_wt901_hint')}</Text>
                </Pressable>
              );
            })}
          </View>
          {settings.source === 'phone' && <Text style={styles.cardHint}>{t('source_phone_placement')}</Text>}
        </Section>

        {settings.source === 'wt901' && <SensorSection />}

        <Section title={t('camper')}>
          <View style={styles.grid}>
            {CAMPER_KEYS.map((key) => {
              const type = CAMPERS[key];
              const selected = settings.camper === key;
              return (
                <Pressable
                  key={key}
                  onPress={() => selectCamper(key, settings.camper, settings.dimensions, update)}
                  style={[styles.camperCard, selected && styles.selectedCard]}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                >
                  <Svg width="100%" height={58} viewBox={`-12 ${-(type.meta.height + 8)} ${type.meta.length + 24} ${type.meta.height + 18}`}>
                    <ArtDefs />
                    <Art shapes={type.side} colour={colour} />
                  </Svg>
                  <Text style={styles.cardTitle}>{t(`camper_${key}` as TextKey)}</Text>
                  <Text style={styles.cardHint}>{t(`camper_${key}_hint` as TextKey)}</Text>
                </Pressable>
              );
            })}
          </View>
          <Text style={styles.subheading}>{t('camper_colour')}</Text>
          <View style={styles.wrap}>
            {BODY_COLOURS.map((colour) => {
              const selected = settings.colour === colour.key;
              return (
                <Pressable
                  key={colour.key}
                  onPress={() => update({ colour: colour.key })}
                  style={[styles.swatch, { backgroundColor: colour.hex }, selected && styles.swatchSelected]}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                  accessibilityLabel={t(`colour_${colour.key}` as TextKey)}
                />
              );
            })}
          </View>
        </Section>

        <DimensionsSection />
      </ScrollView>
    </View>
  );
}

/** Switching camper type also switches to its typical dimensions, unless the user entered their own. */
function selectCamper(
  key: CamperKey,
  current: CamperKey,
  dimensions: Dimensions,
  update: (patch: { camper: CamperKey; dimensions?: Dimensions }) => void,
) {
  const old = CAMPERS[current].defaults;
  const untouched =
    dimensions.wheelbaseMm === old.wheelbaseMm &&
    dimensions.frontTrackMm === old.frontTrackMm &&
    dimensions.rearTrackMm === old.rearTrackMm;
  update(untouched ? { camper: key, dimensions: { ...CAMPERS[key].defaults } } : { camper: key });
}

function SensorSection() {
  const { settings, update, t } = useSettings();
  const client = useSensorClient();
  const [scanning, setScanning] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [found, setFound] = useState<FoundDevice[]>([]);
  const stopScan = useRef<(() => Promise<void>) | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const finish = async () => {
    clearTimeout(timer.current);
    const stop = stopScan.current;
    stopScan.current = null;
    setScanning(false);
    if (stop) {
      await stop();
      await client.start();
    }
  };

  // Leaving the screen ends a scan and reconnects to the chosen sensor.
  useEffect(() => () => void finish(), []); // eslint-disable-line react-hooks/exhaustive-deps

  const scan = async () => {
    setFound([]);
    setScanning(true);
    stopScan.current = await client.discover((device) => {
      setFound((list) => {
        const rest = list.filter((d) => d.id !== device.id);
        return [...rest, device].sort((a, b) => b.rssi - a.rssi);
      });
    }, SCAN_SECONDS);
    timer.current = setTimeout(() => void finish(), SCAN_SECONDS * 1000);
  };

  const choose = async (device: FoundDevice) => {
    await finish();
    update({ sensorId: device.id });
  };

  const visible = found.filter(
    (device) => showAll || (device.name ?? '').toUpperCase().startsWith(SENSOR_NAME_PREFIX),
  );

  return (
    <Section title={t('sensor')}>
      <View style={styles.sensorRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardHint}>{t('sensor_current')}</Text>
          <Text style={styles.mono}>{settings.sensorId}</Text>
        </View>
        <Pressable
          onPress={scanning ? () => void finish() : () => void scan()}
          style={[styles.button, scanning && styles.buttonActive]}
          accessibilityRole="button"
        >
          <Text style={styles.buttonText}>{scanning ? t('sensor_scanning') : t('sensor_scan')}</Text>
        </Pressable>
      </View>
      {(scanning || found.length > 0) && (
        <View style={styles.list}>
          {visible.length === 0 && <Text style={styles.cardHint}>{t('sensor_none_found')}</Text>}
          {visible.map((device) => {
            const inUse = device.id.toUpperCase() === settings.sensorId.toUpperCase();
            return (
              <View key={device.id} style={styles.deviceRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>{device.name ?? t('sensor_unnamed')}</Text>
                  <Text style={styles.cardHint}>{`${device.id} · ${device.rssi} dBm`}</Text>
                </View>
                <Pressable
                  onPress={() => void choose(device)}
                  disabled={inUse}
                  style={[styles.button, inUse && styles.buttonActive]}
                  accessibilityRole="button"
                >
                  <Text style={styles.buttonText}>{inUse ? t('sensor_in_use') : t('sensor_use')}</Text>
                </Pressable>
              </View>
            );
          })}
          <View style={styles.switchRow}>
            <Text style={styles.cardHint}>{t('sensor_show_all')}</Text>
            <Switch value={showAll} onValueChange={setShowAll} trackColor={{ true: colours.accent }} />
          </View>
        </View>
      )}
    </Section>
  );
}

function DimensionsSection() {
  const { settings, update, t } = useSettings();
  const fields: Array<[keyof Dimensions, TextKey]> = [
    ['wheelbaseMm', 'wheelbase'],
    ['frontTrackMm', 'front_track'],
    ['rearTrackMm', 'rear_track'],
  ];
  return (
    <Section title={t('dimensions')}>
      <Text style={styles.cardHint}>{t('dimensions_hint')}</Text>
      {fields.map(([key, label]) => (
        <NumberField
          key={`${key}-${settings.dimensions[key]}`}
          label={t(label)}
          value={settings.dimensions[key]}
          onChange={(value) => update({ dimensions: { ...settings.dimensions, [key]: value } })}
        />
      ))}
      <Pressable
        onPress={() => update({ dimensions: { ...CAMPERS[settings.camper].defaults } })}
        style={styles.linkButton}
        accessibilityRole="button"
      >
        <Text style={styles.link}>{t('dimensions_reset')}</Text>
      </Pressable>
    </Section>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  const [text, setText] = useState(String(Math.round(value)));
  const commit = () => {
    const parsed = Number(text.replace(/[^0-9]/g, ''));
    if (Number.isFinite(parsed) && parsed >= 500 && parsed <= 10000) onChange(parsed);
    else setText(String(Math.round(value)));
  };
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.inputBox}>
        <TextInput
          value={text}
          onChangeText={setText}
          onEndEditing={commit}
          onSubmitEditing={commit}
          keyboardType="number-pad"
          inputMode="numeric"
          style={styles.input}
          accessibilityLabel={label}
          selectTextOnFocus
        />
        <Text style={styles.unit}>mm</Text>
      </View>
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionBody}>{children}</View>
    </View>
  );
}

function Chip({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, selected && styles.selectedCard]}
      accessibilityRole="radio"
      accessibilityState={{ selected }}
    >
      <Text style={[styles.chipText, selected && { color: '#FFFFFF' }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colours.background },
  titleRow: {
    height: 64,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: { fontFamily: fonts.bold, fontSize: 24, color: colours.text },
  done: { height: 40, paddingHorizontal: 18, borderRadius: 20, backgroundColor: colours.accent, justifyContent: 'center' },
  doneText: { fontFamily: fonts.bold, fontSize: 15, color: '#04212A' },
  content: { paddingHorizontal: 16, gap: 20 },
  section: { gap: 10 },
  sectionTitle: { fontFamily: fonts.semibold, fontSize: 14, color: colours.muted, textTransform: 'uppercase', letterSpacing: 0.6 },
  sectionBody: {
    backgroundColor: colours.surface,
    borderColor: colours.border,
    borderWidth: 1,
    borderRadius: 20,
    padding: 14,
    gap: 12,
  },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  camperCard: {
    width: '48%',
    flexGrow: 1,
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2A313D',
    backgroundColor: colours.surfaceRaised,
    gap: 2,
  },
  selectedCard: { borderColor: colours.accent, backgroundColor: '#1E3243' },
  cardTitle: { fontFamily: fonts.semibold, fontSize: 15, color: colours.text },
  cardHint: { fontFamily: fonts.regular, fontSize: 13, color: colours.muted },
  subheading: { fontFamily: fonts.medium, fontSize: 14, color: colours.muted, marginTop: 4 },
  swatch: { width: 40, height: 40, borderRadius: 20, borderWidth: 2, borderColor: '#2A313D' },
  swatchSelected: { borderColor: colours.accent, borderWidth: 3 },
  chip: {
    height: 44,
    paddingHorizontal: 16,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colours.borderStrong,
    backgroundColor: colours.surfaceRaised,
    justifyContent: 'center',
  },
  chipText: { fontFamily: fonts.semibold, fontSize: 15, color: colours.textSoft },
  sensorRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  mono: { fontFamily: fonts.number, fontSize: 18, color: colours.text, letterSpacing: 0.5 },
  button: {
    minHeight: 44,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colours.borderStrong,
    backgroundColor: colours.surfaceRaised,
    justifyContent: 'center',
  },
  buttonActive: { borderColor: colours.accent, backgroundColor: colours.selected },
  buttonText: { fontFamily: fonts.semibold, fontSize: 14, color: colours.textSoft },
  list: { gap: 10, borderTopWidth: 1, borderTopColor: colours.border, paddingTop: 12 },
  deviceRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  switchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  field: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  fieldLabel: { fontFamily: fonts.medium, fontSize: 16, color: colours.text },
  inputBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderColor: colours.borderStrong,
    borderRadius: 12,
    backgroundColor: colours.surfaceRaised,
    paddingHorizontal: 12,
    minHeight: 44,
  },
  input: { fontFamily: fonts.number, fontSize: 20, color: colours.text, minWidth: 64, textAlign: 'right', paddingVertical: 6 },
  unit: { fontFamily: fonts.regular, fontSize: 14, color: colours.muted },
  linkButton: { minHeight: 44, justifyContent: 'center' },
  link: { fontFamily: fonts.semibold, fontSize: 15, color: colours.accent },
});
