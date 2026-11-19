# Datenfutter: verified status and implementation plan

Implementation started 19 November 2026, Asia/Shanghai, under the user-approved plan. Work proceeds in small commits with checks and verified pushes. The assessment below records the baseline observed before implementation.

**Implementation status**

- Step 1: pushed and remote head verified (2d1100d).
- Step 2: shared code, assets, tests and CI baseline imported; 64 tests pass locally in the declared environment; remote validation pending.
- Steps 3–8: pending.
- Remaining topic migrations and Drive cleanup: pending.

Source: [Datenfutter working folder](https://drive.google.com/drive/folders/1K-NwNYx3TcyCWFCtuaCVljVi-bqEXizs). Destination: [datenfutter/datenfutter](https://github.com/datenfutter/datenfutter).

**Baseline assessment: the saved fuel snapshot is reproducible; implementation was absent from GitHub when assessed.** Finish the handover before extending the migration. Keep one current output per topic, language and post, with future revision history in Git.

**Verified baseline before implementation**

| Area | Evidence observed now | Status |
| --- | --- | --- |
| GitHub workspace | Main is at commit `8243682de9e878900c82c527d2bb22623fbf363e`, “Initialize Datenfutter repository”. Its tree contains only `.gitignore`. Only main was returned; no pull requests or Actions runs were returned. | Repository created; implementation not pushed to the inspected repository. |
| Claimed local migration pilot | The previous plan reports a completed CLI, canonical layout, deterministic SVGs and regression checks. Its migrated checkout, `inventory.json` and `fuel-verification.json` were not supplied. No matching migration package was found in the Drive searches/index inspected. | Reported complete locally; not independently verified or available as a remote handover. |
| Original DE/CH/LU archive | Downloaded the exact linked 18 November archive: 211 files. All 26 entries in `sources/retrievals.jsonl` resolve to raw files with matching SHA-256 and byte size. | Recovery input verified. |
| Offline fuel preparation | Ran the archived preparation script. All 24 refresh CSVs, both refresh specifications and the refresh source register matched their pre-run bytes. Checks passed for 564 observations, six series, 94 months, 12 baseline months and composition reconciliation. | Current saved preparation reproduced; no new source refresh. |
| Fuel plots and text | Rebuilt both three-slide posts. All six PNGs and all four caption/alt-text files matched the saved refresh bytes. | Current visual/text outputs reproduced. |
| SVGs | None of the six rebuilt SVGs matched byte for byte. All matched after normalizing embedded render dates and generated element IDs. | Deterministic SVG generation still needs fixing in the recovered code, or verification in the unavailable pilot. |
| Output layout | October outputs are in `previews/refresh-2026-11-18/`; older August outputs are in `posts/petrol/` and `posts/diesel/`. Both generations exist and differ. | Selection and consolidation required. A folder called posts is not proof of the latest output. |
| Shared engine | All seven archived shared Python module hashes match their entries in the inspected Drive index. The saved entrypoint is `render.py`; the archive has no `datenfutter/__main__.py`. | Shared implementation recovered; the plan's new CLI is not verified in this saved version. |
| Tests / CI | Drive contains ten test modules and historical passing reports. The fuel archive excludes that suite. No GitHub workflow runs exist. | Fresh full-suite and CI verification remain outstanding. |
| Other topics | The Drive projects/packages listed below exist; they are absent from the inspected GitHub tree. | Saved in Drive; GitHub migration not completed. |

The latest fuel review says “internally_checked; user requested reference style and authorized task”; its manifests say “preview”. Preserve that distinction. Successful reproduction, save authorization, design review and social publication are different facts. Do not infer explicit approval from a folder name or from this cleanup request.

**Current-state retention policy**

| Item | Rule |
| --- | --- |
| Current PNGs and editable SVGs | One set at `projects/<topic>/posts/<language>/<post>/`, with stable numbered filenames. Replace the managed set when a new version is accepted. |
| Caption, alt text and manifest | One matching current copy beside those plots. |
| Specifications and processed data | One active set at stable paths. Record the selected vintage in metadata/source selection, not duplicate output directories. |
| Previews, contact sheets and intermediate renders | Disposable local `build/` only. Do not commit or maintain them as another final set. |
| Old plot revisions, dated exports, backup folders, palette demo images and delivery ZIP copies | Exclude from the new Git working tree. Remove obsolete Drive derivatives after the relevant migration and verification. Do not create an archive directory for them. |
| Raw responses and retrieval receipts | Preserve immutable evidence, including recorded unsuccessful or superseded attempts. These are not plot backups. Every retained receipt must remain resolvable. |
| Historical observations in a time series | Preserve the years needed by the current analysis. |
| Review and migration records | Keep compact current review state and necessary original-path/hash mappings. Avoid numbered copies of reports. |
| Git history | Keep ordinary history. Current-only files do not require history rewriting or force pushes. |
| Palettes and approved logo assets | Retain reusable A/B/C configurations and approved masters. Remove obsolete rendered comparisons, not selectable palettes. |

For the fuel pilot, the proposed active selection is the 18 November snapshot covering January 2019–October 2026. Preserve its actual review state. For topics with only an unreviewed draft, retain inputs and review state, render a current preview into `build/`, and do not invent an approved final.

**Target layout**

| Path | Responsibility |
| --- | --- |
| `datenfutter/` | One shared renderer, chart/data helpers, localization, provenance and small CLI. |
| `brand/` | Shared typography, palettes and logo assets. |
| `projects/<topic>/README.md` | Current scope, definitions, coverage and reproduction instructions. |
| `projects/<topic>/prepare.py` | Offline topic preparation; source/country rules stay outside the generic renderer. |
| `projects/<topic>/sources/source-register.json` | Current source definitions, selected receipt IDs, claim/method links and limitations. |
| `projects/<topic>/sources/retrievals.jsonl`, `sources/raw/` | Original evidence and receipts. Preserve existing raw paths where receipts depend on them. |
| `projects/<topic>/data/processed/` | Selected current derived tables. |
| `projects/<topic>/specs/de/*.json`, `specs/en/*.json` | Current language-specific copy and chart specifications. |
| `projects/<topic>/posts/<language>/<post>/` | Numbered PNG/SVG, caption, alt text and output manifest. |
| `projects/<topic>/review.json` | Current checks and actual review state keyed to exact output hashes. |
| `tests/` | Behavioral tests and small input fixtures, without galleries of obsolete production plots. |
| `build/` | Ignored, disposable preparation/render/check output. |

Discover projects/posts from specifications where possible. Add a small recipe/config only for real inputs such as selected receipt IDs and source-linked parameters. Do not duplicate coverage, status and file lists across several registries.

**Refactors and simplifications**

1. **Remove old-version dependencies before deleting old files.** The current `prepare_refresh.py` reads `posts/<post>/post.json` and `sources/split-source-register.json`, then changes old copy and dated paths. Make it read the selected current inputs directly. Otherwise removing the August specification breaks the October rebuild.
2. **Make committed outputs deterministic.** Stabilize SVG IDs and remove wall-clock export timestamps from committed artifacts. Keep actual retrieval times and editorial dates intact; put transient run timing in CI/local logs. Check manifests from another checkout directory.
3. **Reuse existing output protection.** `_publish` already stages renders, rejects another post/language's destination and removes obsolete managed slides. Preserve those behaviors and failure-preservation tests. Do not introduce another output-management framework. Its per-file replacement is not a transactional directory swap.
4. **Use one build path.** A thin CLI should discover projects, build offline into `build/`, and compare reproduction with current committed outputs. Keep acquisition explicit and separate. Replace dated packaging scripts with an on-demand export only if needed; do not commit export ZIPs or preview HTML.
5. **Share language-independent work after checking vintages.** German DK/NO/PL/CZ fuel is documented through September 2026; its saved English edition is documented through August. Verify and reconcile the difference before sharing processed data. Never silently use newer data with older English copy. Distinct current language editions are not backup versions.
6. **Consolidate contradictory instructions.** `WORKFLOW.md` says palettes remain under discussion and later says A/B/C are accepted. It also requires retained preview revisions and dated exports. The current request replaces that output-retention rule. Keep concise agent instructions, one entry README, schema documentation and brand guidance with separate responsibilities. Update stale project skill guidance about renderer support and explanation blocks; avoid repeated policy text.
7. **Remove legacy renderer paths last.** The saved `render.py` contains classic/legacy code alongside `editorial.py` and `charts.py`. Migrate active inflation/ECB specifications first, preserve their needed behavior, then remove unused schemas and duplicate rendering. Replace tests dependent on old root projects with small equivalent input fixtures.

Keep the current design unchanged during this refactor: cream `#FAF8EF`, navy `#1C2D57`, black general text, DejaVu Sans, the existing df logo, bold navy pagination, one descriptive block and localized date footer. The supplied reference images do not require a redesign here.

**Small commits and pushes**

These are proposed steps, not completed changes. First recover the previously reported migrated pilot if it becomes available, compare it with the verified archive, and reuse working changes. Do not recreate functioning code merely because its package was unavailable during this assessment.

| Step / proposed commit | Bounded change | Gate before commit and push |
| --- | --- | --- |
| 1. `docs: record verified status and current-output policy` | Commit the current plan, selected fuel vintage and concise canonical layout/retention policy. Clearly mark unverified historical claims. | Source links, identifiers and selected paths checked; no plot/data or publication-state change. |
| 2. `build: import shared renderer and establish CI baseline` | Import shared code, brand, dependencies and tests; recover the necessary small test inputs. Add a Python 3.12 baseline CI job. | Imported suite passes locally and remotely. Record its actual count rather than copying an old report. |
| 3. `data: import fuel evidence and current specifications` | Import receipt/raw closure, current source register, 24 selected CSVs and two German specs at canonical paths. Record old paths/hashes and omissions. Exclude old generated plots. | All 26 current-log entries remain resolvable; hashes/sizes pass; both specs render. Audit the separate older receipt log before omitting any evidence it references. |
| 4. `refactor: make fuel preparation independent of old revisions` | Replace old-spec/split-register dependencies with one offline preparation path and explicit selected parameters. Preserve formulas and limitations. | All 24 CSVs reproduce exactly; coverage, baseline and reconciliation checks pass; preparation makes no network requests. |
| 5. `fix: make SVG and manifest output reproducible` | Stabilize IDs, metadata and any checkout-dependent fields. Preserve substantive dates and source identities. | Two builds in different directories match; PNG/text match the reference. SVG differences are limited to documented metadata/ID normalization. |
| 6. `refactor: add one project build and check entrypoint` | Add/recover `python -m datenfutter` with project discovery and offline build/check commands. Reuse existing helpers. | One project and all work; invalid inputs preserve existing output; shorter posts remove only obsolete owned slides; language/post ownership checks remain. |
| 7. `posts: keep selected fuel outputs at canonical paths` | Commit six PNGs, six SVGs, two captions, two alt-text files and two manifests in the German final-output paths. Align current review metadata. | Reproduction passes; inspect all six full-size and phone-size images and complete captions. Preserve the actual review status and relevant existing authorization. |
| 8. `ci: enforce current-only output layout` | Add a focused layout check and enable complete fuel reproduction checks. Align workflow examples. | CI rejects obsolete output locations/unmanaged final files but permits raw source archives and source dates. A clean checkout rebuild leaves tracked files unchanged. |

Do not import all historical plots in step 3 just to delete them later. If a recovered pilot already contains them, remove them in a separate cleanup commit after the selected replacements reproduce.

Then migrate one topic at a time. Normally use **two commits per topic**: evidence/preparation/specifications, followed by verified current outputs and status update. Split further when data reconciliation or schema conversion is substantive.

| Order | Topic | Evidence and condition |
| --- | --- | --- |
| 1 | `fuel-prices-dk-no-pl-cz` | A six-slide German refresh package and an English project exist. Verify September/August differences, Norway's unresolved allocation and exact source reuse. |
| 2 | `unemployment-comparison` | German and English folders exist. Preserve breaks and verify shared vintage/definitions. |
| 3 | `unemployment-de-ch-dk-no` | November archive, two PNGs and a caption are present. Verify definitions, coverage and breaks. |
| 4 | `income-de-nl-pl` | November archive, two PNGs and a caption are present. Preserve income-year/survey-year and EUR/PPS distinctions. |
| 5 | `vehicle-registrations-de-2016-2026` | Research archive, source/data folders and review records exist. The index says previews await review. Migrate inputs first; do not invent final approval. Keep full-year and partial-year comparisons separate. |
| 6 | Inflation / ECB legacy materials | Complete evidence and active-project audit still needed. A test fixture is not a production migration. Migrate retained active work before removing compatibility code. |

Non-pilot package existence was checked; complete contents and reproducibility were not audited here. Folder presence alone does not justify a completion percentage.

Finish with separate commits for unused legacy renderer/test-dependency removal, then final documentation/status consolidation. Run affected-project checks for project changes; run all migrated projects after shared renderer, schema or brand changes.

**Commit/push routine**

Use a short-lived branch for each coherent slice, starting from the latest verified remote state. For every step: inspect the diff, run its gate, stage explicit paths, create one descriptive commit, push normally, and verify remote head SHA and CI. Resolve failures before stacking more work. Integrate a completed slice before starting the next, retaining useful small-commit history. Do not force-push or bulk-stage downloaded packages and caches.

A step is complete only when committed, pushed and remotely verified. Locally built, saved to Drive, pushed and reviewed are separate statuses. Update migration status in the commit that implements the work.

**Drive cleanup and handover**

Clean up each topic after a clean checkout reproduces the selected outputs and the remote commit/checks are verified. Git becomes the working source for migrated code, specifications and data selection. Drive remains the current-file view and the source for unmigrated topics; avoid two editable code trees.

Use grounded Drive IDs to retain/update selected final files and remove superseded plot derivatives, old preview directories and redundant delivery packages. Prefer recoverable removal where supported. Verify that every needed unique source byte and receipt survives before removing a package. Never delete by a blanket ZIP/date pattern: source datasets can be ZIPs and dated source evidence is intentional. Do not create another backup/archive folder.

Record actual Drive results separately from the preceding Git commit; pushing does not prove Drive cleanup happened. Update the existing Drive index and entry instructions to point to current files and the repository. No Drive removal or reorganization occurred during this assessment.

**Completion criteria**

- A clean clone prepares and renders every migrated project offline from retained evidence.
- Each final topic/language/post has exactly one current output set; draft-only work retains honest review state.
- No committed preview/revision/backup/export copies or generated delivery ZIPs remain; raw archives and meaningful small input fixtures are allowed.
- Preparation and current specs do not depend on superseded plot versions or old caption text.
- Repeated builds are deterministic and leave the working tree clean; original source dates and receipt history remain unchanged.
- Tests retain coverage for gaps/breaks, units/baselines, stack totals, citations, localization, output ownership and failed-build preservation.
- Remote commits and CI are verified; Drive's current-file view matches the handover; instructions describe the supported workflow.

**Assessment evidence**

- Attached `PLAN.md`: the previous 18 November migration plan.
- [Repository](https://github.com/datenfutter/datenfutter), [observed initialization commit](https://github.com/datenfutter/datenfutter/commit/8243682de9e878900c82c527d2bb22623fbf363e), and live tree/branches/pull-request/Actions API reads.
- [Working folder](https://drive.google.com/drive/folders/1K-NwNYx3TcyCWFCtuaCVljVi-bqEXizs), [Drive index](https://drive.google.com/file/d/13-f7SJB9zMjGvSACEGuSRl3-LWiOoUO8/view), and direct project-folder listings.
- [Reproduced fuel archive](https://drive.google.com/file/d/1YsE9afVdFN-m0VIYwcwEJ5l9poCdPWf5/view), SHA-256 `c5b4dd172488e7021cdf3632198e7ba70c5a1e180907927e2029155712fc03be`.
- [Project instructions](https://drive.google.com/file/d/1GoqKT1xJQ3zLfjXF918g3t4_34OyslZI/view), [workflow](https://drive.google.com/file/d/1zbIzKU2vXUp9JITRR2nCDpiXw9s41Ybm/view), [structure](https://drive.google.com/file/d/16LDMTgMnJHFtxvlk1mQ6GIJSz290HDsD/view), [brand guide](https://drive.google.com/file/d/1CcHbA7CBaxpGK8zbBQ4UgqRuLDH4n-b-/view), and selected test-module inspection.

Reproduction runtime: Python 3.12.14, Matplotlib 3.10.8, NumPy 2.3.5, pandas 2.2.3, openpyxl 3.1.5, Pillow 13.0.0. The archive pins Pillow 12.3.0; exact PNG/text matches were observed in this runtime. Restore and verify the declared environment for migration CI rather than silently changing dependency policy.
