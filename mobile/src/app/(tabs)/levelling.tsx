/** LEVELLING page: 2 WEDGES (the two corners to lift) and 4 CORNERS. */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { CAMPERS, paintFor } from '../../campers';
import { PlanView } from '../../components/PlanView';
import { Card, CheckIcon, Segmented } from '../../components/ui';
import { useAttitude } from '../../hooks/useAttitude';
import { formatCm } from '../../i18n';
import { cornerLifts, wedgeAdvice } from '../../levelling';
import { useSettings } from '../../settings/SettingsProvider';
import { colours, fonts } from '../../theme';

export default function LevellingPage() {
  const { settings, t } = useSettings();
  const { attitude } = useAttitude();
  const [mode, setMode] = useState<'wedges' | 'corners'>('wedges');
  const type = CAMPERS[settings.camper];
  const lifts = attitude ? cornerLifts(attitude, settings.dimensions) : null;
  const advice = lifts ? wedgeAdvice(lifts) : null;

  return (
    <View style={styles.page}>
      <Segmented
        options={[
          { value: 'wedges', label: t('tab_wedges') },
          { value: 'corners', label: t('tab_corners') },
        ]}
        value={mode}
        onChange={setMode}
      />
      <Card style={styles.plan}>
        <PlanView type={type} paint={paintFor(settings.colour)} lifts={lifts} mode={mode} advice={advice} t={t} />
      </Card>
      {mode === 'wedges' && advice === 'level' && (
        <Card style={styles.levelCard}>
          <CheckIcon />
          <Text style={styles.levelTitle}>{t('no_wedges_needed')}</Text>
          <Text style={styles.levelText}>{t('van_is_level')}</Text>
        </Card>
      )}
      {mode === 'wedges' && advice !== 'level' &&
        [0, 1].map((index) => {
          const corner = advice ? advice[index] : null;
          return (
            <Card key={index} style={styles.row}>
              <View style={[styles.badge, { backgroundColor: corner ? colours.lift : '#3A4350' }]}>
                <Text style={styles.badgeText}>{index + 1}</Text>
              </View>
              <Text style={styles.rowLabel}>{corner ? t(corner) : '--'}</Text>
              <Text style={styles.rowValue}>{formatCm(corner && lifts ? lifts[corner] : null, t)}</Text>
            </Card>
          );
        })}
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, paddingHorizontal: 16, paddingTop: 4, paddingBottom: 12, gap: 12 },
  plan: { flex: 1, minHeight: 280 },
  row: { height: 64, flexDirection: 'row', alignItems: 'center', gap: 14, paddingHorizontal: 18 },
  badge: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  badgeText: { fontFamily: fonts.bold, fontSize: 15, color: '#1A1000' },
  rowLabel: { flex: 1, fontFamily: fonts.semibold, fontSize: 17, color: colours.text },
  rowValue: { fontFamily: fonts.number, fontSize: 28, color: colours.text },
  levelCard: { height: 140, alignItems: 'center', justifyContent: 'center', gap: 6, borderColor: '#2F6B47' },
  levelTitle: { fontFamily: fonts.bold, fontSize: 20, color: colours.level },
  levelText: { fontFamily: fonts.regular, fontSize: 15, color: colours.textSoft },
});
