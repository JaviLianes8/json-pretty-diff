# json-pretty-diff improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [ ] Pin the ground truth: RFC 8259
- [ ] Comparison: booleans versus numbers, NaN against itself
- [ ] Report: unique section anchors, unencodable characters
- [ ] Command line: Python 3.9 import, stdout encoding, read and write errors, byte order mark, deep nesting
- [ ] Tests and coverage, contracts, pinned sources
- [ ] Typing: mypy --strict, py.typed
- [ ] Docs: README factual fixes, CHANGELOG
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest on 3.8 to 3.14
- [ ] Mutation run
- [ ] Independent review findings fixed
- [ ] Pull request opened, guard clean

Every change keeps the public surface: the `jpd` script and its options (`-o/--output`,
`--open`, `-q/--quiet`, `--no-style`, `--version`), the exit codes 0, 1 and 2, the HTML
report layout, `JsonPrettyDiffCLI`, `DiffUseCase`, `compute_top_level_diff`, `DiffResult`
and `render_html`. Fixes and additions only; anything that would change what existing users
see for input that works today is listed under Proposals for the owner.

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

## Proposals for the owner

(filled in as the round goes)
