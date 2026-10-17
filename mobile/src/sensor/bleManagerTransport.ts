/** BleTransport on top of react-native-ble-manager (Android). */

import { PermissionsAndroid, Platform } from 'react-native';
import BleManager, { BleScanMode, BleState } from 'react-native-ble-manager';

import type { BleTransport, Characteristic } from './client';

async function requestPermissions(): Promise<boolean> {
  if (Platform.OS !== 'android') return true;
  if (Platform.Version >= 31) {
    const result = await PermissionsAndroid.requestMultiple([
      PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN,
      PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
    ]);
    return Object.values(result).every((value) => value === PermissionsAndroid.RESULTS.GRANTED);
  }
  // Android 11 and older need location access to scan.
  const result = await PermissionsAndroid.request(
    PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
  );
  return result === PermissionsAndroid.RESULTS.GRANTED;
}

let started = false;

export const bleManagerTransport: BleTransport = {
  async start() {
    if (!(await requestPermissions())) return false;
    if (!started) {
      await BleManager.start({ showAlert: false });
      started = true;
    }
    return true;
  },

  async isPoweredOn() {
    return (await BleManager.checkState()) === BleState.On;
  },

  scan(seconds) {
    return BleManager.scan({ serviceUUIDs: [], seconds, scanMode: BleScanMode.LowLatency });
  },

  stopScan() {
    return BleManager.stopScan();
  },

  connect(id) {
    return BleManager.connect(id);
  },

  disconnect(id) {
    return BleManager.disconnect(id);
  },

  async characteristics(id) {
    const info = await BleManager.retrieveServices(id);
    return (info.characteristics ?? []).map(
      (c): Characteristic => ({ service: c.service, characteristic: c.characteristic }),
    );
  },

  startNotification(id, target) {
    return BleManager.startNotification(id, target.service, target.characteristic);
  },

  write(id, target, data) {
    return BleManager.write(id, target.service, target.characteristic, data);
  },

  onDiscover(listener) {
    const subscription = BleManager.onDiscoverPeripheral((peripheral) =>
      listener({ id: peripheral.id, name: peripheral.name ?? peripheral.advertising?.localName ?? null, rssi: peripheral.rssi }),
    );
    return () => subscription.remove();
  },

  onStopScan(listener) {
    const subscription = BleManager.onStopScan(() => listener());
    return () => subscription.remove();
  },

  onDisconnect(listener) {
    const subscription = BleManager.onDisconnectPeripheral((event) => listener(event.peripheral));
    return () => subscription.remove();
  },

  onValue(listener) {
    const subscription = BleManager.onDidUpdateValueForCharacteristic((event) =>
      listener(event.peripheral, event.characteristic, event.value),
    );
    return () => subscription.remove();
  },

  onPowerChange(listener) {
    const subscription = BleManager.onDidUpdateState((event) => {
      if (event.state === BleState.On) listener(true);
      else if (event.state === BleState.Off) listener(false);
    });
    return () => subscription.remove();
  },
};
