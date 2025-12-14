# BLEHandler Improvement Suggestions

## Executive Summary

The `BLEHandler` class is a monolithic, low-level wrapper around MicroPython's `ubluetooth` module. While functional, it has several opportunities for:
1. **Simplification** - Reduce coupling and complexity
2. **Better developer clarity** - Clearer code flow and responsibility separation
3. **Better separation of concerns** - Separate discovery, connection, and communication logic

---

## Current Architecture Issues

### 1. ❌ Monolithic Design
**Problem:** Single `BLEHandler` class handles:
- Raw BLE event handling (IRQ)
- Connection state management
- UART-specific connection logic
- LEGO hub-specific connection logic
- MIDI service registration
- Generic scanning and callback management
- Debug logging

**Impact:** Hard to understand what's being done where. Tight coupling makes testing and maintenance difficult.

**Lines of code:** ~350 lines in a single class

---

### 2. ❌ State Machine Complexity
**Problem:** Multiple boolean flags manage connection state:
```python
self.connecting_uart = False
self.connecting_lego = False
self._connected_central = -1
self._search_name = None
self._addr_type = None
self._addr = None
# ... 15+ more state variables
```

**Impact:** Hard to trace state transitions. Easy to introduce bugs when adding new protocols.

---

### 3. ❌ Callback Proliferation
**Problem:** Multiple callback dictionaries with unclear lifecycle:
```python
self._write_done_callbacks = {}
self._disconn_callbacks = {}
self._notify_callbacks = {}
self._write_callbacks = {}
self._char_result_callback = None
self._scan_result_callback = None
self._scan_done_callback = None
# ...
```

**Impact:** Callbacks can leak memory. Hard to trace which callbacks belong to which connection.

---

### 4. ❌ TODO Comments Indicate Incomplete Refactoring
```python
# TODO: Create a generic connecting function that encodes the searched-for advertising data
# self._search_payload = _advertising_payload(name=name, services=[_UART_UUID])
```

The code was intended to be DRY but wasn't refactored.

---

## Recommended Improvements

### Improvement #1: Extract Connection Managers

**Create separate connection handler classes:**

```
BLEHandler (core communication)
├── DiscoveryManager (scan, find devices)
├── UARTConnectionManager (UART-specific connection)
├── LEGOConnectionManager (LEGO-specific connection)
└── CallbackRegistry (centralized callback management)
```

**Benefits:**
- Each class has single responsibility
- Easier to test independently
- Clear protocol-specific logic
- Easier to add new protocols

**Example structure:**
```python
class DiscoveryManager:
    """Handles BLE device discovery and scanning."""
    def __init__(self, ble_handler):
        self.ble_handler = ble_handler
    
    def scan_for(self, criteria):
        """Scan for devices matching criteria."""
    
    def on_result(self, addr_type, addr, name, services):
        """Handle scan result."""

class UARTConnectionManager:
    """Handles UART-specific connection setup."""
    def __init__(self, ble_handler, discovery_manager):
        self.ble_handler = ble_handler
        self.discovery = discovery_manager
    
    def connect(self, name, timeout):
        """Connect to UART peripheral."""
    
    def _on_service_found(self, start_handle, end_handle):
        """Handle UART service discovery."""
```

---

### Improvement #2: State Machine Pattern

**Replace boolean flags with explicit state:**

```python
from enum import IntEnum

class ConnectionState(IntEnum):
    IDLE = 0
    SCANNING = 1
    CONNECTING = 2
    CONNECTED = 3
    DISCONNECTING = 4

class ConnectionContext:
    """Encapsulates connection state for a specific protocol."""
    def __init__(self, protocol_type):
        self.protocol = protocol_type
        self.state = ConnectionState.IDLE
        self.conn_handle = None
        self.addr_type = None
        self.addr = None
        self.start_handle = None
        self.end_handle = None
        self.characteristics = {}  # {uuid: value_handle}
        self.callbacks = {}
        
    def __str__(self):
        return f"{self.protocol.name}({self.state.name})"
```

**Benefits:**
- Explicit state transitions
- Easier to debug (log state changes)
- Single source of truth for connection state
- Prevents invalid state combinations

---

### Improvement #3: Centralized Callback Management

**Create a callback registry:**

```python
class CallbackRegistry:
    """Manages BLE callbacks with automatic cleanup."""
    
    def __init__(self):
        self._callbacks = {}  # {(conn_handle, event_type): callback}
    
    def register(self, conn_handle, event_type, callback):
        """Register callback for connection + event."""
        key = (conn_handle, event_type)
        if key in self._callbacks and self._callbacks[key]:
            print(f"Warning: Overwriting existing {event_type} callback")
        self._callbacks[key] = callback
    
    def trigger(self, conn_handle, event_type, *args):
        """Trigger callback if registered."""
        key = (conn_handle, event_type)
        if key in self._callbacks and self._callbacks[key]:
            self._callbacks[key](*args)
    
    def cleanup(self, conn_handle):
        """Remove all callbacks for a connection."""
        to_remove = [k for k in self._callbacks if k[0] == conn_handle]
        for k in to_remove:
            del self._callbacks[k]
```

**Benefits:**
- Single place to manage callbacks
- Automatic cleanup on disconnect
- No memory leaks from dangling callbacks
- Clear callback lifecycle

---

### Improvement #4: Extract Advertising Utilities

**Move advertising logic to separate module:**

```python
# bt_advertising.py
class AdvertisingPayload:
    """Builder for BLE advertising payloads."""
    def __init__(self):
        self.payload = bytearray()
    
    def add_flags(self, limited_disc=False, br_edr=False):
        """Add flags to payload."""
    
    def add_name(self, name):
        """Add device name to payload."""
    
    def add_services(self, *uuids):
        """Add service UUIDs to payload."""
    
    def add_appearance(self, code):
        """Add appearance descriptor."""
    
    def build(self):
        """Return final payload."""
        return bytes(self.payload)

# Usage:
payload = AdvertisingPayload()
payload.add_name("my-device")
payload.add_services(_UART_UUID)
payload.add_flags()
ble.gap_advertise(100000, adv_data=payload.build())
```

**Benefits:**
- Clearer intent
- Easier to build payloads
- Composable and reusable
- Better testability

---

### Improvement #5: Split IRQ Handler

**Current:** Single 300-line `_irq()` method handles all events

**Proposal:** Route events to protocol-specific handlers

```python
def _irq(self, event, data):
    """Route events to appropriate handlers."""
    
    if event in (
        _IRQ_PERIPHERAL_CONNECT,
        _IRQ_PERIPHERAL_DISCONNECT,
        _IRQ_GATTC_SERVICE_RESULT,
        _IRQ_GATTC_CHARACTERISTIC_RESULT,
    ):
        self._handle_gattc_event(event, data)
    
    elif event in (_IRQ_CENTRAL_CONNECT, _IRQ_CENTRAL_DISCONNECT, _IRQ_GATTS_WRITE):
        self._handle_gatts_event(event, data)
    
    elif event in (_IRQ_SCAN_RESULT, _IRQ_SCAN_DONE):
        self._discovery_manager.handle_event(event, data)
    
    else:
        self._handle_generic_event(event, data)

def _handle_gattc_event(self, event, data):
    """Handle client-side GATT events."""
    # Process GATTC events
    
def _handle_gatts_event(self, event, data):
    """Handle server-side GATT events."""
    # Process GATTS events
```

**Benefits:**
- `_irq()` method becomes readable
- Event handling logic is logically grouped
- Easier to understand flow
- Easier to maintain each event type

---

### Improvement #6: Clearer Documentation

**Add these docstring sections:**

```python
class BLEHandler:
    """
    Bluetooth Low Energy communication handler.
    
    Acts as both BLE central (client) and peripheral (server).
    
    RESPONSIBILITIES:
    - Low-level BLE communication
    - Event dispatching
    - MTU negotiation
    - Callback management
    
    ARCHITECTURE:
    - ConnectionContext: Encapsulates state for each protocol type
    - DiscoveryManager: Handles device scanning
    - Protocol managers: UART, LEGO, MIDI (separate classes)
    
    CALLBACKS:
    Event callbacks are managed through CallbackRegistry.
    Callbacks are automatically cleaned up on disconnect.
    
    EXAMPLE:
        handler = BLEHandler()
        uart_conn = handler.connect_uart("robot")
        handler.on_notify(uart_conn.handle, my_callback)
    
    NOTE: Only one central connection per handler.
          Multiple peripherals supported via separate handlers.
    """
```

---

## Implementation Roadmap

### Phase 1: Non-Breaking Refactoring (Current API stays same)
1. Extract `DiscoveryManager` (internal use only)
2. Extract `CallbackRegistry` (internal use only)
3. Create `ConnectionContext` (internal state)
4. Split `_irq()` into event type handlers

**Impact:** No API changes, easier to maintain

### Phase 2: Improved API (Backward compatible)
5. Create `UARTConnectionManager` class
6. Add new `connect_uart_v2()` using manager
7. Keep old `connect_uart()` for compatibility

**Impact:** New code can use cleaner API

### Phase 3: Major Refactoring (Next major version)
8. Deprecate old connection methods
9. Make protocol managers public API
10. Simplify core `BLEHandler` class

**Impact:** Cleaner API, better maintainability

---

## Code Quality Metrics

### Current State
- BLEHandler: ~350 lines
- Methods: 15+
- State variables: 20+
- Callbacks: 7 different types
- Cyclomatic complexity: Very high

### After Improvements
- BLEHandler: ~150 lines (core only)
- DiscoveryManager: ~80 lines
- UARTConnectionManager: ~70 lines
- CallbackRegistry: ~50 lines
- Methods per class: 5-7 (single responsibility)
- State variables per class: 3-5
- Cyclomatic complexity: Low per module

---

## Testing Benefits

**Current challenges:**
- Hard to mock ubluetooth
- Hard to test connection logic independently
- Hard to test callback behavior

**After refactoring:**
```python
# Easy to test managers independently
def test_uart_connection_manager():
    mock_handler = Mock()
    manager = UARTConnectionManager(mock_handler)
    manager.connect("test-device")
    # Assert discovery called
    # Assert connection initiated

# Easy to test callbacks
def test_callback_cleanup():
    registry = CallbackRegistry()
    registry.register(1, "notify", mock_callback)
    registry.cleanup(1)
    registry.trigger(1, "notify", b"data")  # Should not call callback
```

---

## Migration Path for Users

**No breaking changes needed for:**
- `UARTPeripheral`, `UARTCentral` (no changes)
- `RCReceiver`, `RCTransmitter` (no changes)
- `MidiController` (no changes)

**New imports available:**
```python
# Old way (still works)
from btbricks import RCTransmitter

# New way (after Phase 2)
from btbricks import RCTransmitter, UARTConnectionManager
```

---

## Summary

| Aspect | Current | After Refactoring |
|--------|---------|-------------------|
| **Main class LOC** | 350 | 150 |
| **Number of classes** | 1 (BLEHandler) | 5+ (split responsibilities) |
| **State management** | Boolean flags | State machine + context |
| **Callback safety** | Manual cleanup | Automatic + registry |
| **Testability** | Low | High |
| **New protocol support** | Hard | Easy (template manager) |
| **Documentation clarity** | Low | High |
| **Contributing difficulty** | Hard | Easy |

---

## Recommendations

**Start with Phase 1 immediately:**
- Extract `DiscoveryManager` and `CallbackRegistry`
- Split `_irq()` handler
- No API changes = safe refactoring

**Then consider Phase 2 for v0.2:**
- Create `UARTConnectionManager` and similar
- Deprecate old connection methods
- Provide new cleaner API

**Phase 3 for v1.0:**
- Remove deprecated methods
- Make managers public
- Major API cleanup

This approach allows gradual improvement without breaking user code.
