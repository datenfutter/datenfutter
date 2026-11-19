# Datenfutter: current status and implementation plan

Implementation resumed 19 November 2026, Asia/Shanghai. Work is authorized and proceeds one checked commit and verified push at a time. Current status below is updated in place.

**The foundation is pushed and tested. Production migration has not started on the inspected branch, and the foundation is not yet integrated into main.** Original steps 1–2 are complete on the branch; steps 3–8, the remaining topics and Drive cleanup are pending. This is a milestone count, not a completion percentage.

Working folder: https://drive.google.com/drive/folders/1K-NwNYx3TcyCWFCtuaCVljVi-bqEXizs
Repository: https://github.com/datenfutter/datenfutter

**Verified current status**

| Area | Evidence | Status |
| --- | --- | --- |
| Step 1: policy and entry instructions | Commit `2d1100d9e947c76bb1c65e79334ed50742a21229`, `docs: record verified status and current-output policy`. | Pushed on `refactor/current-state`. |
| Step 2: shared renderer and CI | Branch head `566bbf51b4cfe709aedf609e626c14e7fcbb9545`; 34 tracked files, shared brand/code, ten test modules and a small legacy input fixture. | Pushed and remotely verified. |
| Baseline checks | Actions run `44439057460` succeeded. Its log reports **64 tests passed** under Python 3.12 with the declared renderer dependencies. | Renderer baseline verified; this job does not rebuild production projects. |
| Integration | `main` remains at initialization commit `8243682de9e878900c82c527d2bb22623fbf363e`, containing only `.gitignore`. The PR listing returned no PRs. | Baseline not integrated. |
| Project migration | Branch tree has no `projects/` files and no `datenfutter/__main__.py`. | Fuel import, preparation, CLI and final outputs remain pending. |
| Fuel recovery input | Exact 18 November archive downloaded again: 211 files; archive hash matches the prior assessment. | Available and hash-verified. |
| Evidence completeness | All 26 entries in `sources/retrievals.jsonl` and all 23 entries in `sources/retrieval-log.jsonl` resolve to matching raw bytes, SHA-256 and sizes. The package contains 49 raw files. | Both original logs must survive migration. Eleven distinct older raw hashes are absent from the current log. |
| Current fuel selection | Two schema-0.4 refresh specs, 24 refresh CSVs, six PNG/SVG slide pairs and matching text/manifests. All 18 files listed in the refresh review match its hashes and sizes. | Select the snapshot covering January 2019–October 2026. Preserve its actual review state. |
| Reproducibility | Live renderer code still writes wall-clock manifest timestamps and does not fix SVG IDs/date metadata. | Deterministic committed outputs remain unfinished. |
| Drive cleanup | Fuel's old posts, refresh folder, exports and several delivery packages still coexist. Root checkpoint ZIPs also remain. | Final-only policy is documented in Git but not implemented in Drive. |

Step 2 remote validation is complete: 64 tests passed in Actions run 44439057460. The same 64 tests have passed again locally in the declared renderer environment before continuing.

The prior attached assessment reports successful offline preparation and exact reproduction of six PNGs and four caption/alt-text files, with SVG differences limited to generated IDs/dates after normalization. This assessment reconfirmed archive/receipt/review hashes and inspected the implementation; it did **not** rerun the complete fuel preparation/render pipeline. Rerun it in the declared migration environment before promoting outputs.

The fuel refresh review records “internally_checked; user requested reference style and authorized task”; its manifests say “preview”, and publication is recorded as “not published”. Moving files or passing CI does not change those facts.

**Final-only retention rule**

| Retain | Handling |
| --- | --- |
| Current plots and matching text | Exactly one current set per topic, language and post: numbered PNG/SVG files, caption, alt text and manifest. Replace that managed set at stable paths. |
| Current inputs | One active source selection, preparation path, processed-data set and specification per language/post. Keep vintage in metadata. |
| Raw evidence and original receipts | Preserve immutable responses and the logs that reference them, including older/failed attempts. Historical observations and dated source files remain valid evidence. |
| Current review and delivery state | Keep concise records tied to exact file hashes and verified destinations. Preserve material decisions without keeping every obsolete report. |
| Reusable brand assets | Keep the shared logo masters and accepted A/B/C palette configurations. |
| Ordinary Git history | Let commits retain code/output revision history. Normal cleanup needs no history rewriting. |

Remove superseded plot revisions, numbered backups, dated preview/export folders, palette comparison renders, contact sheets and redundant delivery ZIPs from the maintained project view. Temporary previews and exports belong in ignored `build/` and are disposable. Do not create an archive folder for old plots.

Raw-source ZIPs and mixed recovery packages require a content check: remove a recovery package only after all needed unique evidence and receipts have a verified retained destination. Apply this by role and exact file identity, not by a blanket date or ZIP pattern.

**Target layout**

| Path | Responsibility |
| --- | --- |
| `datenfutter/`, `brand/` | One shared renderer, helpers, localization, provenance, thin CLI and visual configuration. |
| `projects/<topic>/README.md` | Scope, definitions, coverage, limitations and reproduction command. |
| `projects/<topic>/prepare.py` | Offline preparation from selected evidence; topic rules stay here. |
| `projects/<topic>/sources/source-register.json` | Current source definitions, selected receipt IDs, claim/method links and source-linked parameters. |
| `projects/<topic>/sources/raw/` and receipt logs | Immutable evidence. Keep original receipt-relative paths; retain the fuel legacy log under its existing name. |
| `projects/<topic>/data/processed/` | One selected derived-data set, using stable filenames such as `price-composition.csv`. |
| `projects/<topic>/specs/<language>/<post>.json` | Current chart configuration and language-specific copy. |
| `projects/<topic>/posts/<language>/<post>/` | `01.png`, `01.svg`, subsequent numbered slides, `caption.md`, `alt-text.md`, `manifest.json`. |
| `projects/<topic>/review.json`, `delivery.json` | Actual review state and verified delivery, respectively. |
| `tests/`, ignored `build/` | Behavioral tests/small fixtures; disposable build and comparison results. |

Draft-only topics keep inputs and honest review state; their previews remain in `build/`. A canonical output path does not itself mean user approval. Discover posts from their specs and maintain status in the relevant current record, avoiding parallel inventories of the same files.

**Refactor decisions**

1. **Continue the existing baseline.** Shared code, brand, tests and CI are already imported. Recover any separately supplied pilot only if concrete files become available; an unavailable historical claim should not block the next bounded import.
2. **Untie fuel preparation from old plots.** `prepare_refresh.py` currently reads old `posts/<post>/post.json`, copies `sources/split-source-register.json`, replaces August text and writes dated paths. Move the selected definitions/copy to current inputs and regenerate calculated fields explicitly. Remove those old dependencies before excluding their files.
3. **Complete the dependency declaration.** Fuel preparation imports pandas and openpyxl; the current root requirements list only Matplotlib, NumPy and Pillow. Pin and verify the preparation dependencies in a small separate change.
4. **Separate deterministic outputs from run logs.** Use stable SVG IDs and deterministic export metadata. Remove wall-clock render timestamps from committed manifests; preserve source-retrieval times, editorial dates and actual review/delivery times in their proper records. Verify builds in different checkout paths.
5. **Reuse existing output ownership checks.** `_publish` already stages rendering, checks post/language ownership and removes obsolete managed slides. Preserve these behaviors. Its replacements are per-file; existing failure-preservation tests do not prove a transactional directory swap or recovery from an interrupted promotion.
6. **Make build/check simple.** A thin CLI prepares and renders into `build/`; checking compares a rebuilt set against the canonical set and fails on missing, extra or changed managed files. Source acquisition stays explicit. A green unit suite or an empty project list must not be reported as complete production reproduction.
7. **Give each record one purpose.** Source register = selected evidence and meaning; manifest = deterministic inputs/outputs; review = actual editorial checks/decisions; delivery = verified external save. Keep current policy in concise entry instructions and dedicated schema/brand documentation. Replace stale Drive requirements to preserve output revisions and checkpoints when the relevant handover is performed.
8. **Consolidate languages after checking vintages.** Put DE/EN specs and posts under the same topic and share matching evidence/data. The prior assessment reports September/August differences for DK/NO/PL/CZ; verify them before sharing its processed tables.
9. **Retire compatibility code last.** Inventory active inflation/ECB work, migrate retained specifications, then remove unused classic/legacy branches. Keep their relevant behavioral tests using small fixtures. Manifest size reduction and broader chart refactors can follow evidence of a real maintenance need; they need not delay the pilot.

Preserve the current design throughout: 1080×1350, cream `#FAF8EF`, navy `#1C2D57` accents, black text, DejaVu Sans, existing df logo, bold pagination, one descriptive block and localized lower-left date. Keep full literal source URLs in captions. The reference images establish continuity, not a redesign task.

**Remaining implementation in small commits**

These are proposed actions. Reuse the original step numbers so progress remains comparable. Each row is one independently checked commit and normal push; split a row further if it combines unrelated failures.

| Step | Proposed commit | Scope and gate |
| --- | --- | --- |
| Next | `docs: reconcile verified migration status` | Update the current plan/README with the branch, green CI and remaining work. Verify links/status, push and integrate the tested foundation before growing the migration branch further. |
| 3a | `data: import fuel evidence and original receipts` | Import both logs and their 49 referenced raw paths, plus current source selection and necessary methodology. Verify every hash/size and original timestamp; retain compact old-path/hash mapping. Exclude generated historical plots. |
| 3b | `data: add current fuel tables and German specs` | Import the 24 selected CSVs and two refresh specs at stable canonical paths. Check every source/data/logo reference and render both posts into `build/`. |
| 4a | `build: declare fuel preparation dependencies` | Pin pandas/openpyxl and verify a clean environment installs and imports the required packages. Existing unit CI remains green. |
| 4b | `refactor: prepare fuel from current inputs` | Establish one offline preparation path without old specs, old source cards or dated-path replacements. Reproduce all 24 CSVs; verify six series × 94 months, twelve baseline months, gaps/duplicates and composition reconciliation. Keep source-linked assumptions and limitations. |
| 5a | `fix: stabilize SVG export metadata and IDs` | Make repeated SVGs identical. Verify PNG/text content is preserved; inspect any visual difference. Run the shared suite and fuel renders. |
| 5b | `fix: make output manifests deterministic` | Remove volatile fields from committed manifests and verify portable references. Two builds in distinct directories must match all managed output bytes. Keep factual dates unchanged. |
| 6a | `feat: add offline project build command` | Discover specs and invoke preparation/rendering into `build/` for one project or all migrated projects. Verify selection, clear errors and unchanged canonical outputs on failure. |
| 6b | `feat: check rebuilt posts against current outputs` | Compare complete expected file sets and hashes without overwriting finals. Verify missing/extra/mismatched files fail and exact sets pass; retain ownership and shorter-post checks. |
| 7a | `posts: retain current German petrol outputs` | Add three PNG/SVG pairs, caption, alt text and manifest at the canonical petrol path. Check reproduction, all images at full/phone size and the complete caption; record actual review state. |
| 7b | `posts: retain current German diesel outputs` | Do the equivalent for diesel. The pilot then has six PNGs, six SVGs, two captions, two alt texts and two manifests, without duplicate output generations. |
| 8a | `ci: enforce canonical output locations` | Add a focused layout check. Reject backup/preview/export derivatives and unmanaged final files; permit raw evidence, meaningful fixtures and draft-only projects. |
| 8b | `ci: verify offline fuel reproduction` | Run preparation, rendering and comparison in clean CI. Verify tracked files stay unchanged; the same command must work from a clean checkout. |
| Handover | `docs: record verified fuel handover` | After remote checks, update Drive's selected current files, remove verified superseded derivatives and update entry instructions/index by grounded IDs. Verify Drive results, then commit the compact delivery/status record. |

For canonical-path changes, spec and manifest hashes will change legitimately. Compare PNG/text to the selected source package and document expected structural metadata changes; do not mask substantive chart changes as normalization.

**Commit and push routine**

Start from the latest verified remote head. Use one short-lived branch per coherent slice, with one or a few small commits. For each commit:

1. Inspect the diff and run its stated gate. Shared renderer/schema/brand changes also check every migrated project.
2. Stage explicit paths, commit with the bounded purpose, and push normally.
3. Verify the exact remote commit SHA and the CI result for that SHA. Resolve failures before adding the next step.
4. Update the current status, then integrate completed slices before starting unrelated work.

Local checks, pushed state, remote checks, integration, editorial review and Drive delivery are separate statuses. Remote results that occur after a commit are recorded in the next ordinary status update; avoid extra commits solely to chase self-referential commit hashes. Retain the useful small commits and ordinary Git history.

**After the fuel pilot**

Migrate one topic at a time, normally an inputs/preparation/specification commit followed by current outputs and verification. Split source reconciliation into its own change.

| Order | Topic | Required check before consolidation |
| --- | --- | --- |
| 1 | `fuel-prices-dk-no-pl-cz`, DE/EN | Reconcile selected vintages and the recorded Norway allocation limitation. |
| 2 | `unemployment-comparison`, DE/EN | Match definitions/vintages; retain recorded series breaks. |
| 3 | `unemployment-de-ch-dk-no` | Verify source comparability, coverage and gaps. |
| 4 | `income-de-nl-pl` | Preserve income-year/survey-year and EUR/PPS distinctions. |
| 5 | `vehicle-registrations-de-2016-2026` | Keep full-year and partial-year comparisons separate; respect the recorded pending review. |
| 6 | Retained inflation/ECB work | Inventory active content before removing its compatibility code. |

The live Drive listings confirm six German project folders and two English project folders. Detailed reproducibility of non-pilot topics was not audited here. This inventory does not certify unattached packages from other conversations.

**Drive cleanup and completion**

Git becomes the working source for migrated code/specifications/data selection. Drive becomes the current delivery view for those topics and remains the working source for unmigrated topics. Update existing files by identity where appropriate and preserve sharing.

Clean up per topic only after a clean checkout reproduces its selected outputs and remote checks pass. Check recovery packages for unique evidence before removing them; prefer recoverable removal. Update cross-topic bundles only after every included topic's evidence has a retained destination. Do not duplicate final plots into a replacement archive hierarchy.

The work is complete when every retained topic rebuilds offline, every final topic/language/post has one current managed set, no current build depends on an obsolete plot/spec revision, repeated builds leave tracked files unchanged, remote integration/checks are verified, and Drive's current files and instructions match the handover. Drafts remain clearly identified. No social publication is implied.

**Evidence links**

- Branch snapshot: https://github.com/datenfutter/datenfutter/tree/566bbf51b4cfe709aedf609e626c14e7fcbb9545
- Policy commit: https://github.com/datenfutter/datenfutter/commit/2d1100d9e947c76bb1c65e79334ed50742a21229
- Renderer baseline commit: https://github.com/datenfutter/datenfutter/commit/566bbf51b4cfe709aedf609e626c14e7fcbb9545
- Successful CI run and test log: https://github.com/datenfutter/datenfutter/actions/runs/44439057460
- Drive index: https://drive.google.com/file/d/13-f7SJB9zMjGvSACEGuSRl3-LWiOoUO8/view
- Fuel refresh folder: https://drive.google.com/drive/folders/1BWtE1pEt0ZLNILHhmyAilTBfw7GlWjLB
- Fuel recovery archive: https://drive.google.com/file/d/1YsE9afVdFN-m0VIYwcwEJ5l9poCdPWf5/view
- Archive SHA-256: `c5b4dd172488e7021cdf3632198e7ba70c5a1e180907927e2029155712fc03be`.
- Drive workflow: https://drive.google.com/file/d/1zbIzKU2vXUp9JITRR2nCDpiXw9s41Ybm/view
- Drive project structure: https://drive.google.com/file/d/16LDMTgMnJHFtxvlk1mQ6GIJSz290HDsD/view
- Drive brand guide: https://drive.google.com/file/d/1CcHbA7CBaxpGK8zbBQ4UgqRuLDH4n-b-/view
