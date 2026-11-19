# Datenfutter implementation plan

Updated 19 November 2026, Asia/Shanghai. Implement one bounded change, verify it, commit, push and check that exact remote commit before continuing. Update this document in place.

The shared foundation is integrated at `b75c814ed58987f2b2d81fc0f49dbd5fce71cc26`.
Its [main CI run](https://github.com/datenfutter/datenfutter/actions/runs/44468409988)
passed 84 tests and the layout check. Layout reported zero projects and zero
current posts: this is not production reproduction. The implemented foundation
does not need to be rebuilt during migration.

**Current status**

| Task | State |
| --- | --- |
| Foundation: shared renderer, brand, 64 tests and baseline CI | Integrated into main at `0d742590c4123d34b5acee4bbc4a596d50cd059f`; remote run `44464974130` passed. |
| 3a. Fuel evidence and original receipts | Prepared and hash-verified locally; publication of the recovered Drive package awaits explicit disclosure authorization. |
| 3b. Current fuel tables and German specs | Pending. |
| 4a. Preparation dependencies | Integrated into main at `d2b4aa8827e323773e2953caa1892690bbb1b81c`; remote run `44466458991` passed in a clean environment. |
| 4b. Offline preparation without old revisions | Pending. |
| 5a. Deterministic SVG export | Integrated into main at `7a598899d7e5f294cee524998352f32ee587db84`; remote run `44465866261` passed (65 tests). Six fuel PNGs/four text files remain byte-identical. |
| 5b. Deterministic output manifests | Integrated into main at `f62a21a5ed2586c6a38f3c79c3579e0a0876e2c8`; remote run `44466237684` passed (66 tests). Complete fuel outputs reproduce; PNG/text unchanged. |
| 6a. Offline project build command | Integrated into main at `b416fcef216115d0625222af5f03c8acc55d4b10`; remote run `44467081314` passed (73 tests). Private fuel smoke check matches PNG/text. |
| 6b. Compare builds against current outputs | Integrated into main at `1a89cf0290adebf19b4d292bd5bed716f87f126f`; remote run `44467501486` passed. Missing, extra and changed files fail without overwriting current outputs. |
| 7. Current petrol and diesel output sets | Pending; one commit per post. |
| 8a. Canonical layout check | Integrated into main at `b75c814ed58987f2b2d81fc0f49dbd5fce71cc26`; main run `44468409988` passed. Layout validity and production reproduction are separate checks. |
| 8b. Offline production reproduction in CI | Pending; requires the production inputs. |
| Other topics and Drive handover/cleanup | Pending. |

The evidence-import branch remains local. Independent shared-code work can proceed from main without publishing the recovered package. Publishing, integration, source verification, editorial review and Drive delivery are separate states.

**One current state**

Keep one current numbered PNG/SVG set, caption, alt text and manifest per topic/language/post. Replace managed outputs at stable paths. Temporary renders, contact sheets and on-demand exports belong in ignored `build/`.

Remove obsolete plot revisions, backup folders, dated output/export directories and delivery ZIP copies after replacements reproduce. Keep immutable raw evidence, original retrieval receipts, historical observations, meaningful test fixtures and ordinary Git history. Source dates and source ZIPs are valid evidence, not plot backups.

| Path | Responsibility |
| --- | --- |
| `datenfutter/`, `brand/` | Shared renderer, helpers, CLI and visual configuration. |
| `projects/<topic>/README.md`, `prepare.py` | Current scope/method and offline preparation. |
| `projects/<topic>/sources/source-register.json` | Selected evidence, definitions, limitations and source-linked parameters. |
| `projects/<topic>/sources/raw/`, original receipt logs | Immutable source bytes and their actual retrieval history. |
| `projects/<topic>/data/processed/` | One selected derived-data set at stable paths. |
| `projects/<topic>/specs/<language>/<post>.json` | Current chart/copy specification. |
| `projects/<topic>/posts/<language>/<post>/` | Current numbered slides, caption, alt text and manifest. |
| `projects/<topic>/review.json`, `delivery.json` | Actual review decisions and verified external delivery. |
| `tests/`, ignored `build/` | Behavioral fixtures/checks and disposable build output. |

Discover projects/posts from specifications. Keep source acquisition separate from offline builds. Draft-only work retains inputs and honest review state; a render or a folder name does not create approval.

**Atomic tasks and gates**

| Task | Change | Gate |
| --- | --- | --- |
| 3a | Import both fuel receipt logs and their 49 referenced raw paths, current source selection and methodology. | Every original hash, size, path and timestamp preserved. |
| 3b | Import the selected 24 CSVs and two German specs. | References resolve; both posts render under `build/`; historical plots excluded. |
| 4a | Declare the tested preparation dependencies. | Clean installation; existing unit suite passes. |
| 4b | Replace old-spec/source-card copying and dated-path substitutions with one offline preparation path. | All 24 selected CSVs reproduce; coverage, baseline, gaps/duplicates and composition reconcile. |
| 5a | Stabilize SVG IDs and exporter metadata. | Repeated exports match in both supported renderers; PNG/text content unchanged. |
| 5b | Remove volatile manifest fields while retaining source/editorial dates. | Complete output sets match in different directories. |
| 6a | Add a thin CLI for one/all project builds into `build/`. | Clear selection/errors; final outputs preserved on failure. |
| 6b | Add complete file-set/hash comparison against current posts. | Missing/extra/changed files fail; matching outputs pass; checking does not overwrite finals. |
| 7a | Keep the current German petrol post. | Reproduction, full-size/phone-size image review, full caption and actual review metadata. |
| 7b | Keep the current German diesel post. | Same gate; six slide pairs in total with matching text/manifests. |
| 8a | Enforce canonical output locations. | Reject obsolete derivatives and unmanaged finals; allow raw evidence and draft-only topics. |
| 8b | Verify offline production builds in CI. | Clean checkout reproduces every migrated final and leaves tracked files unchanged. |

Keep SVG export and manifest fixes separate. Reuse existing staging and post/language ownership checks. Existing output replacement is per-file; do not describe it as a transactional directory swap.

**Execution order for the remaining migration**

1. Recheck and delete each fully integrated task branch individually. Keep
   `main` and any branch with unique work. Account for local-only changes before
   deleting local branches; a missing old checkout is not evidence of a merge.
2. Inventory the selected inputs and exact source-to-table transformations.
   Reuse recovered implementation only after independently checking its diff
   and acceptance gates. Resolve disclosure for the concrete public payload
   before importing source content or provenance.
3. Integrate verified raw evidence, then selected tables/specifications as
   separate changes. A preview from saved tables proves rendering only.
4. Split preparation changes into source decoding, monthly normalization,
   baseline/index calculations, composition reconciliation and deterministic
   serialization. Each change owns a testable behavior. Activate the preparation
   entry point only when all selected tables reproduce.
5. Retain one complete post per change. Compare that post independently while
   other specifications still lack current outputs; run the whole-project
   comparison only after all intended current posts exist. Never weaken the
   comparison to make an intermediate migration pass.
6. Verify preparation in a disposable copy with saved processed tables removed,
   comparing complete output file sets and bytes. Then require production CI
   to run preparation and rendering without network access and leave the
   checkout unchanged. Empty comparisons must fail.
7. Update current Drive files, verify their exact bytes and links, then remove
   only enumerated superseded derivatives. Repeat this sequence for one topic
   at a time; inventory each topic before defining its preparation tasks.

Keep private recovery records and publication decisions outside public status
updates unless their disclosure is authorized. Update public implementation
facts independently of a blocked source import.

Preserve the visual system: 1080×1350, cream `#FAF8EF`, navy `#1C2D57` accents, black text, DejaVu Sans, the existing df logo, bold pagination, one descriptive block and the localized date footer. Keep literal source URLs in captions.

**Further migrations**

Migrate one topic at a time, normally inputs/preparation/specs followed by current outputs. Reconcile substantive source differences separately.

1. DK/NO/PL/CZ fuel, DE/EN: reconcile vintages and preserve Norway allocation limitations.
2. Unemployment comparison, DE/EN: match definitions/vintages and preserve breaks.
3. DE/CH/DK/NO unemployment: verify comparability, coverage and gaps.
4. DE/NL/PL income: distinguish income year, survey year, EUR and PPS.
5. German vehicle registrations: distinguish full and partial years and preserve pending review.
6. Retained inflation/ECB work: inventory active specifications before removing compatibility code.

Share language-independent work only when the selected evidence/vintages agree. Remove unused legacy branches after their retained projects migrate; preserve relevant behavior in small fixtures. Consolidate stale entry/schema/brand guidance around the supported workflow.

**Push and handover routine**

Inspect the diff, run the task gate, stage explicit paths, commit and push normally. Verify the remote head and CI for that SHA before the next change. Integrate coherent slices into main. Shared renderer/schema/brand changes check every available migrated project. Record remote results in the next ordinary status update; avoid extra commits merely to chase self-referential hashes.

Use one active task branch from current main. After integration, verify the
resulting main SHA and its CI, then delete the task branch after checking
ancestry again. If a gate fails, stay on the same task and branch, record the
failing input/command, and fix it before starting dependent work. Keep local
checks, remote checks, integration, editorial review and delivery distinct.

Git is the working source for migrated code/specifications/data selection once publication is authorized. Drive remains the working source for unmigrated material and the current delivery view. After a clean checkout and remote checks succeed, update selected Drive files by verified IDs, remove superseded derivatives and update the current index/instructions. Preserve sharing.

Inspect mixed recovery packages for unique evidence before removing them; use recoverable removal. Clean cross-topic bundles only after every included topic has a verified retained destination. Do not create a replacement archive hierarchy for old plots.

Complete means: every retained topic rebuilds offline, every final topic/language/post has one current managed set, no active build depends on obsolete plot revisions, repeated builds leave tracked files unchanged, integration/CI are verified, and Drive's current delivery matches the handover. Social publication is outside this task.
