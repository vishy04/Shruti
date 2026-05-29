# Changelog

## [v0.2.0] - 2026-05-29
### Added
- Relational two-sheet database (Customers + Orders)
- Persistent message deduplication via ProcessedMessages sheet
- Duplicate order detection (last 5 entries)

### Changed
- Switched LLM from llama-3.3-70b to llama-3.1-8b-instant (faster)
- Extraction prompt now consolidates design features into special_instructions

### Fixed
- WhatsApp signature verification was using wrong HMAC function
