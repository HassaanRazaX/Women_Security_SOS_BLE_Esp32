import bluetooth
from ble_advertising import advertising_payload
from machine import Pin
from micropython import const
import time

# Constants for BLE
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)

# Button setup
BUTTON_PIN = 0  # Assuming the boot button is on GPIO 0
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# BLE device name
DEVICE_NAME = "EmergencyNecklace"

class BLEUART:
    def __init__(self, ble, name=DEVICE_NAME, rxbuf=100):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()
        self._rx_buffer = bytearray()
        self._handler = None
        self._payload = advertising_payload(name=name, appearance=_ADV_APPEARANCE_GENERIC_COMPUTER)
        self._advertise()

    def irq(self, handler):
        self._handler = handler

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("BLE Connected")
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            print("BLE Disconnected")
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle in self._connections and value_handle == self._rx_handle:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)
                if self._handler:
                    self._handler()

    def any(self):
        return len(self._rx_buffer)

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)
        result = self._rx_buffer[0:sz]
        self._rx_buffer = self._rx_buffer[sz:]
        return result

    def write(self, data):
        if not self._connections:
            print("No BLE connection. Cannot send message.")
            return
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()

    def _advertise(self, interval_us=500000):
        print("Advertising BLE service...")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)


def send_alert(uart, alert_number):
    alerts = ["alert1", "alert2", "alert3"]
    if 1 <= alert_number <= len(alerts):
        message = alerts[alert_number - 1]
        uart.write(message + "\n")
        print(f"Sent: {message}")
    else:
        print("Invalid alert number")


def setup_ble():
    ble = bluetooth.BLE()
    if not ble.active():
        print("Activating BLE...")
        ble.active(True)
    return BLEUART(ble)


def handle_button_press(uart):
    last_button_state = button.value()
    press_count = 0
    last_press_time = time.ticks_ms()

    while True:
        current_button_state = button.value()
        if current_button_state != last_button_state:
            if current_button_state == 0:  # Button pressed
                press_count += 1
                last_press_time = time.ticks_ms()
                print(f"Button pressed {press_count} time(s)")
            last_button_state = current_button_state

        # If no further presses within 1 second, send the alert
        if time.ticks_diff(time.ticks_ms(), last_press_time) > 1000 and press_count > 0:
            send_alert(uart, press_count)
            press_count = 0

        time.sleep_ms(100)


def main():
    print("Starting Emergency Necklace BLE Service...")
    uart = setup_ble()

    try:
        handle_button_press(uart)
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        uart.close()
        print("BLE resources released.")


if __name__ == "__main__":
    main()
