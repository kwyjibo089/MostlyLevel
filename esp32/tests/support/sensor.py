"""Simulated WT901 BLE sensor that drives the client through BLE events.

Packet layouts follow the assumptions in `src/ble_read.py` and
`src/config.py`; they are not captured from a real sensor.
"""

import struct

import fakehw
from bluetooth import UUID
from config import (
    SENSOR_ANGLE_RANGE_DEG,
    SENSOR_CCCD_HANDLE,
    SENSOR_MAC,
    SENSOR_NOTIFY_UUID,
    SENSOR_POWER_REGISTER,
    SENSOR_RAW_FULL_SCALE,
    SENSOR_WRITE_UUID,
)

IRQ_SCAN_RESULT = 5
IRQ_SCAN_DONE = 6
IRQ_PERIPHERAL_CONNECT = 7
IRQ_PERIPHERAL_DISCONNECT = 8
IRQ_GATTC_SERVICE_RESULT = 9
IRQ_GATTC_SERVICE_DONE = 10
IRQ_GATTC_CHARACTERISTIC_RESULT = 11
IRQ_GATTC_CHARACTERISTIC_DONE = 12
IRQ_GATTC_WRITE_DONE = 17
IRQ_GATTC_NOTIFY = 18

CONN_HANDLE = 0
NOTIFY_HANDLE = SENSOR_CCCD_HANDLE - 1
WRITE_HANDLE = SENSOR_CCCD_HANDLE + 3


def angle_raw(degrees):
    return int(round(degrees * SENSOR_RAW_FULL_SCALE / SENSOR_ANGLE_RANGE_DEG))


def attitude_packet(roll=0.0, pitch=0.0, yaw=0.0):
    raw = (0, 0, 2048, 0, 0, 0, angle_raw(roll), angle_raw(pitch), angle_raw(yaw))
    return bytes((0x55, 0x61)) + struct.pack("<9h", *raw)


def power_packet(raw):
    return (
        bytes((0x55, 0x71)) + struct.pack("<HH", SENSOR_POWER_REGISTER, raw) + bytes(14)
    )


class SensorSimulator:
    """Feeds BLE events for the configured sensor into the active fake BLE."""

    def __init__(self):
        self.ble = fakehw.ble

    def irq(self, event, data):
        self.ble.handler(event, data)

    def advertise(self, address=SENSOR_MAC):
        self.irq(IRQ_SCAN_RESULT, (0, address, 0, -60, b""))

    def scan_done(self):
        self.irq(IRQ_SCAN_DONE, (0,))

    def connect(self, cccd_status=0):
        """Run connection, discovery, and notification setup."""
        self.advertise()
        self.irq(IRQ_PERIPHERAL_CONNECT, (CONN_HANDLE, 0, SENSOR_MAC))
        self.irq(IRQ_GATTC_SERVICE_RESULT, (CONN_HANDLE, 1, 30, UUID(0xFFE0)))
        self.irq(IRQ_GATTC_SERVICE_DONE, (CONN_HANDLE, 0))
        self.irq(
            IRQ_GATTC_CHARACTERISTIC_RESULT,
            (CONN_HANDLE, NOTIFY_HANDLE - 1, NOTIFY_HANDLE, 0x10, UUID(SENSOR_NOTIFY_UUID)),
        )
        self.irq(
            IRQ_GATTC_CHARACTERISTIC_RESULT,
            (CONN_HANDLE, WRITE_HANDLE - 1, WRITE_HANDLE, 0x0C, UUID(SENSOR_WRITE_UUID)),
        )
        self.irq(IRQ_GATTC_CHARACTERISTIC_DONE, (CONN_HANDLE, 0))
        self.irq(IRQ_GATTC_WRITE_DONE, (CONN_HANDLE, SENSOR_CCCD_HANDLE, cccd_status))

    def notify(self, packet, handle=NOTIFY_HANDLE):
        self.irq(IRQ_GATTC_NOTIFY, (CONN_HANDLE, handle, packet))

    def attitude(self, roll=0.0, pitch=0.0, yaw=0.0):
        """Send decoded-channel angles (before the app's axis mapping)."""
        self.notify(attitude_packet(roll, pitch, yaw))

    def power(self, raw):
        self.notify(power_packet(raw))

    def disconnect(self):
        self.irq(IRQ_PERIPHERAL_DISCONNECT, (CONN_HANDLE, 0, SENSOR_MAC))
