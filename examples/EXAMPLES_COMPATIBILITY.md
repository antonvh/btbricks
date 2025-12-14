# Examples Compatibility Report

## Summary

**Status:** ⚠️ Most examples need updates

All examples in the `examples/` directory are currently incompatible with the `btbricks` package as distributed. They import from `projects.mpy_robot_tools` (a different package) rather than from `btbricks`.

## Issues Found

### 1. Incorrect Import Paths (All files)
**Problem:** Examples import from `projects.mpy_robot_tools.*`
```python
# WRONG - not available in btbricks
from projects.mpy_robot_tools.bt import RCTransmitter
from projects.mpy_robot_tools.rc import RCReceiver
```

**Should be:**
```python
# CORRECT - from btbricks package
from btbricks import RCTransmitter, RCReceiver
```

### 2. Missing Classes/Functions
Some examples reference functionality not in `btbricks`:
- `CHORD_STYLES` (in `inventor_ble_midi_guitar.py`, `ble-midi-esp/main.py`)
- `note_parser()` (in `ble-midi-esp/main.py`)
- Direct motor control APIs from MINDSTORMS (not in btbricks)
- `mpy_robot_tools.helpers.PBMotor`

### 3. MicroPython-Specific Modules
Examples use LEGO MINDSTORMS-specific imports:
```python
from hub import sound, port
from mindstorms import ColorSensor, DistanceSensor, Motor, MSHub
```

These are specific to LEGO firmware and won't work with generic btbricks on ESP32.

## Files Needing Updates

### High Priority (Basic Bluetooth functionality)
- ✏️ `ble_uart_simple_central.py` — UARTCentral example
- ✏️ `ble_uart_simple_peripheral.py` — UARTPeripheral example
- ✏️ `rc_hotrod_transmitter.py` — RCTransmitter example
- ✏️ `rc_hotrod_car_receiver.py` — RCReceiver example

### Medium Priority (MIDI examples - missing CHORD_STYLES)
- ✏️ `inventor_ble_midi_guitar.py`
- ✏️ `ble-midi-esp/main.py`

### Low Priority (Complex motor sync - tightly coupled to MINDSTORMS)
- ✏️ `rc_snake.py`
- ✏️ `rc_multi_snake_*.py`
- ✏️ `rc_extreme_offroader_spike_wheel.py`
- ✏️ `rc_mecanum_wheels.py`
- ✏️ `rc_snake_with_*.py`
- ✏️ `ble_uart_light_matrix_*.py` — Uses SPIKE Prime specific APIs

## Recommendations

1. **Create corrected examples** using proper `btbricks` imports
2. **Separate examples by platform:**
   - Generic ESP32 examples (basic UART, RC, MIDI)
   - SPIKE Prime/MINDSTORMS examples (with hub APIs)
3. **Add docstrings** explaining hardware requirements and expected connections
4. **Test examples** before distribution

## Next Steps

To fix examples, you should:
1. Update import statements to use `from btbricks import ...`
2. Remove MINDSTORMS-specific APIs (hub, motor controls)
3. Focus on Bluetooth communication examples that work on any MicroPython device
4. Add comments about what devices/hubs to connect to
