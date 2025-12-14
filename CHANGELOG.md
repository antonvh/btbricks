# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Phase 2 (v0.2)

- Add `UARTConnectionManager` and `LEGOConnectionManager` to encapsulate protocol-specific connection logic.
- Add `BLEHandler.uart_manager` and `BLEHandler.lego_manager` lazy properties.
- Add compatibility wrappers `BLEHandler.connect_uart_v2()` and `BLEHandler.connect_lego_v2()`.
- Update `DEVELOPMENT.md` with Phase 2 usage examples and migration notes.
- Improve tests and polyfills to support manager testing on CPython.

### Phase 1 (v0.1)

The initial refactor (Phase 1) extracted several single-responsibility components from the original `BLEHandler` implementation:

- `DiscoveryManager` — centralizes discovery/connect state and transitions.
- `CallbackRegistry` — centralized registration and cleanup for IRQ/callback handlers.
- `ConnectionContext` — small value object encapsulating connection state.
- Split the monolithic `_irq()` handler into specialized routers and handlers for clarity and testability.
- Ensure backward compatibility by keeping existing `connect_uart` / `connect_lego` wrappers.

### Changed

### Deprecated
- None yet; Phase 2 provides non-breaking alternatives. Old methods remain until v1.0.

### Fixed

### Security

## [0.1.0] - 2025-12-14

### Added
- Initial release of btbricks
- Core Hub class for Bluetooth communication
- HubScanner for discovering LEGO hubs
- Protocol module with LEGO BT protocol implementation
- Exception hierarchy for error handling
- API documentation
- Quick start guide
- Development guide
- Examples for hub discovery, control, linking, and sensor reading
