"""
Connection Context for BLE Handler - Encapsulates connection state.

Extracted from BLEHandler to improve state management and reduce scattered variables.
Consolidates all state related to a single connection.
"""

# Discovery/connect modes (used by DiscoveryManager)
CONNECTING_NONE = 0
CONNECTING_UART = 1
CONNECTING_LEGO = 2


class ConnectionContext:
    """
    Encapsulates all state related to a BLE connection.

    Replaces scattered state variables throughout BLEHandler:
    - _conn_handle
    - _start_handle / _end_handle
    - _rx_handle / _tx_handle
    - _lego_value_handle
    - _addr_type / _addr

    Provides:
    - Single source of truth for connection state
    - Type-specific state (UART vs LEGO)
    - Atomic state transitions
    """

    # Connection states
    STATE_IDLE = 0
    STATE_CONNECTING = 1
    STATE_DISCOVERING = 2
    STATE_CONNECTED = 3
    STATE_DISCONNECTING = 4

# Discovery/connect modes (used by DiscoveryManager)
CONNECTING_NONE = 0
CONNECTING_UART = 1
CONNECTING_LEGO = 2

def __init__(self):
    """Initialize connection context with empty state."""
    # Basic connection info
    self.conn_handle = None
    self.addr_type = None
    self.addr = None

    # Discovery state
    self.start_handle = None
    self.end_handle = None

    # UART-specific handles
    self.uart_rx_handle = None
    self.uart_tx_handle = None

    # LEGO-specific handles
    self.lego_value_handle = None

    # Advertisement data
    self.adv_type = None
    self.name = None
    self.services = None

    # State machine
    self.state = self.STATE_IDLE

def reset(self):
    """Reset context to idle state."""
    self.conn_handle = None
    self.addr_type = None
    self.addr = None
    self.start_handle = None
    self.end_handle = None
    self.uart_rx_handle = None
    self.uart_tx_handle = None
    self.lego_value_handle = None
    self.adv_type = None
    self.name = None
    self.services = None
    self.state = self.STATE_IDLE

def set_connection_info(self, conn_handle, addr_type=None, addr=None):
    """
    Set basic connection information.

    :param conn_handle: Connection handle from BLE
    :type conn_handle: int
    :param addr_type: Address type (optional)
    :type addr_type: int
    :param addr: Device address (optional)
    :type addr: bytes
    """
    self.conn_handle = conn_handle
    if addr_type is not None:
        self.addr_type = addr_type
    if addr is not None:
        self.addr = bytes(addr)  # Copy to own the buffer

def set_discovery_handles(self, start_handle, end_handle):
    """
    Set GATT service discovery handles.

    :param start_handle: Start handle of service
    :type start_handle: int
    :param end_handle: End handle of service
    :type end_handle: int
    """
    self.start_handle = start_handle
    self.end_handle = end_handle

def set_uart_handles(self, rx_handle, tx_handle):
    """
    Set UART characteristic handles.

    :param rx_handle: RX characteristic handle
    :type rx_handle: int
    :param tx_handle: TX characteristic handle
    :type tx_handle: int
    """
    self.uart_rx_handle = rx_handle
    self.uart_tx_handle = tx_handle

def set_lego_handle(self, value_handle):
    """
    Set LEGO characteristic handle.

    :param value_handle: LEGO characteristic handle
    :type value_handle: int
    """
    self.lego_value_handle = value_handle

def set_discovery_data(self, adv_type, name, services):
    """
    Set advertisement data from discovery.

    :param adv_type: Advertisement type
    :type adv_type: int
    :param name: Device name
    :type name: str
    :param services: List of service UUIDs
    :type services: list
    """
    self.adv_type = adv_type
    self.name = name
    self.services = services if services else []

def is_uart_ready(self):
    """
    Check if all required UART handles are set.

    :return: True if both RX and TX handles are available
    :rtype: bool
    """
    return self.uart_rx_handle is not None and self.uart_tx_handle is not None

def is_lego_ready(self):
    """
    Check if LEGO handle is set.

    :return: True if LEGO handle is available
    :rtype: bool
    """
    return self.lego_value_handle is not None

def is_connected(self):
    """
    Check if connection is established.

    :return: True if connected, False otherwise
    :rtype: bool
    """
    return self.conn_handle is not None and self.state == self.STATE_CONNECTED

def has_discovery_handles(self):
    """
    Check if discovery handles are set.

    :return: True if both start and end handles are available
    :rtype: bool
    """
    return self.start_handle is not None and self.end_handle is not None

def clear_connection(self):
    """Clear connection information (called on disconnect)."""
    self.conn_handle = None
    self.state = self.STATE_IDLE

def __repr__(self):
    """String representation for debugging."""
    uart_status = "READY" if self.is_uart_ready() else "pending"
    lego_status = "READY" if self.is_lego_ready() else "pending"
    return (
        f"ConnectionContext(conn={self.conn_handle}, "
        f"uart={uart_status}, lego={lego_status}, "
        f"state={self.state}, name={self.name})"
    )
