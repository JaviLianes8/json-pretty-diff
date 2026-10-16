# json-pretty-diff

<p align="center">
  <a href="https://www.linkedin.com/in/jlianes/" target="_blank" rel="noopener noreferrer"><img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" alt="LinkedIn" height="36" width="36" /></a>
  <a href="https://github.com/JaviLianes8/json-pretty-diff" target="_blank" rel="noopener noreferrer"><img src="https://cdn.simpleicons.org/github/181717" alt="GitHub" height="36" width="36" /></a>
  <a href="https://buymeacoffee.com/jlianesglrs" target="_blank" rel="noopener noreferrer"><img src="https://cdn.simpleicons.org/buymeacoffee/FFDD00" alt="Buy Me a Coffee" height="36" width="36" /></a>
</p>
<p align="center">Made with love by Javier Lianes García in Aranjuez ❤️</p>

> This project is stable. Bug fixes will be released as issues are reported.

## Overview
Generate a clean HTML report that summarizes the top-level differences between two JSON files. The report groups keys into Added, Removed, and Changed sections to make the impact of the updates easy to scan.

### Why not a plain text diff?
A line diff such as `diff -u old.json new.json` compares text, so a file that was only reformatted or had its keys reordered shows every line as changed. `jpd` reads both files as JSON first: whitespace and key order do not count, `true` is never mistaken for `1`, and what is left is shown per key in one page that opens in any browser, offline.

## Installation

### From PyPI (recommended)
1. Ensure Python 3.9 or newer is available on your system.
2. Install the package:
   ```bash
   pip install json-pretty-diff
   ```
3. Run the CLI to compare two JSON files:
   ```bash
   jpd original.json updated.json -o diff.html
   ```
4. Open `diff.html` in your browser to explore the report.

### From source
1. Clone this repository.
2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Usage
Run the command-line tool and point it to the files you want to compare:
```bash
jpd A.json B.json -o diff.html
```

### Options
| Flag | Description |
|------|-------------|
| `-o, --output` | Path to the output HTML file. When omitted, HTML is printed to stdout. |
| `--open` | Open the generated HTML report in the default browser (requires `-o`). |
| `-q, --quiet` | Suppress all output except errors. |
| `--no-style` | Generate HTML without CSS styles (lighter output). |
| `--no-timestamp` | Leave the generation time out, so the same inputs always give the same report. |
| `--version` | Show program version and exit. |

### Exit codes
- `0`: no differences were detected (an HTML report is still generated showing "No differences").
- `1`: differences were found and the HTML describes every change.
- `2`: an error occurred (missing file, invalid JSON, or a root element that is not a JSON object) and no HTML report is produced.

Warnings never change the exit code. If the program reading the standard output stops early (for example `jpd a.json b.json | head`), `jpd` stops writing quietly and still exits with `0` or `1`.

### Warnings
`NaN`, `Infinity`, numbers too large for a double and object names repeated inside the same object are not valid or not advised in JSON (RFC 8259). `jpd` still compares such files, prints a `Warning:` line on stderr for each kind (silenced by `-q`) and lists them at the top of the report.

## Use it from Python
```python
from json_pretty_diff import compute_top_level_diff, render_html

diff = compute_top_level_diff({"a": 1, "b": True}, {"a": 1.0, "b": 1, "c": 2})
assert diff.added == ["c"] and list(diff.changed) == ["b"]
html_page = render_html(diff, include_timestamp=False)
```

More in the [guide](https://github.com/JaviLianes8/json-pretty-diff/blob/main/GUIDE.md); every change is in the [changelog](https://github.com/JaviLianes8/json-pretty-diff/blob/main/CHANGELOG.md).

## Example
```bash
jpd fixtures/base.json fixtures/update.json -o reports/diff.html
```
The file `diff.html` will contain one section per change category with simple styles that highlight added, removed, or modified keys.
(`fixtures/` and `reports/` stand for your own folders.)

## Limitations
- Only the first-level keys are compared (no recursive diff).
- There are no exclusions, tolerances, or advanced configuration flags.
- Console output never uses ANSI colors.
- There is no CI/CD integration; the automated test suite in `tests/` runs locally (see `CONTRIBUTING.md`).
