from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
from machine import Pin
import time

# Constants
BUTTON_PIN = 0  # Boot button GPIO
DEBOUNCE_TIME_MS = 200  # Debounce time in milliseconds
MULTI_PRESS_DELAY_MS = 1000  # Time window to detect multiple presses

# BLE Service and Characteristic UUIDs
_ALERT_SERVICE_UUID = bluetooth.UUID('19b10000-e8f2-537e-4f6c-d104768a1214')
_ALERT_CHAR_UUID = bluetooth.UUID('19b10001-e8f2-537e-4f6c-d104768a1214')

# Initialize button with pull-up resistor
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Global variables
press_count = 0
last_press_time = 0

# Debounce function
def debounce(pin):
    global press_count, last_press_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > DEBOUNCE_TIME_MS:
        press_count += 1
        last_press_time = current_time

# Attach interrupt to button
button.irq(trigger=Pin.IRQ_FALLING, handler=debounce)

# Register GATT server
alert_service = aioble.Service(_ALERT_SERVICE_UUID)
alert_characteristic = aioble.Characteristic(
    alert_service, _ALERT_CHAR_UUID, read=True, notify=True
)
aioble.register_services(alert_service)

# Helper to encode the alert message
def encode_alert_message(level):
    return f'Alert {level}: Emergency level {level}!'.encode('utf-8')

# Task to monitor button presses and send alerts
async def button_monitor():
    global press_count
    while True:
        if press_count > 0:
            await asyncio.sleep_ms(MULTI_PRESS_DELAY_MS)
            if press_count == 1:
                message = encode_alert_message(1)
            elif press_count == 2:
                message = encode_alert_message(2)
            elif press_count == 3:
                message = encode_alert_message(3)
            else:
                message = f'Alert {press_count}: Emergency level {press_count}!'.encode('utf-8')

            alert_characteristic.write(message, send_update=True)
            print(f'Sent: {message.decode()}')
            press_count = 0
        await asyncio.sleep_ms(100)

# Task to handle BLE connections
async def peripheral_task():
    while True:
        async with await aioble.advertise(
            100_000,
            name="ESP32_my",
            services=[_ALERT_SERVICE_UUID],
        ) as connection:
            print("Connected to", connection.device)
            await connection.disconnected()
            print("Disconnected")

# Main function to run tasks
async def main():
    monitor_task = asyncio.create_task(button_monitor())
    peripheral_task_instance = asyncio.create_task(peripheral_task())
    await asyncio.gather(monitor_task, peripheral_task_instance)

# Run the main function
asyncio.run(main())
