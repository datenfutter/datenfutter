# Datenfutter completion plan

Updated 19 November 2026, Asia/Shanghai. This file on GitHub is the authoritative execution record. Update it in each task commit. Drive's plan becomes a pointer here.

## Goal

Finish with one remote branch, `main`; one current output set per retained topic/language/post; and one current delivery view in Drive. Every retained final must reproduce from original evidence in a clean checkout with networking disabled. Preserve source evidence and ordinary Git history. Remove verified superseded plot derivatives, not unique research.

## Verified starting checkpoint

- Public main: `036879e4113eb5a4a85550d326ee81c1b2b66052`; [main CI](https://github.com/datenfutter/datenfutter/actions/runs/44514146361) passed 84 tests. Zero production projects are integrated at this baseline.
- The recovered fuel pilot passed 103 tests. All 24 CSVs, one validation report and two nine-file German posts reproduce locally. Original receipt verification and canonical layout pass. These are local results until remote integration is recorded below.
- All 108 final candidate paths match their enumerated sizes/hashes. The durable recovery checkpoint and complete Git history were verified. Private recovery locations are excluded from this public plan.
- Nine remote branches remain: main plus eight integrated branches. The connector lacks delete-ref and this environment lacks authenticated Git CLI access. No canceled sign-in retry.
- Drive retains older plot revisions, exports and packages. Later-topic migration, current delivery and cleanup remain pending.

## Task protocol

1. Read this ledger and the next task. Re-read remote heads; require a clean local worktree. Reuse verified implementation rather than recreating retired draft interfaces.
2. Change only the task's stated paths or enumerated import set. One purpose per commit. Changed behavior requires a failing regression before the fix. Verified imports, documentation and output promotion use direct integrity checks.
3. Run the exact acceptance command, inspect exit status and test count. Zero tests never satisfy a gate. Behavior changes run the full suite; shared changes rebuild every migrated final.
4. Review the full diff, staged paths and outgoing history. Commit task plus PLAN status; push normally; verify the exact remote SHA and its CI. Integrate only passing changes and verify main's own CI.
5. Record the previous task's integration SHA/CI in the next task commit. A task may record its own remote gate as pending until the next update. Do not create recursive status commits just to embed their own hashes. Final reconciliation closes the last references.
6. Keep failures on the same task. Do not weaken comparisons, replace approved references or change vintages to conceal failure. Independent work may continue.
7. Keep one active staging ref. While deletion is unavailable, reuse integrated `task/c03-public-status`, starting each task from verified main. No stacked branches, history rewriting or force-push. Delete the staging ref at closure when supported.

States: pending, local-pass, remote-pass, integrated, delivered, blocked. Each record contains scope, command/result, commit/CI and remaining gate. Private destination IDs and recovery metadata remain in existing private operational records.

## Structure and invariants

| Path | Role |
| --- | --- |
| `datenfutter/`, `brand/` | Shared renderer, CLI and visual configuration |
| `projects/<topic>/README.md`, `prepare.py` | Scope, selected methodology, offline preparation |
| `projects/<topic>/sources/` | Original raw responses/receipts and current selection |
| `projects/<topic>/data/processed/` | One current derived-data set |
| `projects/<topic>/specs/<language>/<post>.json` | Current specification |
| `projects/<topic>/posts/<language>/<post>/` | Numbered PNG/SVG pairs, caption, alt text, manifest |
| `projects/<topic>/review.json` | Exact review state and hashes |
| Ignored `build/` | Disposable previews and exports |

Discover projects/posts from specs. Separate acquisition from preparation. Preserve both fuel receipt logs and all 49 original raw paths, including older/failed attempts and actual retrieval timestamps. Preserve frozen selection, units/currencies and numerical guards. Tests do not imply editorial approval, delivery or social publication.

Keep 1080x1350; cream #FAF8EF; navy #1C2D57 accents; black text; DejaVu Sans; circle-only df logo; approved A/B/C palettes; bold pagination; one descriptive block; localized lower-left date; complete literal source URLs in captions. Social publication and sharing changes are outside scope.

## Ordered atomic tasks

### T00 — Publish this authoritative plan

Scope: PLAN only. Correct retired commands; distinguish local/integrated work; state small tasks and actual blockers. Gate: entire-document/publication review, `git diff --check`, `python -m datenfutter layout`, task CI, main CI.

### C01 — Delete integrated remote branches

Independent of fuel publication. Each row is a separate operation.

| Subtask | Branch | Expected tip |
| --- | --- | --- |
| C01a | `refactor/current-state` | `0d742590c4123d34b5acee4bbc4a596d50cd059f` |
| C01b | `fix/deterministic-svg` | `7a598899d7e5f294cee524998352f32ee587db84` |
| C01c | `fix/deterministic-manifests` | `f62a21a5ed2586c6a38f3c79c3579e0a0876e2c8` |
| C01d | `build/preparation-dependencies` | `d2b4aa8827e323773e2953caa1892690bbb1b81c` |
| C01e | `feat/project-build` | `b416fcef216115d0625222af5f03c8acc55d4b10` |
| C01f | `feat/project-check` | `1a89cf0290adebf19b4d292bd5bed716f87f126f` |
| C01g | `feat/canonical-layout` | `b75c814ed58987f2b2d81fc0f49dbd5fce71cc26` |
| C01h | `task/c03-public-status` | Read fresh at final closure; reused during execution |

Re-read main, branch tip and PRs before each deletion; prove ancestry. Reassess moved tips. Require supported deletion conditional on the expected tip, then confirm ref absence and intact main. Retain unintegrated or safely undeletable refs.

### C02 — Account for recovery

The preserved checkpoint/history is verified. Original unavailable worktrees are not presumed deleted/integrated. Record their disposition without deleting unavailable work. Resume recovered implementation rather than repeating recovery.

### I03 — Import original evidence and frozen selection guards

Prerequisite: T00 and public-write approval for the exact payload. Scope: fuel sources (49 raw paths, both original logs, register), project README, `verify_sources.py`, `tests/test_fuel_sources.py`, PLAN. Publishes original source responses and unchanged retrieval metadata; excludes private recovery/delivery locators.

Gate: 26+23 original receipts and raw hashes/sizes match; selected cards match frozen receipts; corrupt, missing, rewritten and wrong-vintage evidence fails. Run `python -m unittest discover -s tests -p 'test_fuel_sources.py' -v`, full suite, source verifier and layout. Review every imported path.

### I04 — Import selected tables and specifications

Prerequisite: I03 integrated. Scope: exactly 24 CSVs and two German specs, README/PLAN. Build both previews from saved tables with `python -m datenfutter build fuel-prices-de-ch-lu`. Compare six PNGs/four text files to the verified reference; this is rendering, not raw reproduction.

### P07 — Integrate recovered offline preparation

Prerequisite: I04 integrated. Scope: existing fuel `prepare.py`, validation report, `tests/test_fuel_preparation.py`, README/PLAN. Reuse `read_prices`, `index_monthly`, `decompose`, `prepare`; draft loader interfaces are retired.

Gate: all 24 CSVs reproduce from original raw bytes; six series x 94 months and twelve baseline months each; missing/duplicate months, currency errors and inconsistent tax components fail. Run preparation tests, full suite and build. Verify exact bytes and input preservation in a disposable copy without saved processed tables. Do not rewrite proven implementation solely to manufacture commits; defects get separate tasks.

### O01 — Retain German petrol

Prerequisite: P07 integrated. Scope: petrol's nine managed files, review record, README/PLAN. Rebuild previews; compare full petrol file set/bytes; inspect three slides full-size/phone-size and complete caption/alt text. Preserve actual internally-checked/preview/not-published state.

### O02 — Retain German diesel

Prerequisite: O01 integrated. Scope: diesel's nine files, review record, README/PLAN. Same inspection. Then `python -m datenfutter check fuel-prices-de-ch-lu`; require exactly 18 managed outputs and layout of one project/two current posts. Checks leave originals unchanged.

### V01 — Integrate raw-only production verification

Prerequisite: O02 integrated. Scope: `scripts/check_production.py`, `tests/test_production.py`, README/PLAN. Use reviewed-post records and spec discovery; no second output inventory.

Gate: disposable preparation excludes saved processed files; compares every prepared file/current output; rejects empty/shrunken reviewed selection and input mutation. Verify no-op preparation and missing/extra/changed table cases; add missing acceptance cases as bounded tests. Run full suite and `python scripts/check_production.py`: one project, two posts, 25 prepared files. Shared comparison tests cover corrupt output sets.

### V02 — Prove offline production CI

Prerequisite: V01 integrated. Scope: workflow and PLAN. Install pinned dependencies before isolation, then `sudo unshare --net -- "$(command -v python)" scripts/check_production.py`. No online fallback if isolation fails. Require clean tracked/untracked state and successful exact task/main CI URLs.

### D00 — Replace Drive's duplicate plan with a GitHub pointer

Prerequisite: T00 integrated. Update existing Drive PLAN in place, preserving ID/parent/sharing. Replace stale narrative with canonical GitHub PLAN URL and source-of-truth explanation. Verify exact readback.

### D01 — Deliver verified fuel outputs

Prerequisite: V02 integrated and required image/caption review completed. Serial subtasks: D01a map all 18 grounded destination IDs and sharing; D01b replace petrol's nine files; D01c replace diesel's nine files; D01d reconcile delivery/index/entry records.

Prepare the complete set before replacement. Updates are per-file, not transactional. Read back each file and compare hashes to tested main. Resume partial failures by ID; keep destination IDs private.

### D02 — Remove superseded fuel derivatives

Prerequisite: D01 complete. D02a enumerate each candidate ID, role and verified replacement; inspect mixed packages for unique evidence/unmigrated topics. D02b remove each eligible item recoverably, then verify delivery and evidence still resolve. No blanket date/folder/ZIP deletion or archive hierarchy for obsolete plots. If only permanent deletion is available, retain candidates and record the blocker.

### R01–R06 — Migrate remaining topics serially

| Task | Scope and reconciliation |
| --- | --- |
| R01 | DK/NO/PL/CZ fuel, DE/EN; vintages and Norway allocation limitations |
| R02 | Unemployment comparison, DE/EN; definitions, vintages, breaks |
| R03 | DE/CH/DK/NO unemployment; comparability, coverage, gaps |
| R04 | DE/NL/PL income; income/survey year, EUR/PPS |
| R05 | German vehicle registrations; full/partial years and actual review state |
| R06 | Retained inflation/ECB; active specs and compatibility users |

Start each topic with a separate `.01` inventory/contract commit: exact files/hashes/vintages, languages/posts, transformations and review state. Add concrete children here before coding: `.02` evidence; `.03` tables/specs; `.04a` onward one decoder/transformation per change; `.04z` raw-only table verification; `.05a` onward one complete language/post per change; `.06` offline CI for all finals; `.07a` onward bounded delivery; `.08a` cleanup inventory and `.08b` individual recoverable removals. No entire-topic commits or invented input contracts.

### Z01 — Remove proven-unused compatibility

After retained-topic inventories/migrations, trace every compatibility user. Remove one unused unit per task; retain useful behavioral fixtures. Run full suite and offline reproduction for all finals. Keep any unit with an active retained user.

### Z02 — Final reconciliation

Align GitHub README/AGENTS/PLAN and Drive entry/index guidance. Retire conflicting instructions only after checking unique content. Reconcile mixed packages after all dependent topics have retained destinations. Verify final main CI, full suite, offline reproduction, clean worktree, current Drive hashes/sharing and main-only refs. Record unresolved external capabilities/unavailable work explicitly.

## Task ledger

| Task | State | Evidence / remaining gate |
| --- | --- | --- |
| T00 | integrated | `2841d858423ec45af922005f320c2c85c235bf08`; [task CI](https://github.com/datenfutter/datenfutter/actions/runs/44528662178) and [main CI](https://github.com/datenfutter/datenfutter/actions/runs/44528829844) passed. |
| C01 | blocked | Seven original tips reverified as ancestors; no PRs. Nine live refs remain; no authenticated conditional deletion operation. |
| C02 | local-pass | Durable checkpoint/history verified; unavailable original worktrees preserved by non-deletion. |
| I01 | local-pass | Recovered contract and 108 final candidate paths verified; no reselection. |
| I03 | blocked | Prepared import passes 6 source tests / 90 total tests and source/layout gates. Automatic approval review rejected the first evidence upload: explicit authorization for original source responses and retrieval metadata in this public repository is required. No evidence blob was uploaded. |
| I04–P07 | local-pass | Recovered implementation verified; public integration pending. |
| O01–O02 | local-pass | Two posts reproduce; remote integration/delivery pending. |
| V01 | local-pass | Production verifier succeeds; check every named negative case before integration. |
| V02 | pending | Network-isolated remote execution unverified. |
| D00 | delivered | Existing Drive plan replaced in place by GitHub pointer; exact text readback, parent and owner-only sharing verified. Receipt `aed81ff76c4459c7dcc6b513e11c3b6c8a6ab1a1`; [task CI](https://github.com/datenfutter/datenfutter/actions/runs/44529090498) and [main CI](https://github.com/datenfutter/datenfutter/actions/runs/44529244680) passed. |
| D01–D02 | pending | No current output replacements or derivative removals. |
| R01–R06, Z01–Z02 | pending | Follow pilot and topic inventories. |

## Rulings

- Reuse verified code and actual test/CLI names; old draft interfaces are superseded.
- This committed ledger replaces parallel status-plan maintenance; private operational metadata stays private.
- Reuse the existing integrated staging ref while deletion is unavailable; main-only closure remains outstanding.
- Local verification, public integration, remote CI, editorial review, delivery and cleanup have separate gates.

- I03: original downloaded HTML contains whitespace flagged by Git. Preserve its exact bytes; apply whitespace checks to authored files and validate raw evidence by original hashes.

- I03 publication boundary: the current instruction authorized the GitHub task workflow, but automatic approval review rejected publishing original provenance without explicit payload/destination approval. Stop source uploads; retain the tested candidate and request the concrete 52-source-file disclosure decision. Dependent pilot integration/delivery remain blocked.
