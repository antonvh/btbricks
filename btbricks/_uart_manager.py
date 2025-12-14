"""
UART Connection Manager - High-level UART connection handling.

Part of Phase 2: Cleaner, protocol-specific connection managers.
Encapsulates UART-specific connection logic with clear, focused responsibility.

Replaces scattered UART connection code in BLEHandler and UARTCentral.
"""

try:
    from utime import sleep_ms
except Exception:
    from time import sleep

    def sleep_ms(ms):
        sleep(ms / 1000.0)


class UARTConnectionManager:
    """
    Manages BLE UART connections with a clean, focused API.

    Handles:
    - Finding UART devices by name
    - Establishing connections
    - Negotiating MTU
    - Registering callbacks
    - Providing write interface

    Usage:
        manager = UARTConnectionManager(ble_handler)
        conn_handle, rx_handle, tx_handle = manager.connect("robot_name")
        manager.on_notify(conn_handle, my_callback)
        manager.write(conn_handle, data, rx_handle)
    """

    def __init__(self, ble_handler):
        """
        Initialize UART connection manager.

        :param ble_handler: BLEHandler instance to use for BLE operations
        :type ble_handler: BLEHandler
        """
        self.ble_handler = ble_handler
        self.is_connecting = False

    def connect(
        self,
        name="robot",
        on_disconnect=None,
        on_notify=None,
        on_write_done=None,
        timeout=10,
        debug=False,
    ):
        """
        Connect to a UART peripheral by name.

        Cleaner alternative to BLEHandler.connect_uart().
        Returns immediately on success or failure.

        :param name: Name of device to find and connect to
        :type name: str
        :param on_disconnect: Callback when device disconnects
        :type on_disconnect: function
        :param on_notify: Callback for notifications from device
        :type on_notify: function
        :param on_write_done: Callback when write completes
        :type on_write_done: function
        :param timeout: Seconds to wait for connection
        :type timeout: int
        :param debug: Show debug output during connection
        :type debug: bool
        :return: Tuple of (conn_handle, rx_handle, tx_handle) or (None, None, None) on failure
        :rtype: tuple
        """
        self.is_connecting = True

        # Start discovery using BLEHandler's components
        self.ble_handler._discovery.start_uart_discovery(name)
        self.ble_handler._connection.reset()

        # Begin scanning
        self.ble_handler.scan()

        # Wait for connection with timeout
        for i in range(timeout):
            if debug:
                self.ble_handler.print_log()
            else:
                print(f"[UART] Connecting to {name}... ({i+1}/{timeout}s)")
            sleep_ms(1000)
            from ._connection_context import CONNECTING_NONE

            if self.ble_handler._discovery.mode == CONNECTING_NONE:
                break

        # Check if connection succeeded
        if self.ble_handler._connection.is_uart_ready():
            # Register callbacks
            if on_notify:
                self.ble_handler._callbacks.on_notify(
                    self.ble_handler._connection.conn_handle, on_notify
                )
            if on_disconnect:
                self.ble_handler._callbacks.on_disconnect(
                    self.ble_handler._connection.conn_handle, on_disconnect
                )
            if on_write_done:
                self.ble_handler._callbacks.on_write_done(
                    self.ble_handler._connection.conn_handle, on_write_done
                )

            # Negotiate MTU for better throughput
            self._negotiate_mtu()

            result = (
                self.ble_handler._connection.conn_handle,
                self.ble_handler._connection.uart_rx_handle,
                self.ble_handler._connection.uart_tx_handle,
            )
        else:
            result = (None, None, None)

        self.ble_handler._discovery.stop_discovery()
        self.is_connecting = False
        return result

    def _negotiate_mtu(self):
        """
        Negotiate MTU (Maximum Transmission Unit) with device.
        Increases packet size for better throughput.
        """
        from btbricks.bt import TARGET_MTU

        conn_handle = self.ble_handler._connection.conn_handle
        try:
            self.ble_handler._ble.config(mtu=TARGET_MTU)
            self.ble_handler._ble.gattc_exchange_mtu(conn_handle)
            sleep_ms(60)
            self.ble_handler.mtu = self.ble_handler._ble.config("mtu") - 4
        except:
            # MTU negotiation failed, continue with default
            pass

    def write(self, conn_handle, data, rx_handle=12, response=False):
        """
        Write data to UART RX characteristic.

        :param conn_handle: Connection handle
        :type conn_handle: int
        :param data: Data to write
        :type data: bytes
        :param rx_handle: RX characteristic handle (default 12)
        :type rx_handle: int
        :param response: Whether to request write response
        :type response: bool
        """
        self.ble_handler.uart_write(data, conn_handle, rx_handle, response)

    def on_notify(self, conn_handle, callback):
        """
        Register callback for notifications.

        :param conn_handle: Connection handle
        :type conn_handle: int
        :param callback: Callback function
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

    def on_write_done(self, conn_handle, callback):
        """
        Register callback for write completion.

        :param conn_handle: Connection handle
        :type conn_handle: int
        :param callback: Callback function
        :type callback: function
        """
        self.ble_handler._callbacks.on_write_done(conn_handle, callback)

    def disconnect(self, conn_handle):
        """
        Disconnect from device.

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
