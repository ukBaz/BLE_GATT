"""
Example of connecting and getting notifications of value
changes of characteristics
"""
import BLE_GATT
from gi.repository import GLib

ubit_address = 'E9:06:4D:45:FC:8D'
uart_rx = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
uart_tx = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'


def notify_handler(value):
    print(f"Received: {bytes(value).decode('UTF-8')}")


def send_ping():
    print('sending: ping')
    ubit.char_write(uart_rx, b'ping\n')
    return True


ubit = BLE_GATT.Central(ubit_address)
ubit.connect()
ubit.on_value_change(uart_tx, notify_handler)
GLib.timeout_add_seconds(20, send_ping)
ubit.wait_for_notifications()
