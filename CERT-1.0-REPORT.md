# json-pretty-diff 1.2.0 certification report

The 1.0.0 certification bar (`CERT-1.0.md`, 19 items) applied to the 1.2.0 release.

Progress:
- [x] Branch `release/1.2.0` created from `main` (1.1.1 plus the merged improvement round)
- [x] Browser check of the diff rows in headless Chrome (blank rows confirmed, then fixed)
- [x] Owner decisions implemented: warnings, header hyphen, inline icons, `--no-timestamp`,
      diff rows, quiet broken pipe, public names at the top level
- [x] Tests: contracts, golden edit from 1.1.1, warnings, pipes, fuzz, bounded matching (items 6, 9)
- [x] Docs: README additions, GUIDE, CHANGELOG 1.2.0 (items 11, 12)
- [x] Gates on every interpreter of this PC (items 10, 15)
- [x] Packaging, wheel e2e and upgrade from PyPI 1.1.1 (items 8, 13, 14)
- [x] Author mutation round (item 18): 46 mutants, 41 killed, 5 killed by new contracts
- [x] Five QA lenses PASS (item 19)
- [ ] Independent scorecard (item 16)
- [ ] PR and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: 6 names plus `__version__` at the top level, every 1.1.1 import path kept, new options keyword-only with defaults, every change in CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: 7 module doctests run by `pytest`; README and GUIDE examples run as tests |
| 4 | Typed end to end | PASS: `mypy --strict` over src, tests, scripts; `py.typed` shipped |
| 5 | Typed, documented, bounded errors | PASS: `TypeError` naming the bad argument; CLI errors `Error: ...` exit 2; paths cut at 1,000 characters, names at 40 |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: RFC 8259 fetched live (`tests/upstream/MANIFEST.json`, sha256 checked); the 1.1.1 reports in `tests/golden/` come from the untouched 1.1.1 code; PyPI 1.1.1 as an oracle |
| 8 | Real e2e from the wheel | PASS: wheel in fresh venvs, `jpd` by subprocess, upgrade in place from PyPI 1.1.1 |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS: seeded tests in `tests/test_fuzz.py`; line matching bounded (see below) |
| 10 | Supported Pythons | PASS: CPython 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 and 3.14 free-threaded |
| 11 | README and `twine check` | PASS: `twine check --strict` on both artifacts |
| 12 | Dated CHANGELOG section | PASS: 1.2.0, 2026-10-15 |
| 13 | pyproject 1.2.0, Production/Stable | PASS: SPDX `MIT`, classifiers 3.9 to 3.14, `Typing :: Typed`, Source, Issues, Changelog URLs, no runtime dependency |
| 14 | sdist and wheel contents | PASS: 26-module wheel with `py.typed` and LICENSE; sdist with the full runnable test suite, docs, no notes or caches |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent scorecard | pending |
| 17 | PR and trace guard | pending |
| 18 | Contracts bite (mutations) | PASS: see Mutation rounds |
| 19 | Five independent QA lenses | PASS: see QA lenses |

## Starting point

PyPI 1.1.1 and `main` after the improvement round (`IMPROVEMENTS-round.md`). The owner chose
the 1.2.0 behaviour: keep the three behaviour changes of the round (`true` against `1` differs,
`NaN` equals itself, UTF-8 on stdout); `1` and `1.0` stay equal; NaN and Infinity accepted with
a warning; repeated names reported; blank rows checked in a browser and fixed; hyphen in the
header; icons inside the page; an option to leave the time out; long integers, deep nesting
and double precision as they are; a closed output pipe ends quietly.

Headless Chrome (playwright-core driving Chrome 155) measured the 1.1.1 report: an 18 pixel
empty row between every pair of diff rows with styles, and an extra row inside multi-line
values without styles; the three header icons failed to load offline. The same measurement
on 1.2.0: no gap between rows in either mode, three `data:` images, no network request.

## Behaviour changes against PyPI 1.1.1

Listed in full in CHANGELOG 1.2.0. In short: `true`/`false` against numbers differ, `NaN`
equals `NaN`; stdout always UTF-8; warnings on stderr and in the report for `NaN`/`Infinity`,
numbers beyond a double and repeated names; `--no-timestamp`; hyphen in the header line;
embedded icons; one `<span>` per diff row with no empty rows; a closed pipe exits 0 or 1
quietly, other stdout failures and a missing stdout exit 2; line matching bounded by a work
budget; control characters in names escaped; search highlight on the text itself; strings
with U+2028, U+2029 or U+0085 kept on one row; a byte order mark accepted; tracebacks replaced
by `Error: ...` and exit 2; top-level imports; `TypeError` for non-mapping input, non-string
keys and non-string warnings; cyclic Python structures compared instead of raising.

The golden test edits each 1.1.1 report with exactly these page changes (hyphen, icons, diff
rows, search function) and requires the 1.2.0 report to be byte for byte the result.

## Gates (item 15), final run at fde6cc6

From a fresh clone, each command on its own: `ruff format --check .`, `ruff check .`,
`mypy --strict` and `pytest` (doctests included: 273 passed, 1 skipped) exit 0. The installed-wheel e2e test
(`JSON_PRETTY_DIFF_E2E=1`) passes. The suite run from the extracted sdist, with `src` removed so
it imports the installed wheel, passes on CPython 3.9.25, 3.10.19, 3.11.5, 3.12.12, 3.13.2,
3.14.2 and 3.14.2 free-threaded: 266 passed on each, one skip each (the opt-in e2e test).

## Bounded line matching (item 9)

`difflib.SequenceMatcher` took about two minutes in 1.1.1 on an array of 16,000 values
repeating 150 numbers. The matcher counts the steps of `difflib`'s inner loop and, past 10
million, shows the differing middle as one replacement. Below the budget the output equals
`difflib`'s (checked on thousands of random inputs); a shuffled array of 100,000 numbers needs
about 5 million steps and keeps `difflib`'s exact result. Measured shapes up to 1.6 million
lines grow linearly.

## Mutation rounds (item 18)

Author round at 924fe9f: each mutant applied alone to a fresh clone, `pytest -x` with no
bytecode, a 900 second limit, baseline green before and after. 46 mutants, 41 killed at once;
the 5 survivors (M08, M18, M29, M34, M46) got contracts in 5c8214c and each was confirmed to
die.

| Mutant | Change | Killed by |
| --- | --- | --- |
| M01 | NaN/Infinity not recorded | test_docs.py::test_the_warning_lines_in_the_guide_are_what_jpd_prints |
| M02 | overflow test wrong | test_docs.py::test_the_warning_lines_in_the_guide_are_what_jpd_prints |
| M03 | duplicates never checked | test_docs.py::test_the_warning_lines_in_the_guide_are_what_jpd_prints |
| M04 | examples cap off by one | test_warnings.py::test_five_examples_are_shown_and_the_rest_counted |
| M05 | quote cap off by one | test_warnings.py::test_a_number_beyond_a_double_is_infinity_with_a_note |
| M06 | more count off by one | test_docs.py::test_the_warning_lines_in_the_guide_are_what_jpd_prints |
| M07 | first value kept | test_sources.py::test_object_names_should_be_unique_and_the_last_one_is_read |
| M08 | names escaped to ASCII | survived round 1; killed by test_warnings.py::test_names_keep_their_characters_in_the_message |
| M09 | Infinity read as NaN | test_warnings.py::test_nan_and_infinities_are_read_as_floats_and_named_once_in_order |
| M10 | overflow note inverted | test_cli.py::test_unwritable_output_is_an_error |
| M11 | path prefix dropped | test_docs.py::test_the_warning_lines_in_the_guide_are_what_jpd_prints |
| M12 | same file warns twice | test_docs.py::test_the_warning_lines_in_the_guide_are_what_jpd_prints |
| M13 | quiet does not silence warnings | test_sources.py::test_object_names_should_be_unique_and_the_last_one_is_read |
| M14 | --no-timestamp ignored | test_output.py::test_no_timestamp_gives_the_same_bytes_every_time |
| M15 | warnings not in the report | test_warnings.py::test_the_command_prints_warnings_and_keeps_the_exit_code |
| M16 | Windows closed pipe is an error | test_output.py::test_a_closed_pipe_is_not_an_error |
| M17 | reader gone reported as written | test_output.py::test_a_closed_pipe_is_not_an_error |
| M18 | stdout not redirected after a closed pipe | survived round 1; killed by test_output.py::test_a_status_line_to_a_closed_pipe_leaves_nothing_for_the_exit_flush |
| M19 | closed stderr raises | test_output.py::test_a_closed_stderr_is_ignored |
| M20 | stdout error message | test_output.py::test_other_write_failures_are_errors |
| M21 | status line unguarded | test_output.py::test_status_line_to_a_closed_pipe_keeps_the_exit_code |
| M22 | closed pipe exits 2 | test_output.py::test_a_closed_pipe_is_not_an_error |
| M23 | header dash back | test_render.py::test_report_differs_from_version_1_1_1_only_as_documented |
| M24 | no-timestamp header text | test_output.py::test_no_timestamp_gives_the_same_bytes_every_time |
| M25 | warnings section dropped | test_docs.py::test_python_examples_run |
| M26 | warnings unescaped | test_warnings.py::test_warning_section_is_escaped_and_absent_without_warnings |
| M27 | inline style without styles | test_warnings.py::test_warning_section_is_escaped_and_absent_without_warnings |
| M28 | timestamp default flipped | test_contract.py::test_function_signatures_are_unchanged |
| M29 | wrong icon | survived round 1; killed by test_render.py::test_the_report_loads_nothing_from_the_network |
| M30 | icon from network | test_render.py::test_the_report_loads_nothing_from_the_network |
| M31 | row break dropped | test_render.py::test_report_differs_from_version_1_1_1_only_as_documented |
| M32 | rows joined with newline | test_render.py::test_report_differs_from_version_1_1_1_only_as_documented |
| M33 | keeps trailing break | test_render.py::test_report_differs_from_version_1_1_1_only_as_documented |
| M34 | truncated row break | survived round 1; killed by test_render.py::test_diff_lines_get_a_class_by_their_prefix |
| M35 | budget never spent | test_matching.py::test_past_the_budget_the_middle_is_replaced_and_the_text_rebuilds |
| M36 | suffix overlaps prefix | test_matching.py::test_past_the_budget_the_middle_is_replaced_and_the_text_rebuilds |
| M37 | empty hunk range | test_matching.py::test_below_the_budget_the_result_is_difflibs |
| M38 | context lines | test_matching.py::test_below_the_budget_the_result_is_difflibs |
| M39 | delete tagged insert | test_matching.py::test_plain_opcodes_keep_the_shared_start_and_end |
| M40 | positions not counted | test_matching.py::test_shuffled_and_repetitive_arrays_render_in_bounded_time |
| M41 | bool equals number | test_decisions.py::test_values_compare_as_documented |
| M42 | NaN differs from NaN | test_decisions.py::test_values_compare_as_documented |
| M43 | byte order mark refused | test_cli.py::test_byte_order_mark_is_accepted |
| M44 | render_html not exported | test_contract.py::test_package_exports_exactly_the_public_names |
| M45 | old and new swapped | test_docs.py::test_python_examples_run |
| M46 | pipe error at exit flush | survived round 1; killed by test_output.py::test_a_status_line_to_a_closed_pipe_leaves_nothing_for_the_exit_flush |

## QA lenses (item 19)

Five independent reviews, one at a time, each reading the certification rules, running the
code and reporting only to the maintainer. Bounded later rounds confirm the earlier findings.

| Lens | Round | Head | Verdict | Findings and outcome |
| --- | --- | --- | --- | --- |
| a. API and docs | 1 | ea9922b | FAIL | no stdout ended in a traceback with exit 1; GUIDE wording on `run`, `DiffResult`, README example paths; untyped errors for bad input; `Dict` instead of `Mapping`; `main` example; fixed in 02068e1 |
| a | 2 | 02068e1 | PASS | all eight items confirmed |
| b. Correctness and ground truth | 1 | 02068e1 | PASS (4 minor) | 4,000 seeded pairs against an independent parser and equality oracle, 4,215 diff blocks and 4,000 tables rebuilt, warnings exact, 318 differences from 1.1.1 all documented; minor: budget wording and a case it cut too early, exact integers undocumented, U+2028 family split rows, CHANGELOG layout; fixed in ea78120 and 46545a1 |
| b | 2 | ea78120 | PASS | fixes confirmed, 500 fresh pairs, 0 failures |
| c. Adversarial and robustness | 1 | 46545a1 | FAIL | cyclic Python structures never returned; minor: depth wording, raw control characters, long paths echoed, search highlight offset, UTF-32 hint, unclear type errors; fixed in b362db4, afc3274, 7b6cb9c |
| c | 2 | afc3274 | PASS | fixes confirmed; injection set, 840 fuzz runs, no regression |
| d. Packaging and real e2e | 1 | 7b6cb9c | PASS (1 minor) | wheel and sdist contents, metadata, 27 CLI cases from the wheel, upgrade from PyPI 1.1.1, sdist install, suite on seven interpreters; minor: CONTRIBUTING named two files missing from the sdist, fixed in c424db8 |
| e. Contract strength (blind) | 1 | c424db8 | PASS with its contracts | 237 mutants, 209 killed, 6 equivalent (constant labels, unreachable branches, anchors that need no escaping), 22 needing contracts, added in a4918a7 |
| e | 2 | a4918a7 | PASS | all 22 killed by the committed suite |
