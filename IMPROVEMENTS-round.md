# json-pretty-diff improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: RFC 8259
- [x] Comparison: booleans versus numbers, NaN against itself
- [x] Report: unique section anchors, unencodable characters
- [x] Command line: Python 3.9 import, stdout encoding, read and write errors, byte order mark, deep nesting
- [x] Tests and coverage, contracts, pinned sources
- [x] Typing: mypy --strict, py.typed
- [x] Docs: README factual fixes, CHANGELOG
- [x] Gates: ruff format, ruff check, mypy --strict, pytest on 3.8 to 3.14
- [x] Mutation run
- [x] Independent review findings fixed
- [x] Pull request opened (#21), checks clean

Every change keeps the public surface: the `jpd` script and its options (`-o/--output`,
`--open`, `-q/--quiet`, `--no-style`, `--version`), the exit codes 0, 1 and 2, the HTML
report layout, `JsonPrettyDiffCLI`, `DiffUseCase`, `compute_top_level_diff`, `DiffResult`
and `render_html`. Fixes and additions only; anything that would change what existing users
see for input that works today is listed under Proposals.

## Starting point

`1.1.1` (the PyPI sdist has the same source as `main`) has no tests. Probed with small files
on CPython 3.13, 3.9 and 3.8 on Windows:

- The package does not import on Python 3.9, although `requires-python` and the README say
  3.9: `infrastructure/cli.py` writes `Sequence[str] | None` in a signature without postponed
  annotations.
- Without `-o`, the report goes to stdout through the console encoding. When the output is
  redirected (`jpd a.json b.json > diff.html`, the way the help text suggests) on a Windows
  code page, every run crashes on the first non-ASCII character of the page (the `−` toggle
  glyph, the heart, the author's name).
- `{"a": true}` against `{"a": 1}` and `[false]` against `[0]` are reported as "no
  differences" with exit code 0, because Python compares `True == 1`. RFC 8259 keeps
  `true`, `false` and numbers as distinct value types.
- A file with `NaN` in it compared with itself reports a change (exit code 1), because NaN is
  never equal to itself in Python.
- Section anchors are not unique when a key already looks like a generated suffix: keys
  `a b`, `a-b` and `a-b-2` give two sections with `id="diff-a-b-2"`, so a summary link jumps
  to the wrong key.
- Invalid UTF-8, a directory or an unreadable path as input, a directory as `-o`, an integer
  longer than Python's digit limit, nesting deeper than the parser or the snapshot copy can
  follow, and a lone surrogate escape (`"\ud800"`) all end in a Python traceback (exit 1, as if
  differences had been found) instead of the documented `Error:` line and exit code 2.
- A UTF-8 byte order mark makes the file "Invalid JSON". RFC 8259 section 8.1 lets a parser
  ignore it.

## Sources

- RFC 8259, https://www.rfc-editor.org/rfc/rfc8259.txt: value types (section 3), unique
  object names (4), numbers without NaN or Infinity (6), strings and unpaired surrogates (7,
  8.2), UTF-8 and the byte order mark (8.1), the examples (13).
- RFC 6901 and RFC 6902 do not apply: the report names top-level keys only, never a pointer
  or a patch.
- The file is not committed. `tests/upstream/MANIFEST.json` records URL, revision, size,
  sha256 and licence; `scripts/fetch_upstream.py` fetches and checks it into the ignored
  `tests/upstream/` folder; the tests that read it skip while it is absent.

## Ranked improvements

1. **Runs on what it declares.** Postponed annotations in the CLI module; tested on 3.9 to
   3.14 (and 3.8, which also works but is not declared).
2. **Redirected stdout works everywhere.** The report is written as UTF-8 (what its
   `<meta charset>` says) whatever the console code page is.
3. **Compare JSON values as JSON.** A boolean never equals a number, at any depth; NaN equals
   NaN. Everything else compares as before (`1` and `1.0` stay equal).
4. **Unique anchors.** A generated anchor never repeats an earlier one; anchors for keys that
   did not collide are unchanged.
5. **Documented errors instead of tracebacks.** Every input or output problem prints
   `Error: ...` and exits 2. A byte order mark is accepted. Characters that cannot be encoded
   (lone surrogates) are written as `\udXXX` instead of crashing.
6. **Tests, typing, gates.** Behaviour tests per module and per bug, contract tests for the
   public surface, pinned-source tests against RFC 8259, `mypy --strict`, ruff, a local gate
   script, a mutation run.

## Out of scope

- Recursive diffing, exclusions or new CLI options (the README lists them as limitations).
- Any change to the HTML layout, styles, texts or the timestamp line.

## Verification

- Gates from a fresh clone of the branch, after the fetch script had fetched RFC 8259 and
  matched the manifest: `ruff format --check .`, `ruff check .`, `mypy --strict` and `pytest`
  exit 0 on CPython 3.14. With `JSON_PRETTY_DIFF_E2E=1` the installed-wheel test builds the
  wheel and sdist, checks their contents (`py.typed` and the new private modules in the wheel,
  no fetched file and no planning notes in the sdist), installs the wheel in a fresh venv and
  drives the `jpd` script from an empty folder. The suite also passes on CPython 3.8, 3.9,
  3.10, 3.11, 3.12 and 3.13.
- The HTML report is pinned byte for byte: `tests/golden/` holds three reports rendered by the
  untouched 1.1.1 code (with styles, without styles, no differences), only the generation
  time masked, and the branch renders them identically.
- Line and branch coverage of the package is 99% after the review fixes; what is left is
  two unreachable guards in the truncation panel code.
- RFC 8259 (section 3 value grammar, section 4 unique names, section 8.1 UTF-8 and the byte
  order mark, the section 13 examples cut out of the fetched text) is read in
  `tests/test_sources.py`.
- Mutation run from a clean clone, without bytecode and with a timeout per mutant, the suite
  green before: 52 hand-placed mutants over the comparison, anchors, file input and output,
  the command line and the main renderer branches. First run: 3 alive (the anchor loop
  reduced to a single retry, `@` instead of `@@` for hunk headers, a truncated new value
  alone); a test was added for each. Second run: 52 killed, 0 alive. Third run, after the
  review fixes rewrote the comparison and the error paths: 59 mutants, 1 alive (the generic
  read error, no longer reached by the directory test); a test was added and checked to fail
  with that mutant.

## Behaviour changes to confirm

These fixes change the result for input that ran without an error in 1.1.1, so they
should be confirmed before a release. Each is small to revert: one branch in
`domain/_equality.py` for the first two, one call in `infrastructure/_io.py` for the third.

- `true` against `1` (or `false` against `0`) now counts as a change: exit 0 becomes exit 1
  and the summary lists the key. RFC 8259 section 3 keeps them as different value types.
- `NaN` against `NaN` no longer counts as a change: exit 1 becomes exit 0. `NaN` is not JSON
  (RFC 8259 section 6); a file compared with itself reporting a change was the bug.
- A report on stdout is always UTF-8. Before, a console set to another encoding with an
  error handler (`PYTHONIOENCODING=cp1252:replace`) got that encoding, which contradicts the
  page's `<meta charset="utf-8">`.

## Review fixes

An independent review compared the branch with 1.1.1 on 30 input pairs in five output
modes (identical bytes, messages and exit codes for every input that worked before, except
the intended fixes) and attacked the fixes. Fixed, each with a test:

- The first version of the JSON comparison recursed with about three stack frames per
  nesting level, so on Python 3.10 and 3.11 a shared key nested 400 levels deep, which 1.1.1
  compares, became "nested too deeply" (exit 2). The comparison now walks its own stack;
  `tests/test_cli_process.py` compares a key 450 levels deep in a fresh interpreter and
  expects exit 1 (it fails on the recursive version). The walk takes about a second for
  300,000 records, less than one of the two snapshot copies 1.1.1 already makes.
- The deep-document test accepted exit 1 or 2 and ran inside pytest's stack; it now runs in
  a fresh interpreter and expects exactly exit 2 with an `Error:` line.
- A directory given as input or as `-o` said "Permission denied" on Windows; it now says
  "it is a directory".
- A UTF-16 file (what Windows PowerShell 5 writes with `>`) gets "(it looks like UTF-16)"
  after "not UTF-8 text"; an integer beyond Python's digit limit says so in plain words
  instead of repeating the interpreter's advice.
- Ruff targets Python 3.9, the declared floor. mypy 2.4 cannot target below 3.10; the code
  uses postponed annotations throughout and the suite runs on 3.8 and 3.9.
- A redundant flush before switching the stream back was removed.

Left as written: the README example paths (`fixtures/base.json`) are an illustration of the
user's own files, not a claim about the repository.

## Proposals

These would change what existing users see for input that works today, or are design
choices, so they are not in the code. Each is a suggestion, ranked by how often it should
bite.

1. **`1` and `1.0` are equal.** The comparison keeps Python's numeric equality, so a number
   that changes from `1` to `1.0` is not reported, although the "Full JSON" table shows the
   two texts. A strict mode would report it.
2. **NaN, Infinity and huge exponents.** Python's reader accepts `NaN`, `Infinity` and
   `-Infinity`, which RFC 8259 section 6 does not allow, and reads `1e400` as infinity, so
   `1e400` against `2e400` is "no differences". Rejecting the non-standard tokens with exit 2,
   or comparing numbers by their text, would make both visible.
3. **Duplicate object names.** `{"a": 1, "a": 2}` is read as `{"a": 2}` without a word;
   RFC 8259 section 4 says names SHOULD be unique. A warning on stderr would help.
4. **Blank lines in the diff blocks.** Each diff line keeps its trailing newline inside a
   block `<span>` in a `<pre>`, and the spans are also joined by newlines, so browsers may
   show an empty line between diff lines. Worth a look in the browser before touching it,
   since the layout is pinned.
5. **The dash in the header.** "Generated on ... &mdash; v1.1.1" renders an em dash; the rest
   of the catalogue avoids that character. A colon or a middle dot would do.
6. **External icons.** The branding header loads its three icons from jsdelivr and
   simpleicons, so a report opened offline shows broken images and opening it contacts two
   CDNs. Inline SVGs would make the file self-contained.
7. **Reproducible reports.** The generation time makes two runs on the same input differ; an
   option (or `SOURCE_DATE_EPOCH`) to fix it would let users keep reports under version
   control.
8. **Integers longer than 4300 digits.** Python 3.11 and later (and security releases of
   3.8 to 3.10) refuse them; they now give a clear exit 2. Raising the limit while reading
   would accept them.
9. **Very deep documents.** Documents that parse but are too deep for the snapshot copy or
   the serializer now give a clear exit 2; an iterative copy would accept them.
10. **Release.** All changes are fixes or additions; suggest releasing them as 1.1.2 (or
    1.2.0 for the byte order mark and `py.typed`). The version was not changed. Classifiers
    for the supported Python versions and `Typing :: Typed` could be added at the same time.
11. **Decimal precision.** `0.1` against `0.10000000000000001`, or `1` against
    `1.0000000000000001`, read as the same float and give "no differences". Reading floats
    as `Decimal`, or comparing number texts, would show them.
12. **Broken pipe.** `jpd a.json b.json | head -c 20` ends in a `BrokenPipeError`
    traceback and exit 1 (unchanged from 1.1.1). Leaving quietly would be friendlier; the
    exit code to use is a design choice.
