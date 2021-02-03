"""Bluetooth BLE peripheral communications"""
from time import sleep
from collections import namedtuple
from pydbus import SystemBus
from gi.repository import GLib

BLUEZ_SERVICE = 'org.bluez'
BLUEZ_DEV_IFACE = 'org.bluez.Device1'
BLUEZ_CHR_IFACE = 'org.bluez.GattCharacteristic1'

PropChangedHandler = namedtuple('PropChangedHandler', ('user_handler',
                                                       'subscription'))


class Central:
    """
    Create a device in a central role and communicate with a peripheral device
    """
    def __init__(self, address):
        self.bus = SystemBus()
        self.mngr = self.bus.get(BLUEZ_SERVICE, '/')
        self._device_path = self._from_device_address(address)
        if self._device_path is None:
            raise KeyError(f'Device address [{address}] is not found.'
                           f'Use bluetoothctl to find what devices are nearby')
        self._adapter_path = '/'.join(self._device_path.split('/')[:-1])
        self.adapter = self.bus.get(BLUEZ_SERVICE,
                                    self._adapter_path)['org.bluez.Adapter1']
        self.device = self.bus.get(BLUEZ_SERVICE, self._device_path)
        self.chrcs = {}
        self._handlers = {}
        self.mainloop = GLib.MainLoop()

    def _from_device_address(self, addr):
        """Look up Device D-Bus object path from device address"""
        mng_objs = self.mngr.GetManagedObjects()
        for path in mng_objs:
            dev_addr = mng_objs[path].get(BLUEZ_DEV_IFACE,
                                          {}).get('Address', '')
            if addr.casefold() == dev_addr.casefold():
                return path
        return None

    def _get_device_chars(self):
        """Find all GATT characteristics for device. Store for look-up later"""
        mng_objs = self.mngr.GetManagedObjects()
        for path in mng_objs:
            chr_uuid = mng_objs[path].get(BLUEZ_CHR_IFACE, {}).get('UUID')
            if path.startswith(self._device_path) and chr_uuid:
                self.chrcs[chr_uuid] = self.bus.get(BLUEZ_SERVICE, path)

    def _get_uuid(self, path):
        """Get the Characteristics UUID from its D-Bus object path"""
        mng_objs = self.mngr.GetManagedObjects()
        return mng_objs[path].get(BLUEZ_CHR_IFACE, {}).get('UUID')

    def connect(self):
        """
        Connect to device.
        Wait for GATT services to be resolved before returning
        """
        self.device.Connect()
        while not self.device.ServicesResolved:
            sleep(0.5)
        self._get_device_chars()

    def disconnect(self):
        """Disconnect from device"""
        self.device.Disconnect()

    def char_write(self, uuid, value):
        """Write value to given GATT characteristic UUID"""
        if uuid.casefold() in self.chrcs:
            self.chrcs[uuid.casefold()].WriteValue(value, {})
        else:
            raise KeyError(f'UUID {uuid} not found')

    def char_read(self, uuid):
        """Read value of given GATT characteristic UUID"""
        if uuid.casefold() in self.chrcs:
            return self.chrcs[uuid.casefold()].ReadValue({})
        raise KeyError(f'UUID {uuid} not found')

    def _chrc_value_update(self, bus_name, path, signal_iface,
                           signal_name, notification):
        """
        Only send notifications to a users event handler when it is a
        GATT characteristics value that has changed
        """
        uuid = self._get_uuid(path)
        iface, props_changed, props_removed = notification
        if iface == BLUEZ_CHR_IFACE and 'Value' in props_changed:
            self._handlers[uuid.casefold()].user_handler(
                props_changed['Value'])

    def on_value_change(self, uuid, handler):
        """
        A function reference which will be called when a property
        value is changed for given GATT characteristic UUID if notifications
        are available
        """
        uuid = uuid.casefold()
        if uuid in self.chrcs:
            if all(('notify' not in self.chrcs[uuid].Flags,
                    'indicate' not in self.chrcs[uuid].Flags)):
                raise NotImplementedError(
                    f'Notifications are not implemented on {uuid}'
                )
            subs = self.bus.subscribe(
                iface='org.freedesktop.DBus.Properties',
                signal='PropertiesChanged',
                object=self.chrcs[uuid]._path,
                signal_fired=self._chrc_value_update)
            self._handlers[uuid] = PropChangedHandler(handler, subs)
            self.chrcs[uuid].StartNotify()
        else:
            raise KeyError(f'UUID {uuid} not found')

    def remove_notify(self, uuid):
        """Stop notifications for given GATT characteristic UUID"""
        uuid = uuid.casefold()
        if uuid in self.chrcs and uuid in self._handlers:
            self.chrcs[uuid.casefold()].StopNotify()
            self._handlers[uuid.casefold()].subscription.disconnect()
            del self._handlers[uuid]

    def wait_for_notifications(self):
        """
        Has the effect of block the code from exiting. In the background it
        starts an event loop to listen for updates from the device
        """
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            self.cleanup()

    def cleanup(self):
        """
        If you have the used `wait_for_notifications`, then this command
        will remove that blocking. This will stop the event loop, remove
        all notification subscriptions, disconnect from the peripheral device.
        """
        self.mainloop.quit()
        all_uuids = list(self._handlers.keys())
        for uuid in all_uuids:
            self.remove_notify(uuid)
        self.disconnect()
