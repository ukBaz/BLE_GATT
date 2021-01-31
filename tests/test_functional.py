import io
from pathlib import Path
import subprocess
import dbus
import dbusmock
from gi.repository import GLib
from unittest.mock import patch

import BLE_GATT


class TestBasicFunctionality(dbusmock.DBusTestCase):
    """
    Test mocking bluetoothd
    """

    @classmethod
    def setUpClass(cls):
        cls.start_system_bus()
        cls.dbus_con = cls.get_dbus(True)

    def setUp(self):
        here = Path(__file__).parent
        template = str(here.joinpath('dbusmock_templates',
                                          'bluez_scan.py'))
        (self.p_mock, self.obj_bluez) = self.spawn_server_template(
            template, {}, stdout=subprocess.PIPE)

        self.dbusmock = dbus.Interface(self.obj_bluez, dbusmock.MOCK_IFACE)
        self.obj_bluez.Reset()
        self.dbusmock_bluez = dbus.Interface(self.obj_bluez, 'org.bluez.Mock')

    def tearDown(self) -> None:
        # self.stop_dbus(self.system_bus_pid)
        self.p_mock.stdout.close()
        self.p_mock.terminate()
        self.p_mock.wait()

    def test_find_paths(self):
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'E9:06:4D:45:FC:8D', '')

        central = BLE_GATT.Central('E9:06:4D:45:FC:8D')
        self.assertEqual('/org/bluez/hci0/dev_E9_06_4D_45_FC_8D',
                         central._device_path)
        self.assertEqual('/org/bluez/hci0', central._adapter_path)

    def test_missing_device(self):
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'E9:06:4D:45:FC:8D', '')

        with self.assertRaises(KeyError) as exception:
            central = BLE_GATT.Central('11:22:33:44:55:66')

    def test_read_write_characteristic(self):
        test_uuid = 'e95d9250-251d-470a-a062-fa1922dfa9a8'
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'E9:06:4D:45:FC:8D', '')
        central = BLE_GATT.Central('E9:06:4D:45:FC:8D')
        central.connect()
        value = central.char_read(test_uuid)
        self.assertListEqual([27], value)
        central.char_write(test_uuid, [29])
        value = central.char_read(test_uuid)
        self.assertListEqual([29], value)
        central.disconnect()

    def test_bad_uuid(self):
        bad_uuid = '12345678-1234-1234-0123456789AB'
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'E9:06:4D:45:FC:8D', '')
        central = BLE_GATT.Central('E9:06:4D:45:FC:8D')
        central.connect()
        with self.assertRaises(KeyError) as exception:
            central.char_read(bad_uuid)
        with self.assertRaises(KeyError) as exception:
            central.char_write(bad_uuid, 0xff)

    def test_bad_value(self):
        test_uuid = 'e95d9250-251d-470a-a062-fa1922dfa9a8'
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'E9:06:4D:45:FC:8D', '')
        central = BLE_GATT.Central('E9:06:4D:45:FC:8D')
        central.connect()
        with self.assertRaises(TypeError) as exception:
            central.char_write(test_uuid, 'bad_value')
        central.disconnect()

    def test_notifications(self):
        def notify_handler(value):
            print('New value:', value)
        GATT_IFACE = 'org.bluez.GattCharacteristic1'
        test_uuid = 'e95d9250-251d-470a-a062-fa1922dfa9a8'
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'DD:02:02:02:02:02', '')
        central = BLE_GATT.Central('DD:02:02:02:02:02')
        central.connect()
        central.on_value_change(test_uuid, notify_handler)
        central.chrcs[test_uuid].Get(GATT_IFACE, 'Value')
        central.chrcs[test_uuid].Set(GATT_IFACE, 'Value',
                                     GLib.Variant('ay', [33]))
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            main_context = GLib.MainContext.default()
            while main_context.pending():
                main_context.iteration(False)
            self.assertEqual('New value: [33]\n', fake_out.getvalue())
        central.cleanup()

    def test_no_notifications(self):
        def notify_handler(value):
            print('New value:', value)

        GATT_IFACE = 'org.bluez.GattCharacteristic1'
        test_uuid = 'e95d0d2d-251d-470a-a062-fa1922dfa9a8'
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'DD:02:02:02:02:02', '')
        central = BLE_GATT.Central('DD:02:02:02:02:02')
        central.connect()
        with self.assertRaises(NotImplementedError):
            central.on_value_change(test_uuid, notify_handler)

    def test_no_notify_uuid(self):
        def notify_handler(value):
            print('New value:', value)

        GATT_IFACE = 'org.bluez.GattCharacteristic1'
        bad_uuid = '12345678-1234-1234-0123456789AB'
        self.dbusmock_bluez.AddAdapter('hci0', 'My-Test-Device')
        self.dbusmock_bluez.AddDevice('hci0', 'DD:02:02:02:02:02', '')
        central = BLE_GATT.Central('DD:02:02:02:02:02')
        central.connect()
        with self.assertRaises(KeyError):
            central.on_value_change(bad_uuid, notify_handler)
