"""
Example of connecting and getting notifications of value
changes of characteristics
"""
import BLE_GATT

ubit_address = 'E5:10:5E:37:11:2d'
led_text = 'e95d93ee-251d-470a-a062-fa1922dfa9A8'
led_matrix_state = 'e95d7b77-251d-470a-a062-fa1922dfa9a8'
btn_a = 'E95DDA90-251D-470A-A062-FA1922DFA9A8'
btn_b = 'E95DDA91-251D-470A-A062-FA1922DFA9A8'


def btn_common(value, btn_id):
    btn_value = int.from_bytes(value, byteorder='little')
    if btn_value == 1:
        print(f'{btn_id} pressed')
    elif btn_value == 2:
        print(f'{btn_id} is held.')
        if btn_id == 'B':
            print('Bye, bye!')
            ubit.cleanup()
    else:
        print(f'{btn_id} released')


def btn_a_handler(value):
    btn_common(value, 'A')


def btn_b_handler(value):
    btn_common(value, 'B')


ubit = BLE_GATT.Central(ubit_address)
ubit.connect()
ubit.on_value_change(btn_a, btn_a_handler)
ubit.on_value_change(btn_b, btn_b_handler)
ubit.wait_for_notifications()
