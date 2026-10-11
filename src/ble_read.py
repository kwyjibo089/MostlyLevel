import bluetooth
import time


TARGET_MAC = bytes.fromhex("F0A07ADB7D45")

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

WRITE_UUID_STR = "0000ffe9-0000-1000-8000-00805f9a34fb"
NOTIFY_UUID_STR = "0000ffe4-0000-1000-8000-00805f9a34fb"

# Kept from the existing sensor reader. This descriptor handle still needs
# confirmation against a recorded GATT discovery on the actual sensor.
CCCD_HANDLE_CANDIDATE = 16


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


def decode_packet(packet):
    """Decode the 20-byte 0x61 notification format used by the old reader."""
    if len(packet) != 20 or packet[0] != 0x55 or packet[1] != 0x61:
        return None

    raw = []
    for offset in range(2, 20, 2):
        raw.append(read_int16(packet, offset))

    ax, ay, az = raw[0:3]
    gx, gy, gz = raw[3:6]
    roll, pitch, yaw = raw[6:9]

    return {
        "acc_x": ax * 16.0 / 32768.0,
        "acc_y": ay * 16.0 / 32768.0,
        "acc_z": az * 16.0 / 32768.0,
        "gyro_x": gx * 2000.0 / 32768.0,
        "gyro_y": gy * 2000.0 / 32768.0,
        "gyro_z": gz * 2000.0 / 32768.0,
        "roll": roll * 180.0 / 32768.0,
        "pitch": pitch * 180.0 / 32768.0,
        "yaw": yaw * 180.0 / 32768.0,
    }


def print_measurements(values):
    print(
        "WT901BLE67 P:{:+.2f} R:{:+.2f} Y:{:+.2f}".format(
            values["pitch"], values["roll"], values["yaw"]
        )
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
        self.latest = None
        self.sequence = 0
        self.last_packet_ms = 0

    def start(self):
        self.ble.irq(self._irq)
        self._start_scan()

    def _start_scan(self):
        self.conn_handle = None
        self.notify_handle = None
        self.write_handle = None
        self.connected = False
        self.state = "SCANNING"
        print("Scanning for WT901BLE67:", format_address(TARGET_MAC))

        try:
            self.ble.gap_scan(15000, 30000, 30000, True)
        except Exception as exc:
            self.state = "ERROR"
            print("BLE scan failed:", exc)

    def _enable_notifications(self):
        if self.conn_handle is None or self.notify_handle is None:
            self.state = "ERROR"
            return

        self.state = "SETTING UP"
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
            self.state = "ERROR"
            print("Failed to enable notifications:", exc)

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data

            if bytes(addr) == TARGET_MAC and not self.connected:
                print("Found WT901BLE67", format_address(addr), "RSSI", rssi)
                self.state = "CONNECTING"
                try:
                    self.ble.gap_scan(None)
                    self.ble.gap_connect(addr_type, bytes(addr))
                except Exception as exc:
                    self.state = "ERROR"
                    print("Connection request failed:", exc)

        elif event == _IRQ_SCAN_DONE:
            # A scan is stopped explicitly when the target is found.
            # Restart only when the timed scan ended without finding it.
            if self.state == "SCANNING":
                self._start_scan()

        elif event == _IRQ_PERIPHERAL_CONNECT:
            self.conn_handle, addr_type, addr = data
            self.connected = True
            self.state = "DISCOVERING"
            print("Connected to WT901BLE67.")
            try:
                self.ble.gattc_discover_services(self.conn_handle)
            except Exception as exc:
                self.state = "ERROR"
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
                    self.state = "ERROR"
                    print("Characteristic discovery failed:", exc)
            else:
                self.state = "ERROR"
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

            if uuid_str == NOTIFY_UUID_STR:
                self.notify_handle = value_handle
            elif uuid_str == WRITE_UUID_STR:
                self.write_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            callback_conn_handle, status = data
            if status == 0 and self.notify_handle is not None:
                self._enable_notifications()
            else:
                self.state = "ERROR"
                print("Sensor notification characteristic not found.")

        elif event == _IRQ_GATTC_WRITE_DONE:
            callback_conn_handle, value_handle, status = data
            if value_handle == CCCD_HANDLE_CANDIDATE and status == 0:
                self.state = "LIVE"
                print("Sensor notifications enabled.")
            elif value_handle == CCCD_HANDLE_CANDIDATE:
                self.state = "ERROR"
                print("Notification setup status:", status)

        elif event == _IRQ_GATTC_NOTIFY:
            notify_conn_handle, value_handle, notify_data = data
            if value_handle != self.notify_handle:
                return

            values = decode_packet(bytes(notify_data))
            if values is None:
                return

            self.latest = values
            self.last_packet_ms = time.ticks_ms()
            self.sequence += 1

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            disconnected_handle, addr_type, addr = data
            print("Sensor disconnected:", format_address(addr))
            self.latest = None
            self.sequence += 1
            self.state = "DISCONNECTED"
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
