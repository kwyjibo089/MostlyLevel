/** WT901Client against a fake Bluetooth transport and a controllable clock. */

import { beforeEach, expect, test } from '@jest/globals';
import sensor from '../../shared/fixtures/sensor.json';
import { SENSOR_POWER_READ_COMMAND } from '../src/config';
import { BleTransport, Characteristic, displayState, FoundDevice, normalizeUuid, WT901Client } from '../src/sensor/client';
import { hexToBytes } from '../src/sensor/protocol';

const SENSOR = 'F0:A0:7A:DB:7D:45';
const NOTIFY: Characteristic = { service: 'ffe0', characteristic: 'ffe4' };
const WRITE: Characteristic = { service: '0000ffe5-0000-1000-8000-00805f9a34fb', characteristic: '0000FFE9-0000-1000-8000-00805F9A34FB' };
const PACKET = hexToBytes(sensor.attitude_packets[1].hex);
const POWER = hexToBytes(sensor.power_response.hex);

class FakeTransport implements BleTransport {
  calls: string[] = [];
  writes: number[][] = [];
  permitted = true;
  poweredOn = true;
  chars: Characteristic[] = [NOTIFY, WRITE];
  private discover = new Set<(d: FoundDevice) => void>();
  private stopScanListeners = new Set<() => void>();
  private disconnect_ = new Set<(id: string) => void>();
  private value = new Set<(id: string, c: string, v: number[]) => void>();
  private power = new Set<(on: boolean) => void>();

  async start() { this.calls.push('start'); return this.permitted; }
  async isPoweredOn() { return this.poweredOn; }
  async scan() { this.calls.push('scan'); }
  async stopScan() { this.calls.push('stopScan'); }
  async connect(id: string) { this.calls.push(`connect ${id}`); }
  async disconnect(id: string) { this.calls.push(`disconnect ${id}`); }
  async characteristics() { return this.chars; }
  async startNotification(_id: string, c: Characteristic) { this.calls.push(`notify ${c.characteristic}`); }
  async write(_id: string, _c: Characteristic, data: number[]) { this.writes.push(data); }

  private add<T>(set: Set<T>, listener: T) { set.add(listener); return () => { set.delete(listener); }; }
  onDiscover(l: (d: FoundDevice) => void) { return this.add(this.discover, l); }
  onStopScan(l: () => void) { return this.add(this.stopScanListeners, l); }
  onDisconnect(l: (id: string) => void) { return this.add(this.disconnect_, l); }
  onValue(l: (id: string, c: string, v: number[]) => void) { return this.add(this.value, l); }
  onPowerChange(l: (on: boolean) => void) { return this.add(this.power, l); }

  found(id: string) { this.discover.forEach((l) => l({ id, name: 'WT901BLE67', rssi: -60 })); }
  scanEnded() { this.stopScanListeners.forEach((l) => l()); }
  dropped(id = SENSOR) { this.disconnect_.forEach((l) => l(id)); }
  notify(value: number[], characteristic = '0000ffe4-0000-1000-8000-00805f9a34fb') {
    this.value.forEach((l) => l(SENSOR.toLowerCase(), characteristic, value));
  }
  setPower(on: boolean) { this.power.forEach((l) => l(on)); }
}

let now = 0;
let transport: FakeTransport;
let client: WT901Client;

const flush = async () => { for (let i = 0; i < 10; i += 1) await Promise.resolve(); };
const state = () => client.getSnapshot().state;
const shown = () => displayState(client.getSnapshot(), now);

async function live() {
  await client.start();
  transport.found(SENSOR);
  await flush();
  expect(state()).toBe('LIVE');
}

beforeEach(() => {
  now = 1000;
  transport = new FakeTransport();
  client = new WT901Client(transport, SENSOR, () => now);
});

test('16-bit and 128-bit UUIDs compare equal', () => {
  expect(normalizeUuid('FFE4')).toBe('0000ffe4-0000-1000-8000-00805f9a34fb');
  expect(normalizeUuid('0000FFE4-0000-1000-8000-00805F9A34FB')).toBe(normalizeUuid('ffe4'));
});

test('scans, ignores other devices, connects, and enables notifications', async () => {
  await client.start();
  expect(state()).toBe('SCANNING');
  transport.found('11:22:33:44:55:66');
  await flush();
  expect(state()).toBe('SCANNING');
  transport.found(SENSOR.toLowerCase());
  await flush();
  expect(state()).toBe('LIVE');
  expect(transport.calls).toEqual(['start', 'scan', 'stopScan', `connect ${SENSOR}`, 'notify ffe4']);
  // Connected but no data yet: the ESP32 shows WAIT.
  expect(shown()).toBe('WAIT');
});

test('decodes notifications and marks data stale after 1.5 s', async () => {
  await live();
  transport.notify(PACKET);
  expect(shown()).toBe('LIVE');
  expect(client.getSnapshot().latest!.roll).toBeCloseTo(sensor.attitude_packets[1].decoded!.roll, 5);
  now += 1500;
  expect(shown()).toBe('LIVE');
  now += 1;
  expect(shown()).toBe('NO DATA');
});

test('ignores notifications from other characteristics', async () => {
  await live();
  transport.notify(PACKET, '0000ffe9-0000-1000-8000-00805f9a34fb');
  expect(client.getSnapshot().latest).toBeNull();
});

test('polls the battery every 60 s while live and reads the answer', async () => {
  await live();
  transport.notify(PACKET);
  client.maintain();
  expect(transport.writes).toEqual([SENSOR_POWER_READ_COMMAND]);
  transport.notify(POWER);
  expect(client.getSnapshot().battery).toEqual({ raw: 385, voltage: 3.85, percent: 60 });
  now += 59000;
  transport.notify(PACKET);
  client.maintain();
  expect(transport.writes).toHaveLength(1);
  now += 1000;
  transport.notify(PACKET);
  client.maintain();
  expect(transport.writes).toHaveLength(2);
});

test('two frames in one notification are both used, in either order', async () => {
  await live();
  // Seen on the real sensor: a register response and an attitude packet together.
  transport.notify([...POWER, ...PACKET]);
  expect(client.getSnapshot().battery?.percent).toBe(60);
  expect(client.getSnapshot().latest).not.toBeNull();

  client = new WT901Client(transport, SENSOR, () => now);
  await live();
  transport.notify([...PACKET, ...POWER]);
  expect(client.getSnapshot().battery?.percent).toBe(60);
  expect(client.getSnapshot().latest).not.toBeNull();
});

test('a notification of the wrong size is ignored', async () => {
  await live();
  transport.notify([...PACKET, 0x55]);
  expect(client.getSnapshot().latest).toBeNull();
});

test('a dropped link shows DISCONNECTED and rescans', async () => {
  await live();
  transport.notify(PACKET);
  transport.dropped();
  await flush();
  expect(state()).toBe('SCANNING');
  expect(shown()).toBe('DISCONNECTED');
  transport.found(SENSOR);
  await flush();
  transport.notify(PACKET);
  expect(shown()).toBe('LIVE');
});

test('a timed scan that ends without the sensor starts again', async () => {
  await client.start();
  transport.scanEnded();
  await flush();
  expect(transport.calls.filter((c) => c === 'scan')).toHaveLength(2);
});

test('a silent connected sensor is disconnected after 10 s', async () => {
  await live();
  transport.notify(PACKET);
  now += 9999;
  client.maintain();
  expect(state()).toBe('LIVE');
  now += 1;
  client.maintain();
  await flush();
  expect(state()).toBe('DISCONNECTING');
  expect(transport.calls).toContain(`disconnect ${SENSOR}`);
  transport.dropped();
  await flush();
  expect(state()).toBe('SCANNING');
});

test('a missing notify characteristic is an error, retried after 5 s', async () => {
  transport.chars = [WRITE];
  await client.start();
  transport.found(SENSOR);
  await flush();
  expect(state()).toBe('ERROR');
  now += 4999;
  client.maintain();
  expect(state()).toBe('ERROR');
  now += 1;
  client.maintain();
  await flush();
  expect(state()).toBe('DISCONNECTING');
});

test('restarts Bluetooth after 5 recoveries without data', async () => {
  await client.start();
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    now += 30000;
    client.maintain();
    await flush();
    expect(client.failedRecoveries).toBe(attempt);
  }
  now += 30000;
  client.maintain();
  await flush();
  expect(client.failedRecoveries).toBe(0);
  expect(state()).toBe('SCANNING');
  expect(transport.calls.filter((c) => c === 'start')).toHaveLength(2);
});

test('Bluetooth switched off and on again', async () => {
  await live();
  transport.notify(PACKET);
  transport.setPower(false);
  expect(state()).toBe('BLUETOOTH OFF');
  expect(client.getSnapshot().latest).toBeNull();
  transport.setPower(true);
  await flush();
  expect(state()).toBe('SCANNING');
});

test('refused permissions', async () => {
  transport.permitted = false;
  await client.start();
  expect(state()).toBe('NO PERMISSION');
});

test('stop drops the link; switching sensors reconnects to the new one', async () => {
  await live();
  await client.setSensor('AA:BB:CC:DD:EE:FF');
  expect(transport.calls).toContain(`disconnect ${SENSOR}`);
  expect(state()).toBe('SCANNING');
  transport.found(SENSOR);
  await flush();
  expect(state()).toBe('SCANNING');
});
