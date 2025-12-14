# BLEHandler Refactoring - Visual Architecture Guide

## Current Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      BLEHandler                         │
│  (350 lines, everything mixed together)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Responsibilities:                                       │
│  ✗ Raw BLE event handling (_irq)                        │
│  ✗ Connection state management (20+ variables)          │
│  ✗ UART discovery & connection                          │
│  ✗ LEGO discovery & connection                          │
│  ✗ MIDI service registration                            │
│  ✗ Generic scanning                                      │
│  ✗ Callback management (7 different callback types)     │
│  ✗ Debug logging                                         │
│  ✗ MTU negotiation                                       │
│                                                          │
│  Callbacks (scattered, no lifecycle management):        │
│  └─ _scan_result_callback                               │
│  └─ _scan_done_callback                                 │
│  └─ _write_done_callbacks{}                             │
│  └─ _disconn_callbacks{}                                │
│  └─ _notify_callbacks{}                                 │
│  └─ _write_callbacks{}                                  │
│  └─ _char_result_callback                               │
│                                                          │
│  State (20+ variables, no single truth):                │
│  └─ _connected_central, _search_name, _addr_type,       │
│     _addr, _conn_handle, _start_handle, _end_handle,    │
│     _rx_handle, _tx_handle, _lego_value_handle,         │
│     connecting_uart, connecting_lego, ...               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Proposed Architecture - Phase 1

```
┌──────────────────────────────────────────────────────────────┐
│                       BLEHandler                             │
│              (Core communication ~150 lines)                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Responsibilities (ONLY):                               │ │
│  │  • Raw ubluetooth wrapper                               │ │
│  │  • IRQ routing to handlers                              │ │
│  │  • MTU negotiation                                       │ │
│  │  • Debug logging                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                         ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ Routes to specialized event handlers:                   ││
│  │  _handle_scan_event()                                   ││
│  │  _handle_gattc_event()                                  ││
│  │  _handle_gatts_event()                                  ││
│  └──────────────────────────────────────────────────────────┘│
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│  DiscoveryManager        │ (Extract Phase 1)
├──────────────────────────┤
│ Responsibilities:        │
│ • Scan for devices       │
│ • Match criteria         │
│ • Track results          │
└──────────────────────────┘

┌──────────────────────────┐
│  CallbackRegistry        │ (Extract Phase 1)
├──────────────────────────┤
│ Responsibilities:        │
│ • Store callbacks        │
│ • Trigger callbacks      │
│ • Cleanup on disconnect  │
└──────────────────────────┘

┌──────────────────────────┐
│  ConnectionContext       │ (Extract Phase 1)
├──────────────────────────┤
│ Attributes:              │
│ • state (enum)           │
│ • conn_handle            │
│ • characteristics{}      │
│ • callbacks{}            │
└──────────────────────────┘
```

---

## Proposed Architecture - Phase 2 (Backward Compatible)

```
                    BLEHandler
                        │
         ┌──────────────┼──────────────┐
         ↓              ↓              ↓
    DiscoveryMgr  CallbackRegistry  [other utilities]
         │
         ├─ UARTConnectionManager (NEW - Phase 2)
         │
         ├─ LEGOConnectionManager (NEW - Phase 2)
         │
         └─ MidiServiceManager (NEW - Phase 2)


Old API (still works):
    handler.connect_uart("robot")          ← Uses UARTConnectionManager internally
    
New API (cleaner):
    uart_mgr = UARTConnectionManager(handler)
    ctx = uart_mgr.connect("robot")        ← Returns ConnectionContext
    handler.on_notify(ctx.handle, callback)
```

---

## Event Flow - Before vs After

### BEFORE (Monolithic)

```
ubluetooth event
        ↓
    _irq() [300 lines]
        ├─ Parse event
        ├─ Check 20+ state variables
        ├─ Update state
        ├─ Call scattered callbacks
        ├─ Manage 7 different callback types
        ├─ Handle UART logic
        ├─ Handle LEGO logic
        └─ Log to debug buffer
```

### AFTER (Layered)

```
ubluetooth event
        ↓
    _irq() [50 lines]
        ├─ Dispatch to handler
        └─ Handlers process independently
               ├─ _handle_scan_event() → DiscoveryManager
               ├─ _handle_gattc_event() → ConnectionContext + callbacks
               ├─ _handle_gatts_event() → Peripheral logic
               └─ _handle_other_event() → Utilities
```

---

## State Management - Before vs After

### BEFORE
```python
class BLEHandler:
    def __init__(self):
        # UART connection state
        self._search_name = None
        self._addr_type = None
        self._addr = None
        self._tx_handle = None
        self._rx_handle = None
        
        # LEGO connection state
        self._lego_value_handle = None
        
        # Generic connection state
        self._conn_handle = None
        self._start_handle = None
        self._end_handle = None
        
        # Mode flags
        self.connecting_uart = False
        self.connecting_lego = False
        self._connected_central = -1
        
        # ... and more scattered state
```

### AFTER
```python
class ConnectionContext:
    def __init__(self, protocol_type):
        self.protocol = protocol_type
        self.state = ConnectionState.IDLE
        self.conn_handle = None
        self.addresses = {}      # {addr_type, addr}
        self.characteristics = {}  # {uuid: handle}
        self.callbacks = {}

class BLEHandler:
    def __init__(self):
        self._contexts = {}  # {protocol: ConnectionContext}
        self._callbacks = CallbackRegistry()
        self._discovery = DiscoveryManager(self)
```

✓ Clear, centralized, protocol-agnostic state
✓ Easy to add new protocols
✓ No boolean flag spaghetti
```

---

## Callback Management - Before vs After

### BEFORE
```python
class BLEHandler:
    def __init__(self):
        self._write_done_callbacks = {}
        self._disconn_callbacks = {}
        self._notify_callbacks = {}
        self._write_callbacks = {}
        self._scan_result_callback = None
        self._char_result_callback = None
    
    # Callbacks scattered throughout _irq()
    # No cleanup mechanism
    # Memory leaks possible
    # Hard to debug which callback is called

# Usage:
ble.on_write(handle, callback)
ble.on_write_done(conn, callback)
# ... but disconnection doesn't clean them up!
```

### AFTER
```python
class CallbackRegistry:
    def __init__(self):
        self._callbacks = {}  # {(conn_handle, event_type): callback}
    
    def register(self, conn_handle, event_type, callback):
        key = (conn_handle, event_type)
        self._callbacks[key] = callback
    
    def trigger(self, conn_handle, event_type, *args):
        key = (conn_handle, event_type)
        if key in self._callbacks:
            self._callbacks[key](*args)
    
    def cleanup(self, conn_handle):
        """Automatic cleanup on disconnect"""
        to_remove = [k for k in self._callbacks if k[0] == conn_handle]
        for k in to_remove:
            del self._callbacks[k]

class BLEHandler:
    def on_peripheral_disconnect(self, conn_handle, addr_type, addr):
        self._callbacks.cleanup(conn_handle)  # Auto cleanup!
```

✓ Single source of truth for callbacks
✓ Automatic cleanup
✓ No memory leaks
✓ Easy to debug and test

---

## Adding New Protocols - Before vs After

### BEFORE
```python
# Adding MESH protocol support:
# 1. Add 20+ state variables to BLEHandler
# 2. Add new connection flags (connecting_mesh)
# 3. Add case to _irq() for MESH events
# 4. Add connect_mesh() method with duplicate logic
# 5. Manually wire callbacks
# 6. Hope nothing breaks!

Risk: Very high. Easy to introduce bugs in 350-line class.
```

### AFTER
```python
# Adding MESH protocol support:
# 1. Create MeshConnectionManager class (100 lines)
# 2. Implement connect() method
# 3. Implement _on_service_found() callback
# 4. Register with BLEHandler
# Done!

class MeshConnectionManager:
    def __init__(self, ble_handler):
        self.handler = ble_handler
        self._discovery = DiscoveryManager(ble_handler)
    
    def connect(self, name):
        ctx = ConnectionContext("MESH")
        self._discovery.scan_for(name)
        # ... implementation

Risk: Low. Isolated, testable, follows same pattern.
```

---

## Code Quality Metrics

### Cyclomatic Complexity

**Before:**
```
BLEHandler._irq(): 47
BLEHandler.connect_uart(): 18
BLEHandler.connect_lego(): 12
Total: Very high, hard to understand
```

**After:**
```
BLEHandler._irq(): 8
BLEHandler._handle_scan_event(): 6
BLEHandler._handle_gattc_event(): 7
DiscoveryManager.handle_event(): 5
UARTConnectionManager.connect(): 4
Total per function: Low, easy to understand
```

### Test Coverage Example

```python
# BEFORE: Hard to test
def test_connect_uart():
    # How do you mock ubluetooth events?
    # How do you inject scan results?
    # How do you verify state changes?
    pass

# AFTER: Easy to test
def test_uart_connection_manager():
    mock_handler = Mock()
    ctx = ConnectionContext("UART")
    manager = UARTConnectionManager(mock_handler, ctx)
    
    # Inject mock results
    manager._discovery.on_scan_result(addr_type, addr, "robot", [_UART_UUID])
    
    # Verify state changed
    assert ctx.state == ConnectionState.CONNECTING
    mock_handler.gap_connect.assert_called()
```

---

## Summary Table

| Metric | Before | After |
|--------|--------|-------|
| **BLEHandler LOC** | 350 | 150 |
| **Max function LOC** | 50 | 15 |
| **Max cyclomatic complexity** | 47 | 8 |
| **Number of classes** | 1 | 5+ |
| **Callbacks per class** | 7 | 1 |
| **State variables per class** | 20+ | 3-5 |
| **Test difficulty** | Very High | Low |
| **Easy to add protocol?** | No | Yes |
| **Memory safe?** | No | Yes |
| **Developer docs needed?** | High | Low |

---

## Key Takeaways

1. **Monolithic design** → **Modular design** (responsibility separation)
2. **Boolean flags** → **State machine** (explicit states)
3. **Scattered callbacks** → **Centralized registry** (lifecycle management)
4. **Duplicate connection logic** → **Reusable managers** (DRY principle)
5. **Hard to test** → **Easy to test** (isolated components)

Each refactoring phase maintains backward compatibility while improving code quality.
