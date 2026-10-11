import bluetooth
import time

TARGET_MAC = bytes.fromhex("F0A07ADB7D45")

# MicroPython BLE IRQ event constants
_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE = 6
_IRQ_PERIPHERAL_CONNECT = 7
_IRQ_PERIPHERAL_DISCONNECT = 8
_IRQ_GATTC_SERVICE_RESULT = 9
_IRQ_GATTC_SERVICE_DONE = 10
_IRQ_GATTC_CHARACTERISTIC_RESULT = 11
_IRQ_GATTC_CHARACTERISTIC_DONE = 12
_IRQ_GATTC_DESCRIPTOR_RESULT = 13
_IRQ_GATTC_DESCRIPTOR_DONE = 14

# Characteristic property flags
_PROP_READ = 0x0002
_PROP_WRITE_NO_RESPONSE = 0x0004
_PROP_WRITE = 0x0008
_PROP_NOTIFY = 0x0010
_PROP_INDICATE = 0x0020

ble = bluetooth.BLE()
ble.active(True)

connected = False
conn_handle = None
service_discovery_started = False
characteristic_discovery_started = False
services = []
characteristics = []


def format_address(addr):
    return ":".join("%02X" % b for b in addr)


def format_uuid(uuid):
    return str(uuid)


def format_properties(props):
    names = []

    if props & _PROP_READ:
        names.append("READ")
    if props & _PROP_WRITE:
        names.append("WRITE")
    if props & _PROP_WRITE_NO_RESPONSE:
        names.append("WRITE_NO_RESPONSE")
    if props & _PROP_NOTIFY:
        names.append("NOTIFY")
    if props & _PROP_INDICATE:
        names.append("INDICATE")

    return ", ".join(names) if names else "NONE"


def on_ble_event(event, data):
    global connected, conn_handle
    global service_discovery_started
    global characteristic_discovery_started

    if event == _IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data

        if bytes(addr) == TARGET_MAC and not connected:
            print("\n*** WT901BLE SENSOR FOUND ***")
            print("Address:", format_address(addr))
            print("Address type:", addr_type)
            print("RSSI:", rssi, "dBm")
            print("Advertisement type:", adv_type)
            print("Raw advertisement:", bytes(adv_data))

            # Stop scanning and connect.
            try:
                ble.gap_scan(None)
                ble.gap_connect(addr_type, addr)
                print("\nConnecting to WT901BLECL...")
            except Exception as exc:
                print("Connection request failed:", exc)

    elif event == _IRQ_SCAN_DONE:
        print("Scan complete.")

    elif event == _IRQ_PERIPHERAL_CONNECT:
        conn_handle, addr_type, addr = data
        connected = True

        print("\n*** CONNECTED ***")
        print("Connection handle:", conn_handle)

        try:
            ble.gattc_discover_services(conn_handle)
            service_discovery_started = True
            print("\nDiscovering services...")
        except Exception as exc:
            print("Service discovery failed:", exc)

    elif event == _IRQ_GATTC_SERVICE_RESULT:
        handle, start_handle, end_handle, uuid = data

        services.append((start_handle, end_handle, uuid))

        print(
            "SERVICE:",
            "start =", start_handle,
            "end =", end_handle,
            "UUID =", format_uuid(uuid),
        )

    elif event == _IRQ_GATTC_SERVICE_DONE:
        status = data[1]
        print("\nService discovery complete. Status:", status)

        if status == 0 and services:
            # Discover characteristics across the entire GATT table.
            try:
                ble.gattc_discover_characteristics(
                    conn_handle, 1, 0xFFFF
                )
                characteristic_discovery_started = True
                print("\nDiscovering characteristics...")
            except Exception as exc:
                print("Characteristic discovery failed:", exc)
        else:
            print("No services discovered or discovery failed.")

    elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
        handle, def_handle, value_handle, properties, uuid = data

        characteristics.append(
            (def_handle, value_handle, properties, uuid)
        )

        print(
            "CHARACTERISTIC:",
            "value_handle =", value_handle,
            "properties =", format_properties(properties),
            "UUID =", format_uuid(uuid),
        )

    elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
        status = data[1]
        print("\nCharacteristic discovery complete. Status:", status)

        print("\n*** DISCOVERY SUMMARY ***")
        print("Services:", len(services))
        print("Characteristics:", len(characteristics))
        print("\nPlease save this output for the next step.")

    elif event == _IRQ_PERIPHERAL_DISCONNECT:
        conn_handle_disconnected, addr_type, addr = data

        print("\nDisconnected from WT901BLECL.")

        connected = False
        conn_handle = None


ble.irq(on_ble_event)

print("Scanning for WT901BLECL...")
print("Target MAC: F0:A0:7A:DB:7D:45")
print("Keep the sensor close to the ESP32-S3.")
print("Make sure the sensor is not connected to another device.")

ble.gap_scan(15000, 30000, 30000, True)

while True:
    time.sleep_ms(100)
