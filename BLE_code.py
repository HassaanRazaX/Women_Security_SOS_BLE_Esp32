from machine import Pin, Timer
from time import sleep_ms
import ubluetooth

class ESP32_BLE:
    def __init__(self, name):
        self.led = Pin(2, Pin.OUT)
        self.timer1 = Timer(0)
        self.name = name
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.connected = False
        self.ble.irq(self.ble_irq)
        self.register()
        self.advertise()

    def ble_irq(self, event, data):
        if event == 1:  # Central device connected
            self.connected = True
            self.led.value(1)
            self.timer1.deinit()
        elif event == 2:  # Central device disconnected
            self.connected = False
            self.advertise()
            self.timer1.init(period=500, mode=Timer.PERIODIC, callback=lambda t: self.led.value(not self.led.value()))

    def register(self):
        NUS_UUID = ubluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
        RX_UUID = (ubluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), ubluetooth.FLAG_WRITE)
        TX_UUID = (ubluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), ubluetooth.FLAG_NOTIFY)
        BLE_UART = (NUS_UUID, (TX_UUID, RX_UUID))
        ((self.tx, self.rx),) = self.ble.gatts_register_services((BLE_UART,))

    def send(self, data):
        if self.connected:
            self.ble.gatts_notify(0, self.tx, data + '\n')
        else:
            print("No BLE device connected.")

    def advertise(self):
        name = bytes(self.name, 'UTF-8')
        adv_data = b'\x02\x01\x02' + bytes([len(name) + 1, 0x09]) + name
        self.ble.gap_advertise(100, adv_data)
        print("Advertising as:", self.name)

# Button handling
debounce_time = 300  # milliseconds
press_count = 0
last_press_time = 0

def button_irq(pin):
    global press_count, last_press_time
    current_time = int(time.ticks_ms())
    if current_time - last_press_time > debounce_time:
        press_count += 1
        last_press_time = current_time
        print(f"Button pressed {press_count} time(s)")
    
    # Timer to detect when presses are done
    Timer(1).init(mode=Timer.ONE_SHOT, period=700, callback=send_alert)

def send_alert(timer):
    global press_count
    if press_count == 1:
        ble.send("alert1")
    elif press_count == 2:
        ble.send("alert2")
    elif press_count == 3:
        ble.send("alert3")
    else:
        print("Invalid press count")
    press_count = 0  # Reset the counter after sending alert

# Initialize BLE
ble = ESP32_BLE("ESP32_SOS")

# Button setup
button = Pin(0, Pin.IN, Pin.PULL_UP)
button.irq(trigger=Pin.IRQ_FALLING, handler=button_irq)

while True:
    sleep_ms(100)
