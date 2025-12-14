# btbricks

A MicroPython Bluetooth library for controlling LEGO hubs and creating custom Bluetooth peripherals (RC controllers, MIDI devices, etc.) compatible with LEGO hubs. Implements the official LEGO Bluetooth protocol with support for Nordic UART, MIDI, and BLE Remote communication.

## Features

- 🔌 **BLE Communication**: Comprehensive Bluetooth Low Energy support via MicroPython's `ubluetooth`
- 🎮 **Hub Control**: Control LEGO MINDSTORMS hubs, SPIKE sets, and smart hubs over Bluetooth
- 📱 **Custom Peripherals**: Create RC controllers, MIDI controllers, and other BLE peripherals compatible with LEGO hubs
- 🚀 **MicroPython Ready**: Optimized for MicroPython on ESP32, LEGO SPIKE, and other platforms
- 📡 **LEGO Protocol**: Full support for LEGO Bluetooth protocols (LPF2, LPUP, CTRL+)
- 🎛️ **Multiple Interfaces**: Nordic UART, MIDI, RC control, and native LEGO hub communication
- ⚙️ **Advanced BLE**: Automatic MTU negotiation, descriptor handling, and efficient payload management

## Installation

```bash
pip install btbricks
```

## Quick Start

### Connect to a LEGO Hub

```python
from btbricks import BtHub

# Create hub instance
hub = BtHub()

# Connect to a nearby hub
hub.connect()

if hub.is_connected():
    # Set hub LED to green
    hub.set_led_color(6)  # GREEN constant
    
    # Read accelerometer data
    acc = hub.acc()
    if acc:
        print(f"Accelerometer: {acc}")
    
    # Control motor on port A with 50% power
    hub.dc("A", 50)
    
    hub.disconnect()
```

### Create an RC Receiver (Hub-side)
RCReceiver, R_STICK_HOR, R_STICK_VER

# Create RC receiver
receiver = RCReceiver(name="robot")

# Wait for transmitter connection
while not receiver.is_connected():
    pass

print("Transmitter connected!")

# Read control values in a loop
while receiver.is_connected():
    steering = receiver.get_value(R_STICK_HOR)
    throttle = receiver.get_value(R_STICK_VER)
    print(f"Steering: {steering}, Throttle: {throttle}"
receiver.on_data = on_rc_data
receiver.start()
```RCTransmitter, R_STICK_HOR, R_STICK_VER
from time import sleep

# Create transmitter
tx = RCTransmitter()

# Connect to receiver
if tx.connect(name="robot"):
    while tx.is_connected():
        # Set stick values
        tx.set_stick(R_STICK_HOR, 50)  # Steering at 50%
        tx.set_stick(R_STICK_VER, 75)  # Throttle at 75%
        
        # Send to receiver
        tx.transmit()
        sleep(0.1ransmitter = RCTransmitter(ble)

# Connect and send RC commands
transmitter.connect_and_send(b'LEGO Hub', {
    R_STICK_HOR: 50, MidiController
from time import sleep

# Create MIDI controller
midi = MidiController()

# Send MIDI note on
midi.send_note_on(60, 100)  # Middle C, velocity 100
sleep(0.5)

# Send MIDI note off

ble = BLEHandler()
midi = MidiController(ble)

# Connect to MIDI device and send note on
midi.connect_to_hub(b'LEGO Hub')
midi.send_note_on(60, 100)  # Middle C, velocity 100
midi.send_note_off(60)
```

## API Reference

See the [documentation](docs/api.rst) for detailed API reference.

### Core Classes

- `BLEHandler`: Low-level Bluetooth communication
- `UARTCentral`: Nordic UART client mode
- `UARTPeripheral`: Nordic UART server mode
- `RCReceiver`: Receive RC control signals
- `RCTransmitter`: Send RC control signals
- `MidiController`: Send MIDI commands over BLE
- `BtHub`: High-level hub communication interface

### Control Constants

- Sticks: `L_STICK_HOR`, `L_STICK_VER`, `R_STICK_HOR`, `R_STICK_VER`
- Triggers: `L_TRIGGER`, `R_TRIGGER`
- Buttons: `BUTTONS`
- Settings: `SETTING1`, `SETTING2`

## Supported Platforms

- **LEGO MINDSTORMS EV3** (with MicroPython firmware)
- **LEGO SPIKE Prime/Prime Essential** (with MINDSTORMS firmware)
- **LEGO SPIKE Robot Inventor**
- **ESP32** with MicroPython
- Other MicroPython boards with `ubluetooth` support

## Firmware Notes

SPIKE Prime requires the MINDSTORMS firmware for Bluetooth support. See [Anton's Mindstorms documentation](https://docs.antonsmindstorms.com) for detailed setup instructions.

## License

MIT License

## Author

Anton Vanhoucke