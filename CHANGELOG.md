# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- The package imports and runs on Python 3.9, as `requires-python` declares.
- A report sent to a redirected stdout (`jpd a.json b.json > diff.html`) is written as UTF-8,
  the charset the page declares, instead of crashing on a Windows console code page.
- `true` and `1`, or `false` and `0`, at any depth, are reported as changed (RFC 8259 keeps
  them as different value types).
- A document with `NaN` compared with itself no longer reports a change.
- Section anchors stay unique when a key looks like a numbered anchor (`a b`, `a-b`, `a-b-2`).
- Invalid UTF-8, unreadable inputs, unwritable outputs, integers beyond Python's digit limit
  and documents nested too deeply print `Error: ...` and exit with 2 instead of a traceback.
- Lone surrogate escapes such as `"\ud800"` are written as `\ud800` instead of crashing.

### Added
- A UTF-8 byte order mark at the start of an input is accepted (RFC 8259 section 8.1).
- `py.typed`, so type checkers use the package's annotations.
- A test suite with the 1.1.1 report pinned byte for byte, and a local quality gate.

## [1.1.1]

First version recorded here.
