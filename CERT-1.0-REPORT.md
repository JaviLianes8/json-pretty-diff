# json-pretty-diff 1.2.0 certification report

The 1.0.0 certification bar applied to the 1.2.0 release (read "1.0.0" as "1.2.0").

Progress:
- [x] Branch `release/1.2.0` created from `main` (1.1.1 plus the merged improvement round)
- [x] Browser check of the diff rows in headless Chrome (blank rows confirmed)
- [x] Owner decisions implemented: warnings, header hyphen, inline icons, `--no-timestamp`,
      diff rows, quiet broken pipe, public names at the top level
- [x] Tests: contracts, golden transform from 1.1.1, warnings, pipe, fuzz, bounded matching (items 6, 9)
- [x] Docs: README additions, GUIDE, CHANGELOG 1.2.0 (items 11, 12)
- [ ] Gates on every interpreter of this PC (items 10, 15)
- [ ] Packaging, wheel e2e and upgrade from PyPI 1.1.1 (items 8, 13, 14)
- [x] Author mutation round 1 (item 18): 46 mutants, 41 killed, 5 survivors killed by new contracts in 5c8214c (confirmed)
- [ ] Five QA lenses PASS, independent review (items 16, 19)
- [ ] PR and trace guard CLEAN (item 17); merge and publish left to the maintainer
