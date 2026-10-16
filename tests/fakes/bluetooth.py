"""Fake MicroPython `bluetooth` module that records client calls.

Tests deliver BLE events by calling the handler registered with `BLE.irq`,
usually through `support.sensor.SensorSimulator`.
"""

import fakehw


class UUID:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        # Matches MicroPython: UUID(0xffe4) or UUID('0000ffe4-...').
        if isinstance(self.value, int):
            return "UUID(0x%04x)" % self.value
        return "UUID('%s')" % self.value


class BLE:
    def __init__(self):
        self.calls = []
        self.handler = None
        self.is_active = False
        fakehw.ble = self

    def active(self, value=None):
        if value is not None:
            self.is_active = bool(value)
        return self.is_active

    def irq(self, handler):
        self.handler = handler

    def gap_scan(self, duration_ms, *args):
        self.calls.append(("gap_scan", duration_ms) + tuple(args))

    def gap_connect(self, addr_type, addr):
        self.calls.append(("gap_connect", addr_type, bytes(addr)))

    def gap_disconnect(self, conn_handle):
        self.calls.append(("gap_disconnect", conn_handle))

    def gattc_discover_services(self, conn_handle):
        self.calls.append(("discover_services", conn_handle))

    def gattc_discover_characteristics(self, conn_handle, start, end):
        self.calls.append(("discover_characteristics", conn_handle, start, end))

    def gattc_write(self, conn_handle, value_handle, data, mode=0):
        self.calls.append(("write", conn_handle, value_handle, bytes(data), mode))

    def writes(self, value_handle=None):
        return [
            call for call in self.calls
            if call[0] == "write" and (value_handle is None or call[2] == value_handle)
        ]
