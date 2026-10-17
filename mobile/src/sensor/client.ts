/**
 * WT901 BLE client, ported from WT901BLEClient in esp32/src/ble_read.py.
 *
 * Same states and recovery rules as the ESP32: scan for the configured
 * sensor, connect, find the notify (FFE4) and write (FFE9) characteristics,
 * enable notifications, and keep the latest decoded sample. maintain() runs
 * on a timer and reconnects a link stuck in ERROR, in an unfinished setup or
 * scan, or connected without data. Where the ESP32 hard-resets the board
 * after repeated failed recoveries, the client restarts its Bluetooth stack.
 *
 * The Bluetooth library sits behind BleTransport so tests can drive the
 * client with a fake.
 */

import {
  BATTERY_POLL_INTERVAL_MS,
  SENSOR_ERROR_RETRY_MS,
  SENSOR_NOTIFY_UUID,
  SENSOR_POWER_READ_COMMAND,
  SENSOR_RECOVERY_RESET_COUNT,
  SENSOR_SCAN_TIMEOUT_MS,
  SENSOR_SETUP_TIMEOUT_MS,
  SENSOR_SILENT_RECONNECT_MS,
  SENSOR_STALE_MS,
  SENSOR_WRITE_UUID,
} from '../config';
import {
  decodePacket,
  decodePowerResponse,
  isRegisterPacket,
  PowerReading,
  SensorValues,
  splitFrames,
} from './protocol';

export type ClientState =
  | 'IDLE'
  | 'SCANNING'
  | 'CONNECTING'
  | 'DISCOVERING'
  | 'SETTING UP'
  | 'LIVE'
  | 'DISCONNECTING'
  | 'ERROR'
  | 'BLUETOOTH OFF'
  | 'NO PERMISSION';

/** What the screen shows, derived like the ESP32 main loop does. */
export type DisplayState = ClientState | 'NO DATA' | 'WAIT' | 'DISCONNECTED';

export type Characteristic = { service: string; characteristic: string };
export type FoundDevice = { id: string; name: string | null; rssi: number };

export interface BleTransport {
  /** Initialise the library and ask for permissions; false if refused. */
  start(): Promise<boolean>;
  isPoweredOn(): Promise<boolean>;
  scan(seconds: number): Promise<void>;
  stopScan(): Promise<void>;
  connect(id: string): Promise<void>;
  disconnect(id: string): Promise<void>;
  characteristics(id: string): Promise<Characteristic[]>;
  startNotification(id: string, target: Characteristic): Promise<void>;
  write(id: string, target: Characteristic, data: number[]): Promise<void>;
  onDiscover(listener: (device: FoundDevice) => void): () => void;
  onStopScan(listener: () => void): () => void;
  onDisconnect(listener: (id: string) => void): () => void;
  onValue(listener: (id: string, characteristic: string, value: number[]) => void): () => void;
  onPowerChange(listener: (on: boolean) => void): () => void;
}

export type Snapshot = {
  state: ClientState;
  latest: SensorValues | null;
  lastPacketMs: number;
  linkLost: boolean;
  battery: PowerReading | null;
  sequence: number;
};

const SCAN_SECONDS = 15;

/** Compare UUIDs given as 16-bit ("ffe4") or 128-bit strings, any case. */
export function normalizeUuid(uuid: string): string {
  const value = uuid.trim().toLowerCase();
  if (/^(0x)?[0-9a-f]{4}$/.test(value)) {
    return `0000${value.replace(/^0x/, '')}-0000-1000-8000-00805f9a34fb`;
  }
  return value;
}

function sameId(a: string, b: string): boolean {
  return a.toUpperCase() === b.toUpperCase();
}

/** The state the screen shows: live, stale, waiting, or the link state. */
export function displayState(snapshot: Snapshot, now: number): DisplayState {
  if (snapshot.latest !== null) {
    return now - snapshot.lastPacketMs > SENSOR_STALE_MS ? 'NO DATA' : 'LIVE';
  }
  if (snapshot.state === 'LIVE') return 'WAIT';
  if (snapshot.linkLost && snapshot.state !== 'ERROR') return 'DISCONNECTED';
  return snapshot.state;
}

export class WT901Client {
  private sensorId: string;
  private state: ClientState = 'IDLE';
  private stateSinceMs: number;
  private connected = false;
  private notify: Characteristic | null = null;
  private writeTarget: Characteristic | null = null;
  private latest: SensorValues | null = null;
  private lastPacketMs = 0;
  private linkLost = false;
  private battery: PowerReading | null = null;
  private lastBatteryRequestMs: number | null = null;
  private sequence = 0;
  /** Recoveries since the last attitude packet; see maintain(). */
  failedRecoveries = 0;
  private running = false;
  private unsubscribers: Array<() => void> = [];
  private listeners = new Set<() => void>();
  private snapshot: Snapshot;

  constructor(
    private readonly transport: BleTransport,
    sensorId: string,
    private readonly now: () => number = Date.now,
    private readonly log: (message: string) => void = () => {},
  ) {
    this.sensorId = sensorId;
    this.stateSinceMs = now();
    this.snapshot = this.makeSnapshot();
  }

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getSnapshot = (): Snapshot => this.snapshot;

  private makeSnapshot(): Snapshot {
    return {
      state: this.state,
      latest: this.latest,
      lastPacketMs: this.lastPacketMs,
      linkLost: this.linkLost,
      battery: this.battery,
      sequence: this.sequence,
    };
  }

  private emit(): void {
    this.snapshot = this.makeSnapshot();
    for (const listener of this.listeners) listener();
  }

  /** Still in `state` after an await? (Events may have moved the client on.) */
  private isIn(state: ClientState): boolean {
    return this.state === state;
  }

  private setState(state: ClientState): void {
    this.state = state;
    this.stateSinceMs = this.now();
    this.log(`state ${state}`);
    this.emit();
  }

  async start(): Promise<void> {
    if (this.running) return;
    this.running = true;
    this.subscribeTransport();
    if (!(await this.transport.start())) {
      this.setState('NO PERMISSION');
      return;
    }
    if (!(await this.transport.isPoweredOn())) {
      this.setState('BLUETOOTH OFF');
      return;
    }
    await this.startScan();
  }

  /** Stop scanning and drop the link, e.g. while the app is in the background. */
  async stop(): Promise<void> {
    if (!this.running) return;
    this.running = false;
    for (const unsubscribe of this.unsubscribers) unsubscribe();
    this.unsubscribers = [];
    await this.transport.stopScan().catch(() => {});
    if (this.connected) await this.transport.disconnect(this.sensorId).catch(() => {});
    this.resetLink();
    this.latest = null;
    this.linkLost = false;
    this.sequence += 1;
    this.setState('IDLE');
  }

  /** Use another sensor; reconnects if running. */
  async setSensor(sensorId: string): Promise<void> {
    if (sameId(sensorId, this.sensorId)) return;
    const wasRunning = this.running;
    await this.stop();
    this.sensorId = sensorId;
    this.battery = null;
    if (wasRunning) await this.start();
  }

  private subscribeTransport(): void {
    const t = this.transport;
    this.unsubscribers = [
      t.onDiscover((device) => this.onDiscover(device)),
      t.onStopScan(() => this.onStopScan()),
      t.onDisconnect((id) => this.onDisconnect(id)),
      t.onValue((id, characteristic, value) => this.onValue(id, characteristic, value)),
      t.onPowerChange((on) => this.onPowerChange(on)),
    ];
  }

  private resetLink(): void {
    this.connected = false;
    this.notify = null;
    this.writeTarget = null;
    this.lastBatteryRequestMs = null;
  }

  private async startScan(): Promise<void> {
    this.resetLink();
    this.setState('SCANNING');
    this.log(`scanning for ${this.sensorId}`);
    try {
      await this.transport.scan(SCAN_SECONDS);
    } catch (error) {
      this.log(`scan failed: ${String(error)}`);
      this.setState('ERROR');
    }
  }

  private onPowerChange(on: boolean): void {
    if (!this.running) return;
    if (!on) {
      this.resetLink();
      if (this.latest !== null) this.linkLost = true;
      this.latest = null;
      this.sequence += 1;
      this.setState('BLUETOOTH OFF');
    } else if (this.state === 'BLUETOOTH OFF') {
      void this.startScan();
    }
  }

  private onDiscover(device: FoundDevice): void {
    if (this.state !== 'SCANNING' || this.connected || !sameId(device.id, this.sensorId)) return;
    this.log(`found ${device.id} RSSI ${device.rssi}`);
    this.setState('CONNECTING');
    void this.connect();
  }

  private async connect(): Promise<void> {
    try {
      await this.transport.stopScan();
      await this.transport.connect(this.sensorId);
    } catch (error) {
      this.log(`connect failed: ${String(error)}`);
      this.setState('ERROR');
      return;
    }
    if (!this.isIn('CONNECTING')) return; // Recovered or stopped meanwhile.
    this.connected = true;
    this.setState('DISCOVERING');
    let found: Characteristic[];
    try {
      found = await this.transport.characteristics(this.sensorId);
    } catch (error) {
      this.log(`discovery failed: ${String(error)}`);
      this.setState('ERROR');
      return;
    }
    if (!this.isIn('DISCOVERING')) return;
    const notifyUuid = normalizeUuid(SENSOR_NOTIFY_UUID);
    const writeUuid = normalizeUuid(SENSOR_WRITE_UUID);
    this.notify = found.find((c) => normalizeUuid(c.characteristic) === notifyUuid) ?? null;
    this.writeTarget = found.find((c) => normalizeUuid(c.characteristic) === writeUuid) ?? null;
    this.log(`characteristics: ${found.map((c) => `${c.service}/${c.characteristic}`).join(', ')}`);
    if (this.notify === null) {
      this.log('notify characteristic not found');
      this.setState('ERROR');
      return;
    }
    this.setState('SETTING UP');
    try {
      await this.transport.startNotification(this.sensorId, this.notify);
    } catch (error) {
      this.log(`enabling notifications failed: ${String(error)}`);
      this.setState('ERROR');
      return;
    }
    if (!this.isIn('SETTING UP')) return;
    // Counts as the last packet until data arrives.
    this.lastPacketMs = this.now();
    this.linkLost = false;
    this.setState('LIVE');
  }

  private onStopScan(): void {
    // A scan stopped because the sensor was found leaves SCANNING first.
    // Restart only when the timed scan ended without finding it.
    if (this.running && this.state === 'SCANNING') void this.startScan();
  }

  private onDisconnect(id: string): void {
    if (!this.running || !sameId(id, this.sensorId)) return;
    if (!this.connected && this.state !== 'DISCONNECTING') return;
    this.log('sensor disconnected');
    this.latest = null;
    this.sequence += 1;
    this.linkLost = true;
    void this.startScan();
  }

  private onValue(id: string, characteristic: string, value: number[]): void {
    if (
      !sameId(id, this.sensorId) ||
      this.notify === null ||
      normalizeUuid(characteristic) !== normalizeUuid(this.notify.characteristic)
    ) {
      return;
    }
    for (const frame of splitFrames(value)) this.onFrame(frame);
  }

  private onFrame(frame: number[]): void {
    if (isRegisterPacket(frame)) {
      const power = decodePowerResponse(frame);
      if (power !== null) {
        this.log(`battery ${power.percent} % (${power.voltage.toFixed(2)} V)`);
        this.battery = power;
        this.emit();
      }
      return;
    }
    const values = decodePacket(frame);
    if (values === null) return;
    this.latest = values;
    this.lastPacketMs = this.now();
    this.sequence += 1;
    this.failedRecoveries = 0;
    this.emit();
  }

  /** Recover from a stuck link and poll the battery; call regularly. */
  maintain(): void {
    if (!this.running) return;
    const now = this.now();
    const age = now - this.stateSinceMs;
    let stuck = false;
    switch (this.state) {
      case 'ERROR':
        stuck = age >= SENSOR_ERROR_RETRY_MS;
        break;
      case 'CONNECTING':
      case 'DISCOVERING':
      case 'SETTING UP':
      case 'DISCONNECTING':
        stuck = age >= SENSOR_SETUP_TIMEOUT_MS;
        break;
      case 'SCANNING':
        stuck = age >= SENSOR_SCAN_TIMEOUT_MS;
        break;
      case 'LIVE':
        stuck = now - this.lastPacketMs >= SENSOR_SILENT_RECONNECT_MS;
        break;
    }
    if (stuck) {
      void this.recover();
      return;
    }
    if (
      displayState(this.snapshot, now) === 'LIVE' &&
      this.writeTarget !== null &&
      (this.lastBatteryRequestMs === null || now - this.lastBatteryRequestMs >= BATTERY_POLL_INTERVAL_MS)
    ) {
      this.lastBatteryRequestMs = now;
      this.log('requesting battery level');
      this.transport
        .write(this.sensorId, this.writeTarget, SENSOR_POWER_READ_COMMAND)
        .catch((error) => this.log(`battery request failed: ${String(error)}`));
    }
  }

  private async recover(): Promise<void> {
    const state = this.state;
    this.log(`link stuck in ${state}; reconnecting`);
    this.failedRecoveries += 1;
    this.latest = null;
    this.sequence += 1;
    if (this.failedRecoveries >= SENSOR_RECOVERY_RESET_COUNT) {
      this.log('link did not recover; restarting Bluetooth');
      await this.stop();
      this.failedRecoveries = 0;
      await this.start();
      return;
    }
    if (this.connected && state !== 'DISCONNECTING') {
      this.linkLost = true;
      // The disconnect event starts the next scan.
      this.setState('DISCONNECTING');
      try {
        await this.transport.disconnect(this.sensorId);
        return;
      } catch (error) {
        this.log(`disconnect failed: ${String(error)}`);
      }
    }
    await this.transport.stopScan().catch(() => {});
    await this.startScan();
  }

  /** List nearby BLE devices for the settings screen; pauses the link. */
  async discover(onFound: (device: FoundDevice) => void, seconds = 10): Promise<() => Promise<void>> {
    await this.stop();
    if (!(await this.transport.start())) {
      this.setState('NO PERMISSION');
      return async () => {};
    }
    const unsubscribe = this.transport.onDiscover(onFound);
    await this.transport.scan(seconds).catch((error) => this.log(`scan failed: ${String(error)}`));
    return async () => {
      unsubscribe();
      await this.transport.stopScan().catch(() => {});
    };
  }
}
