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

CCCD_HANDLE_CANDIDATE = 16

ble = bluetooth.BLE()
ble.active(True)

conn_handle = None
notify_handle = None
write_handle = None
connected = False

last_print_time = 0


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
    """
    Decode a WT901BLE 0x61 packet.

    Expected format:
    55 61 + 9 signed 16-bit values
    """

    if len(packet) != 20:
        return None

    if packet[0] != 0x55 or packet[1] != 0x61:
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
    print()
    print("-------- WT901BLE67 --------")

    print(
        "Roll:       {:+8.2f} deg".format(values["roll"])
    )
    print(
        "Pitch:      {:+8.2f} deg".format(values["pitch"])
    )
    print(
        "Yaw:        {:+8.2f} deg".format(values["yaw"])
    )

    print()

    print(
        "Accel X:    {:+8.3f} g".format(values["acc_x"])
    )
    print(
        "Accel Y:    {:+8.3f} g".format(values["acc_y"])
    )
    print(
        "Accel Z:    {:+8.3f} g".format(values["acc_z"])
    )

    print()

    print(
        "Gyro X:     {:+8.2f} deg/s".format(values["gyro_x"])
    )
    print(
        "Gyro Y:     {:+8.2f} deg/s".format(values["gyro_y"])
    )
    print(
        "Gyro Z:     {:+8.2f} deg/s".format(values["gyro_z"])
    )

    print("----------------------------")


def enable_notifications():
    print("Enabling sensor notifications...")

    try:
        ble.gattc_write(
            conn_handle,
            CCCD_HANDLE_CANDIDATE,
            b"\x01\x00",
            1,
        )
        print("Notification enable request submitted.")

    except Exception as exc:
        print("Failed to enable notifications:", exc)


def on_ble_event(event, data):
    global conn_handle
    global notify_handle, write_handle
    global connected, last_print_time

    if event == _IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data

        if bytes(addr) == TARGET_MAC and not connected:
            print("\nWT901BLE67 found:", format_address(addr))
            print("RSSI:", rssi, "dBm")

            try:
                ble.gap_scan(None)
                ble.gap_connect(addr_type, addr)
                print("Connecting...")

            except Exception as exc:
                print("Connection failed:", exc)

    elif event == _IRQ_SCAN_DONE:
        print("Scan complete.")

    elif event == _IRQ_PERIPHERAL_CONNECT:
        conn_handle, addr_type, addr = data
        connected = True

        print("\nConnected to WT901BLE67.")
        print("Connection handle:", conn_handle)

        try:
            ble.gattc_discover_services(conn_handle)
            print("Discovering services...")

        except Exception as exc:
            print("Service discovery failed:", exc)

    elif event == _IRQ_GATTC_SERVICE_RESULT:
        handle, start_handle, end_handle, uuid = data

        print(
            "Service:",
            start_handle,
            end_handle,
            uuid,
        )

    elif event == _IRQ_GATTC_SERVICE_DONE:
        status = data[1]

        print("Service discovery complete:", status)

        if status == 0:
            try:
                ble.gattc_discover_characteristics(
                    conn_handle,
                    1,
                    0xFFFF,
                )
            except Exception as exc:
                print("Characteristic discovery failed:", exc)

    elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
        (
            callback_conn_handle,
            def_handle,
            value_handle,
            properties,
            uuid,
        ) = data

        uuid_str = normalize_uuid(uuid)

        print(
            "Characteristic:",
            uuid_str,
            "value handle:",
            value_handle,
            "properties:",
            properties,
        )

        if uuid_str == NOTIFY_UUID_STR:
            notify_handle = value_handle

        elif uuid_str == WRITE_UUID_STR:
            write_handle = value_handle

    elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
        status = data[1]

        print("Characteristic discovery complete:", status)
        print("Notification handle:", notify_handle)
        print("Write handle:", write_handle)

        if status == 0 and notify_handle is not None:
            enable_notifications()
        else:
            print("Could not find notification characteristic.")

    elif event == _IRQ_GATTC_WRITE_DONE:
        print("GATT write completed:", data)

    elif event == _IRQ_GATTC_NOTIFY:
        notify_conn_handle, value_handle, notify_data = data

        if value_handle != notify_handle:
            return

        packet = bytes(notify_data)
        values = decode_packet(packet)

        if values is None:
            print("Unexpected packet:", packet.hex())
            return

        # Print at most five times per second.
        # This keeps the serial console readable.
        now = time.ticks_ms()

        if (
            last_print_time == 0
            or time.ticks_diff(now, last_print_time) >= 200
        ):
            last_print_time = now
            print_measurements(values)

    elif event == _IRQ_PERIPHERAL_DISCONNECT:
        disconnected_handle, addr_type, addr = data

        print("\nSensor disconnected:", format_address(addr))

        connected = False
        conn_handle = None
        notify_handle = None
        write_handle = None


ble.irq(on_ble_event)

print("Scanning for WT901BLE67...")
print("Target MAC: F0:A0:7A:DB:7D:45")
print("Make sure the sensor is powered on.")

try:
    ble.gap_scan(
        15000,
        30000,
        30000,
        True,
    )
except Exception as exc:
    print("BLE scan failed:", exc)

while True:
    time.sleep_ms(100)