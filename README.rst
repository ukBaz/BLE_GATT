========
BLE GATT
========

.. image:: https://img.shields.io/pypi/l/bluezero.svg
   :target: https://github.com/ukBaz/python-bluezero/blob/master/LICENSE
   :alt: MIT License

.. image:: https://img.shields.io/pypi/v/BLE-GATT.svg
   :target: https://pypi.python.org/pypi/BLE-GATT/
   :alt: PyPI Version

.. image:: ![Test](https://github.com/ukBaz/BLE_GATT/workflows/Tests/badge.svg)
    :target: https://github.com/ukBaz/BLE_GATT/actions?query=workflow%3ATests
    :alt: Build Status



Python package for using BlueZ D-Bus API to create a device in the Central role

Goal
----

The goal of this library is to only have a small number of dependencies and
to be easily installable (even in a Python virtual environment without
`--system-site-packages`).

The commands should be installed and run by the user without `sudo`
privileges.

Install
-------

.. code-block:: bash

    $ python3 -m venv venv_ble
    $ . venv_ble/bin/activate
    $ pip3 install BLE_GATT

tl;dr
-----

Example of connecting and reading and writing without
notifications or asynchronous data

.. code-block:: python

    import BLE_GATT

    ubit_address = 'E5:10:5E:37:11:2d'
    led_text = 'e95d93ee-251d-470a-a062-fa1922dfa9A8'
    led_matrix_state = 'e95d7b77-251d-470a-a062-fa1922dfa9a8'

    ubit = BLE_GATT.Central(ubit_address)
    ubit.connect()
    ubit.char_write(led_text, b'test')
    ubit.char_write(led_matrix_state, [1, 2, 4, 8, 16])
    print(ubit.char_read(led_matrix_state))
    ubit.disconnect()

Example of connecting and interacting with characteristics asynchronously

.. code-block:: python

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


Basics of BLE
-------------

Hopefully you are here you are here with some basic knowledge of Bluetooth
and you understand that Bluetooth Classic and Bluetooth BLE are different.

There is an introduction to BLE at:

https://www.bluetooth.com/bluetooth-resources/intro-to-bluetooth-low-energy/

This library is only going to work with BLE. It will also only be a Central
device connecting to a Peripheral device.

The two key things that you will need to know about the peripheral device
you want to connect to is its address and the UUID of the GATT
characteristic you want to interact with.

Addreess
~~~~~~~~

This will be in the form of a mac address. This is 6 pairs of numbers separate
by colons. e.g. `11:22:33:44:55:66` This should be unique to each device.

UUID
~~~~

A UUID is a 128-bit value that are written in groups 0f 8-4-4-4-12. For example
00002A00-0000-1000-8000-00805F9B34FB.

Each characteristic will have a UUID that represents what it is. The number
above is for the `Device Name Characteristic`.

Writing those long numbers is cumbersome so Bluetooth official
characteristics can be shortened to 16-bits. This means you will often see
the above Device Name Characteristic written as 0x2A00 although on the system
it will still be the 128-bit value. The official Bluetooth base UUID is:
0000xxxx-0000-1000-8000-00805F9B34FB and the 16-bit value replaces the x's.

One-time provisioning of peripheral device
------------------------------------------

A BLE peripheral device will be advertising some summary information, such
as what services it offers, and our Central device needs to have read this
advertisement before it can connect. Some devices will also need to exchange
security information before they can connect and exchange information
securely.

This security information exchange is called pairing or bonding. As this
is a one-time provisioning step this library does not do the discovery or
pairing step. Those can be done with the Linux `bluetoothctl` tool.



To launch the tool::

    $ bluetoothctl

To start and stop the discovery of nearby advertising peripherals::

    [bluetooth]# scan on
    [bluetooth]# scan off

Discovered devices will scroll up the screen. Once you stop discovery, to
get a list of devices use::

    [bluetooth]# devices

If you need to pair with the peripheral then the commands are::

    [bluetooth]# agent KeyboardDisplay
    [bluetooth]# pair 11:22:33:44:55:66

If you don't need to pair, then doing a connect will save the device
in the Bluetooth information on the machine::

    [bluetooth]# connect 11:22:33:44:55:66
    [Name Of Device]# disconnect


Getting Started
---------------

Now you have the peripheral device address, UUID's of interest, and have done
the provisioning of the device we are ready to do some coding.

Create a device object
~~~~~~~~~~~~~~~~~~~~~~

Import the library to you code and tell it about the address of the
peripheral device to connect to.

.. code-block:: python

    import BLE_GATT
    my_device = BLE_GATT.Central('11:22:33:44:55:66')

Connect and disconnect
~~~~~~~~~~~~~~~~~~~~~~

Establish (or remove) a Bluetooth connection between the Linux computer your
code runs on and the peripheral device.

.. code-block:: python

    my_device.connect()
    my_device.disconnect()

Exchange Information
~~~~~~~~~~~~~~~~~~~~

The API uses the structure of the command name is the activity you want
to perform on the characteristic. The first parameter is the UUID of the
characteristic you want to perform that on. To save us keep writing the long
UUID, it is a good idea to create a constant/variable with the UUID value

Bluetooth data is always an array of unsigned bytes. We can represent
that in Python as a list of values between 0 and 255. Numbers that
are bigger than 255 will take multiple bytes. We can connect these
together in Python with  int.from_bytes or struct.unpack.

To create the values to write we can use int.to_bytes or stuct.pack

Expect Bluetooth data to be in little endian format.

.. code-block:: python

    my_custom_uuid = '12345678-1234-1234-1234-123456789ABC'
    value = my_device.char_read(my_custom_uuid)
    my_device.char_write(my_custom_uuid, [255, 255, 0, 123])

Asynchronous Data
~~~~~~~~~~~~~~~~~

As well as reading and writing data, it is also possible get
notifications from a Bluetooth peripheral when the value of a
characteristic has changed. This is very efficient on Bluetooth
traffic and also the battery of the peripheral as it can turn the
radio off when there isn't new data. For programming the client it
means we don't know when there is going to be data to handle. This
requires us to code using asynchronous technique.

We do this be using the `on_value_change` command for the GATT
characteristic UUID of interest. We give it a function that will get
called when the value changes. We also need to use
`wait_for_notifications` to stop the code exiting. This runs an
event loop listening for updates.

.. code-block:: python

    def my_callback(value):
        print(value)
    on_value_change(my_custom_uuid, my_callback)
    wait_for_notifications())

If you want to stop getting notifications from a GATT characteristic
UUID then there is:

.. code-block:: python

    remove_notify(my_custom_uuid)

There is also a command that will remove all notifications, exit the
event loop, and disconnect from the peripheral device.

.. code-block:: python

    cleanup()

Bytes and Values
----------------

With Bluetooth values will always be in bytes which isn't very readable to
humans so most of the time we will want to covert them to an integer or
floating point number.

Let's use an example from GATT Specification Supplement at
https://www.bluetooth.com/specifications/specs/

We will use Electric Current Specification (0x2AF0) which has three fields
within the characteristic each two bytes (octets) in size. Those three fields
are minimum, typical and maximum electric current. With current being defined
as:

+------------------+-----------------------------------------------------+
| Field            | Current                                             |
+------------------+-----------------------------------------------------+
| Data Type        | uint16  (Represents a 16-bit unsigned integer)      |
+------------------+-----------------------------------------------------+
| Size (in octets) | 2                                                   |
+------------------+-----------------------------------------------------+
| Description      | - Unit: org.bluetooth.unit.electric_current.ampere  |
|                  | - Minimum value: 0                                  |
|                  | - Maximum value: 655.34                             |
|                  | - Represented values: M = 1, d = -2, b = 0          |
|                  | - Unit is degrees with a resolution of 0.01         |
+------------------+-----------------------------------------------------+

The represented value information helps us convert an integer to a floating
point number:

 * M = multiplier, positive or negative integer (between -10 and +10)
 * d = decimal exponent, positive or negative integer
 * b = binary exponent, positive or negative integer

From bytes
~~~~~~~~~~

If we had three values of `12.34, 23.45, 34.56` they would arrive as
`[210, 4, 41, 9, 128, 13]`. Let's see how we could covert them using
firstly `struct`.

.. code-block:: python

    >>> value = [210, 4, 41, 9, 128, 13]
    >>> import struct
    >>> struct.unpack('<HHH', bytes(value))
    (1234, 2345, 3456)
    >>> [value * (10 ** -2) for value in struct.unpack('<HHH', bytes(value))]
    [12.34, 23.45, 34.56]

And doing the same using `int.from_bytes`

.. code-block:: python

    >>> int.from_bytes(value[0:2], byteorder='little', signed=False)
    1234
    >>> int.from_bytes(value[0:2], byteorder='little', signed=False) * (10 ** -2)
    12.34
    >>> int.from_bytes(value[2:4], byteorder='little', signed=False) * (10 ** -2)
    23.45
    >>> int.from_bytes(value[4:6], byteorder='little', signed=False) * (10 ** -2)
    34.56

To Bytes
~~~~~~~~

If we were sending this data then it needs to go from being floating point
numbers to a list of bytes.

Using `struct`

.. code-block:: python

    >>> c_min = 12.34
    >>> c_typ = 23.45
    >>> c_max = 34.56
    >>> expo = 10 ** 2
    >>> list(struct.pack('<HHH', int(c_min * expo),
                                 int(c_typ * expo),
                                 int(c_max * expo)))
    [210, 4, 41, 9, 128, 13]

Using int.to_bytes

.. code-block:: python

    >>> list(b''.join((int(c_min * expo).to_bytes(2, byteorder='little', signed=False),
    ...                int(c_typ * expo).to_bytes(2, byteorder='little', signed=False),
    ....               int(c_max * expo).to_bytes(2, byteorder='little', signed=False))))
    [210, 4, 41, 9, 128, 13]

Advanced Information
--------------------

The BlueZ D-Bus API's used in making this library is documented at:

 - https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/adapter-api.txt
 - https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/device-api.txt
 - https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/gatt-api.txt

You can get help on accessing those full APIs with the following commands:

.. code-block:: python

    import BLE_GATT
    my_device = BLE_GATT.Central('11:22:33:44:55:66')
    my_custom_uuid = '12345678-1234-1234-1234-123456789ABC'
    help(my_device.adapter)
    help(my_device.device)
    help(my_device.chrcs[my_custom_uuid.casefold()])
