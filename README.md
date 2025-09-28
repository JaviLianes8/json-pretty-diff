# json-pretty-diff

## Purpose
Generate a clean HTML report that summarizes the top-level differences between two JSON files. The report groups keys into Added, Removed, and Changed sections to make the impact of the updates easy to scan.

## Local installation
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
- When `-o` is omitted, the HTML is printed to `stdout` and can be redirected with `>`.
- Exit code `0`: no differences were detected (an HTML report is still generated showing "No differences").
- Exit code `1`: differences were found and the HTML describes every change.
- Exit code `2`: an error occurred (missing file, invalid JSON, or a root element that is not a JSON object) and no HTML report is produced.

## Example
```bash
jpd fixtures/base.json fixtures/update.json -o reports/diff.html
```
The file `diff.html` will contain one section per change category with simple styles that highlight added, removed, or modified keys.

## Limitations
- Only the first-level keys are compared (no recursive diff).
- There are no exclusions, tolerances, or advanced configuration flags.
- Console output never uses ANSI colors.
- There is no CI/CD integration or bundled automated test suite.
