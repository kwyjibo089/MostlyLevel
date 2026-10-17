/** The two pages, ATTITUDE and LEVELLING, under one header and the level/warning overlays. */

import { router, Tabs } from 'expo-router';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomNav, Header, SensorWarning, StatusFrame, warningText } from '../../components/Chrome';
import { useAttitude } from '../../hooks/useAttitude';
import { useSettings } from '../../settings/SettingsProvider';
import { colours } from '../../theme';

export default function PagesLayout() {
  const { t } = useSettings();
  const { shown, levelFrame, batteryPercent } = useAttitude();
  const insets = useSafeAreaInsets();
  const live = shown === 'LIVE';

  return (
    <View style={{ flex: 1, backgroundColor: colours.background, paddingTop: insets.top }}>
      <Header state={shown} batteryPercent={batteryPercent} onSettings={() => router.push('/settings')} t={t} />
      <Tabs
        screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: colours.background } }}
        tabBar={({ state, navigateToTab }) => (
          <BottomNav
            page={state.routes[state.index].name === 'levelling' ? 'levelling' : 'attitude'}
            onPage={(page) => {
              const route = state.routes.find((r) => r.name === (page === 'levelling' ? 'levelling' : 'index'));
              if (route) navigateToTab(route.key);
            }}
            t={t}
            bottomInset={insets.bottom}
          />
        )}
      >
        <Tabs.Screen name="index" />
        <Tabs.Screen name="levelling" />
      </Tabs>
      {!live && <SensorWarning text={warningText(shown, t)} />}
      <StatusFrame level={live && levelFrame} warn={!live} />
    </View>
  );
}
