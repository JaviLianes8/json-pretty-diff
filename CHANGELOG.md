# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-10-15

The command-line options, the exit codes, the report layout and every name that 1.1.1 could
import keep working. This release is stable: the names in `json_pretty_diff.__all__`, the
`jpd` options and the exit codes 0, 1 and 2 will only change in a new major version.
[GUIDE.md](https://github.com/JaviLianes8/json-pretty-diff/blob/main/GUIDE.md) has the upgrade
notes.

### Changed (results that differ from 1.1.1 for the same input)
- Input that 1.1.1 refused or crashed on is listed under Added and Fixed: a byte order mark,
  text that is not UTF-8, lone surrogate escapes, very long integers and very deep nesting.
- `true` and `1`, or `false` and `0`, at any depth, are reported as changed (RFC 8259 keeps
  them as different value types). 1.1.1 reported no difference and exited with 0.
- A document with `NaN` compared with itself no longer reports a change (exit 0, was 1).
- A report on standard output is always UTF-8, whatever the console encoding.
- The header line reads `Generated on <time> UTC - v1.2.0`: a plain hyphen instead of a long
  dash.
- The three icons of the report header are drawn inside the page (`data:` images) instead of
  being loaded from two CDNs, so a report opened offline is complete and opening it contacts
  nobody. They are small drawings of the same three marks.
- Diff blocks no longer show an empty row between lines in the browser. Each line of a diff
  block is one `<span>` that ends with its own line break, with nothing between the spans.
- Input holding `NaN`, `Infinity` or `-Infinity`, a number beyond the range of a double (read
  as infinity, as before), or an object name repeated in the same object (the last value is
  used, as before) is still compared, and now gets a `Warning: <file> ...` line on stderr and a
  "Warnings" section at the top of the report. `-q` silences the stderr lines; the section
  stays. Warnings never change the exit code.
- When the reader of the standard output stops early (`jpd a.json b.json | head`), `jpd` stops
  writing quietly and exits with the comparison result, 0 or 1. 1.1.1 printed a
  `BrokenPipeError` traceback and exited with 1. Any other failure to write to standard output
  prints `Error: Cannot write to standard output: ...` and exits with 2.
  Without any standard output (`pythonw`, a closed descriptor) the report cannot be shown
  and `jpd` exits with 2; with `-o` the report is written and the status line skipped.
- Line matching for the diff blocks and the full JSON table is bounded by a work budget (10
  million steps of `difflib`'s inner loop, a few seconds at most). Input past the budget, such
  as an array of 16,000 values repeating 150 numbers (about two minutes in 1.1.1, a few
  seconds now), shows the part between the lines both sides share at the start and at the end
  as one replacement. Input within the budget gives exactly the lines 1.1.1 gave.
- Error and warning lines that the console cannot encode are written with backslash escapes
  instead of failing.

### Added
- `--no-timestamp` leaves the generation time out of the report (the header line then reads
  `json-pretty-diff v1.2.0`), so the same inputs always give the same file. The default is
  unchanged.
- `render_html(..., include_timestamp=True, warnings=())`: two keyword options matching the
  above.
- The public names can be imported from the package itself: `DiffResult`, `DiffUseCase`,
  `JsonPrettyDiffCLI`, `compute_top_level_diff`, `main` and `render_html`. The 1.1.1 module
  paths still work.
- A UTF-8 byte order mark at the start of an input is accepted (RFC 8259 section 8.1).
- `py.typed`, so type checkers use the package's annotations.
- `compute_top_level_diff` and `DiffUseCase.execute` accept any mapping and raise `TypeError`
  naming the argument that is not one (1.1.1 failed later with an unrelated error).
- Package metadata: Production/Stable status, supported Python versions, `Typing :: Typed`, an
  SPDX licence expression, and Source, Issues and Changelog links.

### Fixed
- The package imports and runs on Python 3.9, as `requires-python` declares.
- A report sent to a redirected stdout (`jpd a.json b.json > diff.html`) no longer crashes on
  a Windows console code page.
- Section anchors stay unique when a key looks like a numbered anchor (`a b`, `a-b`, `a-b-2`).
- Invalid UTF-8, unreadable inputs, unwritable outputs, integers beyond Python's digit limit
  and documents nested too deeply print `Error: ...` and exit with 2 instead of a traceback.
- Errors name a directory given as input or output, and hint at UTF-16 input.
- Lone surrogate escapes such as `"\ud800"` are written as `\ud800` instead of crashing.
- A string holding U+2028, U+2029 or U+0085 stays on one row of the diff blocks and the full
  JSON table; 1.1.1 split it there and dropped the character from the table.

### Unchanged on purpose
- `1` and `1.0` compare as equal, and so do numbers with a fraction or an exponent that
  read as the same double (`0.1` and `0.10000000000000001`). Integers are read exactly.
- Integers longer than Python's digit limit and documents nested too deeply for the report
  are still not compared; they now end in `Error: ...` and exit 2 (see Fixed).

## [1.1.1]

First version recorded here.
