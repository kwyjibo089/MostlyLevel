import bluetooth
import time
from config import (
    SENSOR_ACCEL_RANGE_G,
    SENSOR_ANGLE_RANGE_DEG,
    SENSOR_ATTITUDE_PACKET_LENGTH,
    SENSOR_ATTITUDE_PACKET_TYPE,
    SENSOR_BATTERY_PERCENT_BANDS,
    SENSOR_CCCD_HANDLE,
    SENSOR_ERROR_RETRY_MS,
    SENSOR_GYRO_RANGE_DPS,
    SENSOR_MAC,
    SENSOR_NAME,
    SENSOR_NOTIFY_UUID,
    SENSOR_PACKET_HEADER,
    SENSOR_POWER_READ_COMMAND,
    SENSOR_POWER_REGISTER,
    SENSOR_POWER_VOLTAGE_DIVISOR,
    SENSOR_RAW_FULL_SCALE,
    SENSOR_SCAN_TIMEOUT_MS,
    SENSOR_SETUP_TIMEOUT_MS,
    SENSOR_SILENT_RECONNECT_MS,
    SENSOR_REGISTER_PACKET_TYPE,
    SENSOR_WRITE_UUID,
)

_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE = 6
_IRQ_PERIPHERAL_CONNECT = 7
_IRQ_PERIPHERAL_DISCONNECT = 8
_IRQ_GATTC_SERVICE_RESULT = 9
_IRQ_GATTC_SERVICE_DONE = 10
_IRQ_GATTC_CHARACTERISTIC_RESULT = 11
_IRQ_GATTC_CHARACTERISTIC_DONE = 12
_IRQ_GATTC_WRITE_DONE = 17
_IRQ_GATTC_NOTIFY = 18

# Kept from the existing sensor reader. This descriptor handle still needs
# confirmation against a recorded GATT discovery on the actual sensor.
CCCD_HANDLE_CANDIDATE = SENSOR_CCCD_HANDLE


def format_address(addr):
    return ":".join("%02X" % b for b in addr)


def normalize_uuid(uuid):
    value = str(uuid).strip().lower()

    if value.startswith("uuid(") and value.endswith(")"):
        value = value[5:-1].strip()

    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        value = value[1:-1]

    if value.startswith("0x"):
        try:
            short_uuid = "%04x" % int(value[2:], 16)
            value = (
                "0000" + short_uuid
                + "-0000-1000-8000-00805f9a34fb"
            )
        except Exception:
            pass

    return value


def read_int16(data, offset):
    """Read a signed 16-bit little-endian integer."""
    value = data[offset] | (data[offset + 1] << 8)
    if value >= 32768:
        value -= 65536
    return value


def format_hex(data):
    return " ".join("%02X" % value for value in data)


def battery_percent(raw):
    """Map battery register voltage using configured model-specific bands."""
    for minimum_raw, percent in SENSOR_BATTERY_PERCENT_BANDS:
        if raw >= minimum_raw:
            return percent
    return 0


def decode_packet(packet):
    """Decode the configured fixed-length attitude notification packet."""
    if (
        len(packet) != SENSOR_ATTITUDE_PACKET_LENGTH
        or packet[0] != SENSOR_PACKET_HEADER
        or packet[1] != SENSOR_ATTITUDE_PACKET_TYPE
    ):
        return None

    raw = []
    for offset in range(2, 20, 2):
        raw.append(read_int16(packet, offset))

    ax, ay, az = raw[0:3]
    gx, gy, gz = raw[3:6]
    roll, pitch, yaw = raw[6:9]

    return {
        "acc_x": ax * SENSOR_ACCEL_RANGE_G / SENSOR_RAW_FULL_SCALE,
        "acc_y": ay * SENSOR_ACCEL_RANGE_G / SENSOR_RAW_FULL_SCALE,
        "acc_z": az * SENSOR_ACCEL_RANGE_G / SENSOR_RAW_FULL_SCALE,
        "gyro_x": gx * SENSOR_GYRO_RANGE_DPS / SENSOR_RAW_FULL_SCALE,
        "gyro_y": gy * SENSOR_GYRO_RANGE_DPS / SENSOR_RAW_FULL_SCALE,
        "gyro_z": gz * SENSOR_GYRO_RANGE_DPS / SENSOR_RAW_FULL_SCALE,
        "roll": roll * SENSOR_ANGLE_RANGE_DEG / SENSOR_RAW_FULL_SCALE,
        "pitch": pitch * SENSOR_ANGLE_RANGE_DEG / SENSOR_RAW_FULL_SCALE,
        "yaw": yaw * SENSOR_ANGLE_RANGE_DEG / SENSOR_RAW_FULL_SCALE,
    }


def print_measurements(values):
    print(
        "%s P:%+.2f R:%+.2f Y:%+.2f"
        % (SENSOR_NAME, values["pitch"], values["roll"], values["yaw"])
    )


class WT901BLEClient:
    """Connect to the configured sensor and retain its latest decoded sample.

    BLE IRQ callbacks only update state and values. The display loop polls
    `latest`, so SPI rendering never runs inside the BLE interrupt handler.
    """

    def __init__(self):
        self.ble = bluetooth.BLE()
        self.ble.active(True)

        self.conn_handle = None
        self.notify_handle = None
        self.write_handle = None
        self.connected = False
        self.state = "IDLE"
        self.state_since_ms = time.ticks_ms()
        # Recoveries since the last attitude packet; see maintain().
        self.failed_recoveries = 0
        # True from a lost connection until notifications run again, so the
        # display can report the loss while the client rescans.
        self.link_lost = False
        self.latest = None
        self.sequence = 0
        self.last_packet_ms = 0
        self.last_power_response = None
        self.power_raw = None
        self.power_voltage = None
        self.power_percent = None

    def start(self):
        self.ble.irq(self._irq)
        self._start_scan()

    def _set_state(self, state):
        self.state = state
        self.state_since_ms = time.ticks_ms()

    def maintain(self):
        """Recover from a stuck link; call this regularly from the main loop.

        BLE callbacks alone cannot notice that an expected event never came,
        and some failures leave the client in ERROR. After a timeout the
        client disconnects if needed and scans again.
        """
        now = time.ticks_ms()
        state = self.state
        age = time.ticks_diff(now, self.state_since_ms)
        if state == "ERROR":
            stuck = age >= SENSOR_ERROR_RETRY_MS
        elif state in ("CONNECTING", "DISCOVERING", "SETTING UP", "DISCONNECTING"):
            stuck = age >= SENSOR_SETUP_TIMEOUT_MS
        elif state == "SCANNING":
            # A timed scan ends with a scan-done event, which rescans.
            stuck = age >= SENSOR_SCAN_TIMEOUT_MS
        elif state == "LIVE":
            stuck = (
                time.ticks_diff(now, self.last_packet_ms) >= SENSOR_SILENT_RECONNECT_MS
            )
        else:
            stuck = False
        if stuck:
            self._recover(state)

    def _recover(self, state):
        print("Sensor link stuck in %s; reconnecting." % state)
        self.failed_recoveries += 1
        self.latest = None
        self.sequence += 1
        if self.connected and self.conn_handle is not None and state != "DISCONNECTING":
            self.link_lost = True
            try:
                self.ble.gap_disconnect(self.conn_handle)
                # The disconnect event starts the next scan.
                self._set_state("DISCONNECTING")
                return
            except Exception as exc:
                print("Disconnect failed:", exc)
        try:
            self.ble.gap_scan(None)
        except Exception:
            pass
        self._start_scan()

    def _start_scan(self):
        self.conn_handle = None
        self.notify_handle = None
        self.write_handle = None
        self.connected = False
        self._set_state("SCANNING")
        print("Scanning for %s:" % SENSOR_NAME, format_address(SENSOR_MAC))

        try:
            self.ble.gap_scan(15000, 30000, 30000, True)
        except Exception as exc:
            self._set_state("ERROR")
            print("BLE scan failed:", exc)

    def _enable_notifications(self):
        if self.conn_handle is None or self.notify_handle is None:
            self._set_state("ERROR")
            return

        self._set_state("SETTING UP")
        try:
            # This is the handle used by the existing reader. It is not
            # derived from the discovered descriptor table yet.
            self.ble.gattc_write(
                self.conn_handle,
                CCCD_HANDLE_CANDIDATE,
                b"\x01\x00",
                1,
            )
            print("Requested sensor notifications.")
        except Exception as exc:
            self._set_state("ERROR")
            print("Failed to enable notifications:", exc)

    def request_power_read(self, keep_previous=False):
        """Request the sensor's power register for a one-shot diagnostic."""
        if self.conn_handle is None or self.write_handle is None:
            raise RuntimeError("Sensor must be connected before reading power.")

        if not keep_previous:
            self.last_power_response = None
            self.power_raw = None
            self.power_voltage = None
            self.power_percent = None
        self.ble.gattc_write(
            self.conn_handle,
            self.write_handle,
            SENSOR_POWER_READ_COMMAND,
            1,
        )
        print(
            "Requested power register 0x%02X; waiting for sensor response."
            % SENSOR_POWER_REGISTER
        )

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data

            if bytes(addr) == SENSOR_MAC and not self.connected:
                print("Found", SENSOR_NAME, format_address(addr), "RSSI", rssi)
                self._set_state("CONNECTING")
                try:
                    self.ble.gap_scan(None)
                    self.ble.gap_connect(addr_type, bytes(addr))
                except Exception as exc:
                    self._set_state("ERROR")
                    print("Connection request failed:", exc)

        elif event == _IRQ_SCAN_DONE:
            # A scan is stopped explicitly when the target is found.
            # Restart only when the timed scan ended without finding it.
            if self.state == "SCANNING":
                self._start_scan()

        elif event == _IRQ_PERIPHERAL_CONNECT:
            self.conn_handle, addr_type, addr = data
            self.connected = True
            self._set_state("DISCOVERING")
            print("Connected to %s." % SENSOR_NAME)
            try:
                self.ble.gattc_discover_services(self.conn_handle)
            except Exception as exc:
                self._set_state("ERROR")
                print("Service discovery failed:", exc)

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            handle, start_handle, end_handle, uuid = data
            print("Service:", start_handle, end_handle, uuid)

        elif event == _IRQ_GATTC_SERVICE_DONE:
            callback_conn_handle, status = data
            if status == 0:
                try:
                    self.ble.gattc_discover_characteristics(
                        self.conn_handle, 1, 0xFFFF
                    )
                except Exception as exc:
                    self._set_state("ERROR")
                    print("Characteristic discovery failed:", exc)
            else:
                self._set_state("ERROR")
                print("Service discovery status:", status)

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            (
                callback_conn_handle,
                def_handle,
                value_handle,
                properties,
                uuid,
            ) = data
            uuid_str = normalize_uuid(uuid)
            print("Characteristic:", uuid_str, "handle:", value_handle)

            if uuid_str == SENSOR_NOTIFY_UUID:
                self.notify_handle = value_handle
            elif uuid_str == SENSOR_WRITE_UUID:
                self.write_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            callback_conn_handle, status = data
            if status == 0 and self.notify_handle is not None:
                self._enable_notifications()
            else:
                self._set_state("ERROR")
                print("Sensor notification characteristic not found.")

        elif event == _IRQ_GATTC_WRITE_DONE:
            callback_conn_handle, value_handle, status = data
            if value_handle == CCCD_HANDLE_CANDIDATE and status == 0:
                self._set_state("LIVE")
                # Counts as the last packet until data arrives.
                self.last_packet_ms = time.ticks_ms()
                self.link_lost = False
                print("Sensor notifications enabled.")
            elif value_handle == CCCD_HANDLE_CANDIDATE:
                self._set_state("ERROR")
                print("Notification setup status:", status)

        elif event == _IRQ_GATTC_NOTIFY:
            notify_conn_handle, value_handle, notify_data = data
            if value_handle != self.notify_handle:
                return

            packet = bytes(notify_data)
            if (
                len(packet) >= 4
                and packet[0] == SENSOR_PACKET_HEADER
                and packet[1] == SENSOR_REGISTER_PACKET_TYPE
            ):
                self.last_power_response = packet
                print("Sensor register response:", format_hex(packet))

                start_register = packet[2] | (packet[3] << 8)
                if start_register == SENSOR_POWER_REGISTER and len(packet) >= 6:
                    self.power_raw = packet[4] | (packet[5] << 8)
                    self.power_voltage = self.power_raw / SENSOR_POWER_VOLTAGE_DIVISOR
                    self.power_percent = battery_percent(self.power_raw)
                    print(
                        "Sensor battery: %d%% (%.2f V, raw %d)"
                        % (self.power_percent, self.power_voltage, self.power_raw)
                    )
                return

            values = decode_packet(packet)
            if values is None:
                return

            self.latest = values
            self.last_packet_ms = time.ticks_ms()
            self.sequence += 1
            self.failed_recoveries = 0

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            disconnected_handle, addr_type, addr = data
            print("Sensor disconnected:", format_address(addr))
            self.latest = None
            self.sequence += 1
            self.link_lost = True
            self._start_scan()


def run_console_reader():
    """Optional serial diagnostic entry point; importing this module is safe."""
    client = WT901BLEClient()
    client.start()
    last_sequence = -1

    while True:
        if client.sequence != last_sequence:
            last_sequence = client.sequence
            if client.latest is not None:
                print_measurements(client.latest)
        time.sleep_ms(100)


if __name__ == "__main__":
    run_console_reader()
