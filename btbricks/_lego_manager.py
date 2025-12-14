"""
LEGO Connection Manager - High-level LEGO hub connection handling.

Part of Phase 2: Cleaner, protocol-specific connection managers.
Encapsulates LEGO-specific connection logic with clear, focused responsibility.

Replaces scattered LEGO connection code in BLEHandler and BtHub.
"""

try:
    from utime import sleep_ms
except Exception:
    from time import sleep

    def sleep_ms(ms):
        sleep(ms / 1000.0)


class LEGOConnectionManager:
    """
    Manages BLE connections to LEGO Smart Hubs with a clean, focused API.

    Handles:
    - Finding LEGO hubs via BLE discovery
    - Establishing GATT connections
    - Locating LEGO service characteristics
    - Providing write/read interface
    - Managing LEGO-specific protocol

    Usage:
        manager = LEGOConnectionManager(ble_handler)
        conn_handle = manager.connect()
        manager.write(conn_handle, command_bytes)
        manager.on_notify(conn_handle, my_callback)
    """

    def __init__(self, ble_handler):
        """
        Initialize LEGO connection manager.

        :param ble_handler: BLEHandler instance to use for BLE operations
        :type ble_handler: BLEHandler
        """
        self.ble_handler = ble_handler
        self.is_connecting = False

    def connect(self, timeout=10, debug=False):
        """
        Connect to a LEGO Smart Hub.

        LEGO hubs advertise when LEDs are blinking (just after power on).
        This method searches for any LEGO hub and connects to the first found.

        Cleaner alternative to BLEHandler.connect_lego().

        :param timeout: Seconds to wait for hub discovery
        :type timeout: int
        :param debug: Show debug output during connection
        :type debug: bool
        :return: Connection handle or None on failure
        :rtype: int or None
        """
        self.is_connecting = True

        # Start discovery using BLEHandler's components
        self.ble_handler._discovery.start_lego_discovery()
        self.ble_handler._connection.reset()

        # Begin scanning
        self.ble_handler.scan()

        # Wait for connection with timeout
        for i in range(timeout):
            if debug:
                self.ble_handler.print_log()
            else:
                print(f"[LEGO] Searching for hub... ({i+1}/{timeout}s)")
            sleep_ms(1000)
            from ._connection_context import CONNECTING_NONE

            if self.ble_handler._discovery.mode == CONNECTING_NONE:
                break

        # Get result
        conn_handle = (
            self.ble_handler._connection.conn_handle
            if self.ble_handler._connection.is_lego_ready()
            else None
        )

        self.ble_handler._discovery.stop_discovery()
        self.is_connecting = False

        if conn_handle:
            print(f"[LEGO] Connected: {self.ble_handler._connection.name}")

        return conn_handle

    def write(self, conn_handle, data, response=False):
        """
        Write command to LEGO hub characteristic.

        :param conn_handle: Connection handle
        :type conn_handle: int
        :param data: Command data to write
        :type data: bytes
        :param response: Whether to request write response
        :type response: bool
        """
        self.ble_handler.lego_write(data, conn_handle, response)

    def on_notify(self, conn_handle, callback):
        """
        Register callback for hub notifications (sensor/status data).

        :param conn_handle: Connection handle
        :type conn_handle: int
        :param callback: Callback function receives (data: bytes)
        :type callback: function
        """
        self.ble_handler._callbacks.on_notify(conn_handle, callback)

    def on_disconnect(self, conn_handle, callback):
        """
        Register callback for disconnection.

        :param conn_handle: Connection handle
        :type conn_handle: int
        :param callback: Callback function
        :type callback: function
        """
        self.ble_handler._callbacks.on_disconnect(conn_handle, callback)

    def disconnect(self, conn_handle):
        """
        Disconnect from hub.

        :param conn_handle: Connection handle
        :type conn_handle: int
        """
        if conn_handle is not None:
            try:
                self.ble_handler._ble.gap_disconnect(conn_handle)
            except:
                pass
            self.ble_handler._callbacks.clear_connection(conn_handle)
            self.ble_handler._connection.clear_connection()

    def get_hub_name(self, conn_handle=None):
        """
        Get the name of the connected hub.

        :param conn_handle: Connection handle (optional, uses last connected)
        :type conn_handle: int
        :return: Hub name or None
        :rtype: str or None
        """
        if self.ble_handler._connection.name:
            return self.ble_handler._connection.name
        return None
