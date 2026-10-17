import { Barlow_400Regular, Barlow_500Medium, Barlow_600SemiBold, Barlow_700Bold } from '@expo-google-fonts/barlow';
import { BarlowCondensed_600SemiBold } from '@expo-google-fonts/barlow-condensed';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { SensorProvider } from '../sensor/SensorProvider';
import { SettingsProvider } from '../settings/SettingsProvider';
import { colours } from '../theme';

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    Barlow_400Regular,
    Barlow_500Medium,
    Barlow_600SemiBold,
    Barlow_700Bold,
    BarlowCondensed_600SemiBold,
  });
  if (!fontsLoaded) return <View style={{ flex: 1, backgroundColor: colours.background }} />;

  return (
    <SafeAreaProvider>
      <SettingsProvider>
        <SensorProvider>
          <StatusBar style="light" />
          <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colours.background } }}>
            <Stack.Screen name="(tabs)" />
            <Stack.Screen name="settings" options={{ presentation: 'modal', animation: 'slide_from_bottom' }} />
          </Stack>
        </SensorProvider>
      </SettingsProvider>
    </SafeAreaProvider>
  );
}
