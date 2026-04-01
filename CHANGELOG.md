# CHANGELOG

## [3.2.0]

### Added
- Added Mobile ID authorization support: `send_mobile_id`, `mobile_id_status`, `verify_mobile_id`.

### Fixed
- Fixed pytest compatibility with pytest 9.x (removed invalid `[]` path argument).
- Fixed missing test coverage for `callbackFormat` parameter in `send_sms`.

## [3.1.0]

### Added
- Added Telegram code sending functionality.

### Fixed
- Fixed pylint warnings

### Changed
- Refined exception handling strategy to catch only specific exceptions
- Improved error handling best practices following Python guidelines


## [3.0.0]

### Added
- Added Docker support for the demo application.
- Added a command line for sending SMS.

### Changed
- Updated dependencies to improve security and performance.
- Improved exception handling in the library.

### Removed
- Removed support for Python 2.7 and 3.4.
