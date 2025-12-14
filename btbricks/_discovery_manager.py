"""
Discovery Manager for BLE Handler - Encapsulates BLE scanning and device discovery.

Extracted from BLEHandler to improve separation of concerns.
Handles:
- Device scanning and filtering
- Device name and service lookup
- Discovery state management
"""


class DiscoveryManager:
    """
    Manages BLE device discovery (scanning).

    Encapsulates the state and logic for:
    - Starting/stopping scans
    - Filtering discovered devices
    - Tracking search parameters (name, services)
    """

    def __init__(self):
        """Initialize discovery manager with empty state."""
        self._search_name = None
        self._search_uuid = None
        from ._connection_context import CONNECTING_NONE

        # mode: CONNECTING_NONE / CONNECTING_UART / CONNECTING_LEGO
        self.mode = CONNECTING_NONE
        self._addr_type = None
        self._addr = None
        self._adv_type = None
        self._name = None
        self._services = None
        self._scan_result_callback = None
        self._scan_done_callback = None

    def start_uart_discovery(self, name, callback_result=None, callback_done=None):
        """
        Start discovery for a UART peripheral by name.

        :param name: Name of the device to find
        :type name: str
        :param callback_result: Optional callback for each scan result
        :type callback_result: function
        :param callback_done: Optional callback when scan is done
        :type callback_done: function
        """
        self._search_name = name
        from ._connection_context import CONNECTING_UART

        self.mode = CONNECTING_UART
        self._addr_type = None
        self._addr = None
        self._scan_result_callback = callback_result
        self._scan_done_callback = callback_done

    def start_lego_discovery(self, callback_result=None, callback_done=None):
        """
        Start discovery for a LEGO hub.

        :param callback_result: Optional callback for each scan result
        :type callback_result: function
        :param callback_done: Optional callback when scan is done
        :type callback_done: function
        """
        from ._connection_context import CONNECTING_LEGO

        self.mode = CONNECTING_LEGO
        self._addr_type = None
        self._addr = None
        self._adv_type = None
        self._name = None
        self._services = None
        self._scan_result_callback = callback_result
        self._scan_done_callback = callback_done

    def stop_discovery(self):
        """Stop scanning and reset discovery state."""
        from ._connection_context import CONNECTING_NONE

        self.mode = CONNECTING_NONE
        self._scan_result_callback = None
        self._scan_done_callback = None

    def on_scan_result(self, addr_type, addr, name, services, uart_uuid, lego_uuid):
        """
        Process a scan result during discovery.

        :param addr_type: Address type of discovered device
        :type addr_type: int
        :param addr: Address of discovered device
        :type addr: bytes
        :param name: Name decoded from advertisement
        :type name: str
        :param services: Services decoded from advertisement
        :type services: list
        :param uart_uuid: UART service UUID for comparison
        :type uart_uuid: UUID
        :param lego_uuid: LEGO service UUID for comparison
        :type lego_uuid: UUID
        :return: True if device matched our search criteria, False otherwise
        :rtype: bool
        """
        matched = False

        if (
            self.mode
            == __import__("btbricks.btbricks._connection_context", fromlist=[""]).CONNECTING_UART
        ):
            if name == self._search_name and uart_uuid in services:
                # Found the UART device we're looking for
                self._addr_type = addr_type
                self._addr = bytes(addr)  # Copy since buffer is owned by caller
                matched = True

        if (
            self.mode
            == __import__("btbricks.btbricks._connection_context", fromlist=[""]).CONNECTING_LEGO
        ):
            if lego_uuid in services:
                # Found a LEGO hub
                self._addr_type = addr_type
                self._addr = bytes(addr)
                self._adv_type = None  # Will be set if needed
                self._name = name
                self._services = services
                matched = True

        # Call user's scan result callback if provided
        if self._scan_result_callback:
            self._scan_result_callback(addr_type, addr, name, services)

        return matched

    def on_scan_done(self):
        """
        Process scan done event.

        :return: Tuple of (found, name_or_addr) where found is bool, name_or_addr is str or None
        :rtype: tuple
        """
        found = False
        info = None

        from ._connection_context import CONNECTING_UART, CONNECTING_LEGO

        if self.mode == CONNECTING_UART:
            found = self._addr_type is not None
            info = self._search_name if found else None
        elif self.mode == CONNECTING_LEGO:
            found = self._addr_type is not None
            info = self._name if found else None

        # Call user's scan done callback if provided
        if self._scan_done_callback:
            self._scan_done_callback(found)

        return found, info

    def get_discovered_address(self):
        """
        Get the address info of the last discovered device.

        :return: Tuple of (addr_type, addr) or (None, None) if not found
        :rtype: tuple
        """
        return self._addr_type, self._addr

    def is_discovering(self):
        """
        Check if discovery is currently active.

        :return: True if actively discovering, False otherwise
        :rtype: bool
        """
        from ._connection_context import CONNECTING_NONE

        return self.mode != CONNECTING_NONE
