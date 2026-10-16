# json-pretty-diff guide

`jpd` compares two JSON files whose root is an object, key by key at the top level, and
writes one self-contained HTML page with what was added, removed and changed.

## The report

From top to bottom:

1. The header with three links, the title and the line `Generated on <UTC time> - v<version>`
   (`json-pretty-diff v<version>` with `--no-timestamp`).
2. **Warnings**, only when an input holds something RFC 8259 does not allow or advises
   against (see below).
3. **SUMMARY**: three cards listing the added, removed and changed keys, each linking to its
   diff block, and the counts.
4. **DIFF**: one block per key, as a unified diff of the two values printed as indented JSON
   with sorted keys. Values longer than 10,000 characters are cut, with a "Show full content"
   panel holding the whole value.
5. **FULL JSON**: both documents side by side, line by line, with a search box that
   highlights matches.

The page needs no network: the styles, the search script and the icons are inside the file.

## How values are compared

A key is changed when its two values are different JSON values at any depth. Python reads
the files with its standard `json` module, and the comparison follows JSON's value types:

| Old | New | Result |
| --- | --- | --- |
| `true` | `1` | changed (a boolean is never a number) |
| `false` | `0` | changed |
| `null` | `0` | changed |
| `"1"` | `1` | changed |
| `1` | `1.0` | equal |
| `0.1` | `0.10000000000000001` | equal (both read as the same double) |
| `NaN` | `NaN` | equal (with a warning) |
| `1e400` | `2e400` | equal (both beyond a double, read as infinity, with a warning) |
| `9007199254740993` | `9007199254740992.0` | changed (integers are read exactly) |
| `[1, 2]` | `[2, 1]` | changed (arrays keep their order) |
| `{"a": 1, "b": 2}` | `{"b": 2, "a": 1}` | equal (object members have no order) |

Integers (numbers without a fraction or exponent) are read exactly, however long, up to
Python's digit limit; only numbers with a fraction or an exponent are read as doubles, and only
they can overflow to infinity and get the range warning.

Only the top-level keys are listed. Inside a changed key, the diff block shows every line that
differs, however deep.

## Warnings

RFC 8259 does not allow `NaN`, `Infinity` and `-Infinity` (section 6) and says object names
SHOULD be unique (section 4). Python's reader accepts all of them, so `jpd` still compares
such files, and says so:

```text
Warning: data.json holds values RFC 8259 does not allow (section 6), read and compared as numbers: NaN
Warning: data.json holds numbers beyond the range of a double, read and compared as infinity: 1e400
Warning: data.json repeats names inside an object, the last value is used (RFC 8259 section 4): "id"
```

At most five examples are named per line, then `and N more`; long names are cut at 40
characters. The same lines appear in the Warnings section of the report. `-q` silences the
stderr lines but not the section. Warnings never change the exit code.

## Command line

```text
jpd SOURCE TARGET [-o REPORT] [--open] [-q] [--no-style] [--no-timestamp]
```

| Option | Effect |
| --- | --- |
| `-o, --output` | Write the report to this file (folders are created). Without it the report goes to standard output. |
| `--open` | Open the written report in the default browser; needs `-o`. |
| `-q, --quiet` | Print nothing but errors. |
| `--no-style` | Leave the stylesheet out. |
| `--no-timestamp` | Leave the generation time out, so the same inputs give the same file. |
| `--version` | Print `jpd <version>`. |

Exit codes: `0` no differences, `1` differences, `2` error (with an `Error: ...` line on
stderr and no report). With `-o`, a status line such as
`Report saved to diff.html (2 added, 1 removed, 5 changed)` goes to standard output.

Output details:

- The report is UTF-8 everywhere, including a redirected standard output on Windows.
- When the reader of the standard output stops early (`jpd a.json b.json | head`), `jpd`
  stops writing without a message and exits with 0 or 1 as usual.
- A UTF-8 byte order mark at the start of an input is accepted; UTF-16 input is refused with
  a hint.
- Errors that end with exit 2: no standard output to write the report to, a missing or
  unreadable file, a directory, text that is not UTF-8, invalid JSON, a root that is not an
  object, an integer longer than Python's digit limit (4,300 digits on current Pythons), a
  document nested too deeply for the report, a report path that cannot be written.

## From Python

The names in `json_pretty_diff.__all__` are the public API.

```python
from json_pretty_diff import compute_top_level_diff, render_html

old = {"name": "demo", "version": 1, "tags": ["a"]}
new = {"name": "demo", "version": 2, "owner": "me"}
diff = compute_top_level_diff(old, new)
assert diff.added == ["owner"] and diff.removed == ["tags"]
assert diff.changed == {"version": {"old": 1, "new": 2}}
page = render_html(diff, include_timestamp=False, warnings=["checked by hand"])
assert "<h2>Warnings</h2>" in page and "Generated on" not in page
```

`compute_top_level_diff(source, target)` takes two mappings (anything else raises `TypeError`)
and returns a `DiffResult`, a frozen dataclass whose lists and dicts can still be changed in
place, with sorted `added` and `removed` key lists, `changed` mapping each changed key to its `old` and `new` value, the
values of the added and removed keys, and copies of both documents. `render_html(diff, *,
include_styles=True, include_timestamp=True, warnings=())` returns the page as a string.
`JsonPrettyDiffCLI().run(argv)` runs the command line and returns 0 or 1; errors, `--help` and
`--version` raise `SystemExit` with their code, as the script does. `main()` is the `jpd`
script. Documents nested deeper than about half of Python's recursion limit (about 500
levels by default) raise `RecursionError` when the snapshots are copied; keys must be strings
and `warnings` a sequence of strings, or `TypeError` is raised.

## Large and repetitive input

Line matching uses Python's `difflib`, whose running time can grow with the square of the
input on some shapes (long arrays of repeated values). `jpd` counts the work and, past a fixed
budget (10 million steps of its inner loop, a few seconds at most), shows the part between the
lines both sides share at the start and at the end as one replacement. Below the budget, the diff is exactly `difflib`'s.

## Upgrading from 1.1.1

Nothing to change in scripts: options, exit codes and imports are the same. What you may
notice is listed in the
[CHANGELOG](https://github.com/JaviLianes8/json-pretty-diff/blob/main/CHANGELOG.md): `true`
against `1` now counts as a change and `NaN` against `NaN` does not, warnings on stderr for
non-standard input, a hyphen in the header line, icons inside the page, no empty rows in the
diff blocks, and a quiet exit when a pipe closes.
