"""Unit tests for the WT901 BLE client and packet decoder (src/ble_read.py).

These check the code against its documented packet assumptions; they do not
prove that a real sensor sends these packets.
"""

import pytest
from support.sensor import (
    NOTIFY_HANDLE,
    WRITE_HANDLE,
    SensorSimulator,
    attitude_packet,
    power_packet,
)


@pytest.fixture
def ble_read(import_fresh):
    return import_fresh("ble_read")


@pytest.fixture
def client(ble_read):
    client = ble_read.WT901BLEClient()
    client.start()
    return client


def test_read_int16_is_signed_little_endian(ble_read):
    assert ble_read.read_int16(b"\x34\x12", 0) == 0x1234
    assert ble_read.read_int16(b"\xff\xff", 0) == -1
    assert ble_read.read_int16(b"\x00\x80", 0) == -32768


@pytest.mark.parametrize(
    "text",
    [
        "UUID('0000ffe4-0000-1000-8000-00805f9a34fb')",
        "UUID(0xffe4)",
        "0000FFE4-0000-1000-8000-00805F9A34FB",
    ],
)
def test_normalize_uuid_accepts_micropython_forms(ble_read, text):
    assert ble_read.normalize_uuid(text) == "0000ffe4-0000-1000-8000-00805f9a34fb"


@pytest.mark.parametrize(
    "raw, percent",
    [
        (385, 60),  # Owner observation: 3.85 V matched 60% in the Android app.
        (397, 100),
        (396, 90),
        (382, 60),
        (381, 50),
        (340, 5),
        (339, 0),
    ],
)
def test_battery_percent_bands(ble_read, raw, percent):
    assert ble_read.battery_percent(raw) == percent


def test_decode_packet_scales_angles(ble_read):
    values = ble_read.decode_packet(attitude_packet(roll=12.5, pitch=-3.25, yaw=90.0))
    assert values["roll"] == pytest.approx(12.5, abs=0.01)
    assert values["pitch"] == pytest.approx(-3.25, abs=0.01)
    assert values["yaw"] == pytest.approx(90.0, abs=0.01)
    assert values["acc_z"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "packet",
    [
        attitude_packet()[:-1],
        b"\x54" + attitude_packet()[1:],
        b"\x55\x71" + attitude_packet()[2:],
    ],
)
def test_decode_packet_rejects_other_packets(ble_read, packet):
    assert ble_read.decode_packet(packet) is None


def test_print_measurements_formats_values(ble_read, capsys):
    ble_read.print_measurements({"pitch": 1.234, "roll": -0.5, "yaw": 12.0})
    assert capsys.readouterr().out.strip() == "WT901BLE67 P:+1.23 R:-0.50 Y:+12.00"


def scans_started(ble):
    """gap_scan calls that start a scan; gap_scan(None) only stops one."""
    return [call for call in ble.calls if call[0] == "gap_scan" and call[1] is not None]


def test_start_scans_for_sensor(client):
    ble = SensorSimulator().ble
    assert ble.calls[0][0] == "gap_scan"
    assert client.state == "SCANNING"


def test_other_devices_are_ignored(client):
    sim = SensorSimulator()
    sim.advertise(b"\x01\x02\x03\x04\x05\x06")
    assert client.state == "SCANNING"
    assert not [call for call in sim.ble.calls if call[0] == "gap_connect"]


def test_scan_restarts_when_it_times_out(client):
    sim = SensorSimulator()
    sim.scan_done()
    assert len(scans_started(sim.ble)) == 2


def test_connection_enables_notifications(client, ble_read):
    sim = SensorSimulator()
    sim.connect()
    assert client.state == "LIVE"
    assert client.notify_handle == NOTIFY_HANDLE
    assert client.write_handle == WRITE_HANDLE
    cccd_write = sim.ble.writes(ble_read.CCCD_HANDLE_CANDIDATE)
    assert cccd_write and cccd_write[0][3] == b"\x01\x00"


def test_failed_notification_setup_is_an_error(client):
    SensorSimulator().connect(cccd_status=1)
    assert client.state == "ERROR"


def test_attitude_notification_updates_latest(client, fake_clock):
    sim = SensorSimulator()
    sim.connect()
    fake_clock.advance(1234)
    sim.attitude(roll=1.5, pitch=-2.0)
    assert client.latest["roll"] == pytest.approx(1.5, abs=0.01)
    assert client.latest["pitch"] == pytest.approx(-2.0, abs=0.01)
    assert client.last_packet_ms == 1234


def test_notifications_from_other_handles_are_ignored(client):
    sim = SensorSimulator()
    sim.connect()
    sim.notify(attitude_packet(roll=5.0), handle=NOTIFY_HANDLE + 10)
    assert client.latest is None


def test_power_read_request_and_response(client):
    sim = SensorSimulator()
    sim.connect()
    client.request_power_read()
    request = sim.ble.writes(WRITE_HANDLE)[-1]
    assert request[3] == bytes((0xFF, 0xAA, 0x27, 0x64, 0x00))

    sim.power(385)
    assert client.power_raw == 385
    assert client.power_voltage == pytest.approx(3.85)
    assert client.power_percent == 60
    assert client.last_power_response == power_packet(385)


def test_power_read_needs_connection(client):
    with pytest.raises(RuntimeError):
        client.request_power_read()


def test_disconnect_clears_data_and_rescans(client):
    sim = SensorSimulator()
    sim.connect()
    sim.attitude(roll=1.0)
    sim.disconnect()
    assert client.latest is None
    assert client.connected is False
    # The client restarts scanning immediately, so the dashboard sees
    # SCANNING rather than DISCONNECTED.
    assert client.state == "SCANNING"
    assert len(scans_started(sim.ble)) == 2
