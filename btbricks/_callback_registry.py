"""
Callback Registry for BLE Handler - Centralized callback management.

Extracted from BLEHandler to improve separation of concerns.
Eliminates scattered callback dictionaries and provides clean management.
"""


class CallbackRegistry:
    """
    Centralized callback management for BLE events.

    Replaces scattered callback dictionaries throughout BLEHandler:
    - _write_callbacks
    - _write_done_callbacks
    - _notify_callbacks
    - _disconn_callbacks

    Provides:
    - Type-safe callback registration
    - Automatic cleanup
    - Clear callback lifecycle
    """

    def __init__(self):
        """Initialize callback registry with empty storage."""
        # Callbacks triggered when a characteristic/descriptor is written
        self._write_callbacks = {}

        # Callbacks triggered when write operation completes
        self._write_done_callbacks = {}

        # Callbacks triggered when notification is received
        self._notify_callbacks = {}

        # Callbacks triggered when connection is lost
        self._disconn_callbacks = {}

        # Callbacks for central connection/disconnection (peripheral side)
        self._central_conn_callback = None
        self._central_disconn_callback = None

        # Callbacks for scan events
        self._scan_result_callback = None
        self._scan_done_callback = None

        # Callback for characteristic discovery results
        self._char_result_callback = None

    def on_write(self, value_handle, callback):
        """
        Register callback for when a characteristic is written.

        :param value_handle: The GATT value handle
        :type value_handle: int
        :param callback: Function to call when written, receives (value)
        :type callback: function
        """
        self._write_callbacks[value_handle] = callback

    def on_write_done(self, conn_handle, callback):
        """
        Register callback for when a write operation completes.

        :param conn_handle: The connection handle
        :type conn_handle: int
        :param callback: Function to call when done, receives (value_handle, status)
        :type callback: function
        """
        self._write_done_callbacks[conn_handle] = callback

    def on_notify(self, conn_handle, callback):
        """
        Register callback for notifications from a connection.

        :param conn_handle: The connection handle
        :type conn_handle: int
        :param callback: Function to call on notify, receives (notify_data)
        :type callback: function
        """
        self._notify_callbacks[conn_handle] = callback

    def on_disconnect(self, conn_handle, callback):
        """
        Register callback for disconnection.

        :param conn_handle: The connection handle
        :type conn_handle: int
        :param callback: Function to call on disconnect, receives ()
        :type callback: function
        """
        self._disconn_callbacks[conn_handle] = callback

    def on_central_connect(self, callback):
        """
        Register callback for when a central connects (peripheral side).

        :param callback: Function to call on connect, receives (conn_handle, addr_type, addr)
        :type callback: function
        """
        self._central_conn_callback = callback

    def on_central_disconnect(self, callback):
        """
        Register callback for when a central disconnects (peripheral side).

        :param callback: Function to call on disconnect, receives (conn_handle)
        :type callback: function
        """
        self._central_disconn_callback = callback

    def on_scan_result(self, callback):
        """
        Register callback for scan results.

        :param callback: Function to call on result, receives (addr_type, addr, name, services)
        :type callback: function
        """
        self._scan_result_callback = callback

    def on_scan_done(self, callback):
        """
        Register callback for when scan is done.

        :param callback: Function to call on done, receives (data)
        :type callback: function
        """
        self._scan_done_callback = callback

    def on_char_result(self, callback):
        """
        Register callback for characteristic discovery results.

        :param callback: Function to call on result, receives (conn_handle, value_handle, uuid)
        :type callback: function
        """
        self._char_result_callback = callback

    def get_write_callback(self, value_handle):
        """Get write callback for a value handle."""
        return self._write_callbacks.get(value_handle)

    def get_write_done_callback(self, conn_handle):
        """Get write-done callback for a connection."""
        return self._write_done_callbacks.get(conn_handle)

    def get_notify_callback(self, conn_handle):
        """Get notify callback for a connection."""
        return self._notify_callbacks.get(conn_handle)

    def get_disconnect_callback(self, conn_handle):
        """Get disconnect callback for a connection."""
        return self._disconn_callbacks.get(conn_handle)

    def get_central_conn_callback(self):
        """Get central connection callback."""
        return self._central_conn_callback

    def get_central_disconn_callback(self):
        """Get central disconnection callback."""
        return self._central_disconn_callback

    def get_scan_result_callback(self):
        """Get scan result callback."""
        return self._scan_result_callback

    def get_scan_done_callback(self):
        """Get scan done callback."""
        return self._scan_done_callback

    def get_char_result_callback(self):
        """Get characteristic result callback."""
        return self._char_result_callback

    def clear_connection(self, conn_handle):
        """
        Clean up all callbacks for a specific connection (called on disconnect).

        :param conn_handle: The connection handle to clean up
        :type conn_handle: int
        """
        # Remove all callbacks related to this connection
        self._write_done_callbacks.pop(conn_handle, None)
        self._notify_callbacks.pop(conn_handle, None)
        self._disconn_callbacks.pop(conn_handle, None)

    def clear_all(self):
        """Clear all registered callbacks."""
        self._write_callbacks.clear()
        self._write_done_callbacks.clear()
        self._notify_callbacks.clear()
        self._disconn_callbacks.clear()
        self._central_conn_callback = None
        self._central_disconn_callback = None
        self._scan_result_callback = None
        self._scan_done_callback = None
        self._char_result_callback = None

    def has_callbacks(self, conn_handle):
        """
        Check if there are any callbacks for a connection.

        :param conn_handle: The connection handle to check
        :type conn_handle: int
        :return: True if any callbacks exist
        :rtype: bool
        """
        return (
            conn_handle in self._write_done_callbacks
            or conn_handle in self._notify_callbacks
            or conn_handle in self._disconn_callbacks
        )
