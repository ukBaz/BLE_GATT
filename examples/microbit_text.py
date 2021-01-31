"""
Example of connecting and reading and writing without
notifications or asynchronous data
"""
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
